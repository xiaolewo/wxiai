from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from open_webui.models.media_library import (
    MediaAsset,
    MediaAssetAuditLogs,
    MediaAssetForm,
    MediaAssets,
    MediaFolder,
    MediaFolderForm,
    MediaFolders,
    MediaLibrarySettingsForm,
    MediaLibrarySettingsTableHelper,
    VISIBILITY_GROUP,
    VISIBILITY_USER,
)
from open_webui.models.cloud_storage import GeneratedFiles
from open_webui.models.groups import Groups
from open_webui.models.users import UserModel


@dataclass
class ScopeContext:
    owner_ids: List[str]
    visibility_scopes: List[str]
    manageable_owner_ids: List[str]
    scope_requested: str


class MediaLibraryService:
    def __init__(self) -> None:
        self.assets = MediaAssets()
        self.folders = MediaFolders()
        self.settings_table = MediaLibrarySettingsTableHelper()
        self.audit_logs = MediaAssetAuditLogs()
        self.generated_files = GeneratedFiles()
        self.groups = Groups

    # ------------------------------
    # Settings
    # ------------------------------

    def get_settings(self) -> Dict[str, Any]:
        settings = self.settings_table.get_settings()
        if not settings:
            settings = self.settings_table.upsert_settings(MediaLibrarySettingsForm())
        return {
            "id": settings.id,
            "enable_group_sharing": settings.enable_group_sharing,
            "allow_bulk_download": settings.allow_bulk_download,
            "allowed_media_types": settings.allowed_media_types,
            "default_visibility": settings.default_visibility,
            "max_storage_per_user": settings.max_storage_per_user,
            "max_storage_per_group": settings.max_storage_per_group,
            "signed_url_ttl_seconds": settings.signed_url_ttl_seconds,
            "thumbnail_strategy": settings.thumbnail_strategy,
            "extra_config": settings.extra_config,
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat(),
        }

    def update_settings(self, data: MediaLibrarySettingsForm) -> Dict[str, Any]:
        settings = self.settings_table.upsert_settings(data)
        return self.get_settings()

    # ------------------------------
    # Access helpers
    # ------------------------------

    def _resolve_scope(self, user: UserModel, scope: Optional[str]) -> ScopeContext:
        requested_scope = scope or "mine"
        if user.role == "admin":
            return ScopeContext(
                owner_ids=[],
                visibility_scopes=[],
                manageable_owner_ids=[],
                scope_requested="admin",
            )

        settings_obj = self.settings_table.get_settings()
        enable_group_sharing = (
            settings_obj.enable_group_sharing if settings_obj else False
        )

        owner_ids = [user.id]
        visibility_scopes = [VISIBILITY_USER]
        manageable = [user.id]
        group_owner_ids: List[str] = []
        group_manage_ids: List[str] = []

        if enable_group_sharing:
            groups = self.groups.get_groups_by_member_id(user.id)
            for group in groups:
                perms = (group.permissions or {}).get("media_library") or {}
                view_scope = perms.get("view")
                manage_actions = perms.get("manage") or []
                if view_scope == "group":
                    group_owner_ids.append(group.id)
                    if manage_actions:
                        group_manage_ids.append(group.id)

        if requested_scope == "group":
            if not group_owner_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Group media access is not enabled for this user",
                )
            owner_ids = group_owner_ids
            visibility_scopes = [VISIBILITY_GROUP]
            manageable = [oid for oid in group_manage_ids]
        elif requested_scope == "all":
            if group_owner_ids:
                owner_ids = [user.id] + group_owner_ids
                visibility_scopes = [VISIBILITY_USER, VISIBILITY_GROUP]
                manageable = [user.id] + group_manage_ids
            else:
                owner_ids = [user.id]
                visibility_scopes = [VISIBILITY_USER]
                manageable = [user.id]
        else:  # mine
            owner_ids = [user.id]
            visibility_scopes = [VISIBILITY_USER]
            manageable = [user.id]

        return ScopeContext(
            owner_ids=owner_ids,
            visibility_scopes=visibility_scopes,
            manageable_owner_ids=manageable,
            scope_requested=requested_scope,
        )

    def _ensure_manage_permission(
        self, context: ScopeContext, asset: MediaAsset, is_admin: bool
    ) -> None:
        if is_admin:
            return
        if asset.owner_id not in context.manageable_owner_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this asset",
            )

    # ------------------------------
    # Assets
    # ------------------------------

    def list_assets(
        self,
        user: UserModel,
        scope: Optional[str],
        page: int,
        limit: int,
        media_type: Optional[str],
        folder_id: Optional[str],
        include_deleted: bool = False,
        search: Optional[str] = None,
        source: Optional[str] = None,
        owner_id: Optional[str] = None,
        visibility_scope_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = self._resolve_scope(user, scope)
        is_admin = user.role == "admin"

        owner_ids = context.owner_ids if context.owner_ids else None
        visibility_scopes = (
            context.visibility_scopes if context.visibility_scopes else None
        )

        if is_admin:
            owner_ids = None
            visibility_scopes = None
            if owner_id:
                owner_ids = [owner_id]
            if visibility_scope_filter:
                visibility_scopes = [visibility_scope_filter]

        if page < 1:
            page = 1
        if limit < 1:
            limit = 20
        limit = min(limit, 100)
        offset = (page - 1) * limit

        media_types = [media_type] if media_type else None

        items, total = self.assets.list_assets(
            owner_ids=owner_ids,
            visibility_scopes=visibility_scopes,
            media_types=media_types,
            folder_id=folder_id,
            include_deleted=include_deleted and is_admin,
            search=search,
            source=source,
            limit=limit,
            offset=offset,
        )

        file_map = self.generated_files.get_files_by_ids(
            [item.file_id for item in items if item.file_id]
        )

        results: List[Dict[str, Any]] = []
        for asset in items:
            file_record = file_map.get(asset.file_id)
            results.append(
                {
                    "id": asset.id,
                    "display_name": asset.display_name,
                    "media_type": asset.media_type,
                    "mime_type": asset.mime_type,
                    "visibility_scope": asset.visibility_scope,
                    "owner_id": asset.owner_id,
                    "folder_id": asset.folder_id,
                    "tags": asset.tags,
                    "metadata": asset.metadata_json,
                    "source": asset.source,
                    "thumbnail_url": asset.thumbnail_url,
                    "checksum": asset.checksum,
                    "created_at": asset.created_at.isoformat(),
                    "updated_at": asset.updated_at.isoformat(),
                    "created_by_user_id": asset.created_by_user_id,
                    "created_by_task_id": asset.created_by_task_id,
                    "deleted_at": (
                        asset.deleted_at.isoformat() if asset.deleted_at else None
                    ),
                    "width": asset.width,
                    "height": asset.height,
                    "duration": asset.duration,
                    "file": {
                        "id": file_record.id if file_record else None,
                        "cloud_url": file_record.cloud_url if file_record else None,
                        "storage_provider": (
                            file_record.storage_provider if file_record else None
                        ),
                        "file_size": file_record.file_size if file_record else None,
                        "mime_type": file_record.mime_type if file_record else None,
                        "status": file_record.status if file_record else None,
                    },
                    "can_manage": is_admin
                    or (asset.owner_id in context.manageable_owner_ids),
                }
            )

        return {
            "data": results,
            "total": total,
            "page": page,
            "limit": limit,
        }

    def update_asset(
        self,
        user: UserModel,
        asset_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        asset = self.assets.get_asset_by_id(asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
            )

        context = self._resolve_scope(user, None)
        is_admin = user.role == "admin"
        self._ensure_manage_permission(context, asset, is_admin)

        allowed_fields = {
            "display_name",
            "folder_id",
            "tags",
            "metadata",
            "thumbnail_url",
        }
        changes = {k: v for k, v in payload.items() if k in allowed_fields}
        if not changes:
            return self._serialize_asset(asset, include_file=True)

        before_snapshot = {}
        for key in changes.keys():
            attr_name = "metadata_json" if key == "metadata" else key
            before_snapshot[key] = getattr(asset, attr_name)
        audit_changes = dict(changes)
        if "metadata" in changes:
            changes["metadata_json"] = changes.pop("metadata")
        updated_asset = self.assets.update_asset(asset_id, changes)
        if not updated_asset:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update asset",
            )

        self.audit_logs.create_record(
            asset_id=asset_id,
            action="update",
            actor_id=user.id,
            actor_role=user.role,
            before=before_snapshot,
            after=audit_changes,
        )

        return self._serialize_asset(updated_asset, include_file=True)

    def delete_asset(self, user: UserModel, asset_id: str) -> Dict[str, Any]:
        asset = self.assets.get_asset_by_id(asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
            )

        context = self._resolve_scope(user, None)
        is_admin = user.role == "admin"
        self._ensure_manage_permission(context, asset, is_admin)

        updated = self.assets.set_deleted(asset_id, True)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove asset",
            )

        self.audit_logs.create_record(
            asset_id=asset_id,
            action="delete",
            actor_id=user.id,
            actor_role=user.role,
            before={"deleted_at": None},
            after={
                "deleted_at": (
                    updated.deleted_at.isoformat() if updated.deleted_at else None
                )
            },
        )

        return self._serialize_asset(updated, include_file=False)

    def restore_asset(self, user: UserModel, asset_id: str) -> Dict[str, Any]:
        asset = self.assets.get_asset_by_id(asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
            )

        context = self._resolve_scope(user, None)
        is_admin = user.role == "admin"
        self._ensure_manage_permission(context, asset, is_admin)

        updated = self.assets.set_deleted(asset_id, False)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore asset",
            )

        self.audit_logs.create_record(
            asset_id=asset_id,
            action="restore",
            actor_id=user.id,
            actor_role=user.role,
            before={
                "deleted_at": asset.deleted_at.isoformat() if asset.deleted_at else None
            },
            after={"deleted_at": None},
        )

        return self._serialize_asset(updated, include_file=False)

    def reassign_asset(
        self,
        user: UserModel,
        asset_id: str,
        owner_id: str,
        visibility_scope: str,
    ) -> Dict[str, Any]:
        asset = self.assets.get_asset_by_id(asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
            )

        if visibility_scope not in {VISIBILITY_USER, VISIBILITY_GROUP}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid visibility scope",
            )

        before_snapshot = {
            "owner_id": asset.owner_id,
            "visibility_scope": asset.visibility_scope,
        }

        updated = self.assets.update_asset(
            asset_id,
            {
                "owner_id": owner_id,
                "visibility_scope": visibility_scope,
            },
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reassign asset",
            )

        self.audit_logs.create_record(
            asset_id=asset_id,
            action="reassign",
            actor_id=user.id,
            actor_role=user.role,
            before=before_snapshot,
            after={
                "owner_id": owner_id,
                "visibility_scope": visibility_scope,
            },
        )

        return self._serialize_asset(updated, include_file=True)

    def _serialize_asset(
        self, asset: MediaAsset, include_file: bool = False
    ) -> Dict[str, Any]:
        payload = {
            "id": asset.id,
            "display_name": asset.display_name,
            "media_type": asset.media_type,
            "mime_type": asset.mime_type,
            "visibility_scope": asset.visibility_scope,
            "owner_id": asset.owner_id,
            "folder_id": asset.folder_id,
            "tags": asset.tags,
            "metadata": asset.metadata_json,
            "source": asset.source,
            "thumbnail_url": asset.thumbnail_url,
            "checksum": asset.checksum,
            "created_at": asset.created_at.isoformat(),
            "updated_at": asset.updated_at.isoformat(),
            "deleted_at": asset.deleted_at.isoformat() if asset.deleted_at else None,
            "width": asset.width,
            "height": asset.height,
            "duration": asset.duration,
        }

        if include_file:
            file_map = self.generated_files.get_files_by_ids([asset.file_id])
            file_record = file_map.get(asset.file_id)
            payload["file"] = (
                {
                    "id": file_record.id,
                    "cloud_url": file_record.cloud_url,
                    "storage_provider": file_record.storage_provider,
                    "file_size": file_record.file_size,
                    "mime_type": file_record.mime_type,
                    "status": file_record.status,
                }
                if file_record
                else None
            )

        return payload

    # ------------------------------
    # Folders
    # ------------------------------

    def list_folders(
        self, user: UserModel, scope: Optional[str]
    ) -> List[Dict[str, Any]]:
        context = self._resolve_scope(user, scope)
        is_admin = user.role == "admin"

        owner_ids = context.owner_ids if context.owner_ids else None
        visibility_scopes = (
            context.visibility_scopes if context.visibility_scopes else None
        )
        include_deleted = False

        if is_admin:
            owner_ids = None
            visibility_scopes = None

        folders = self.folders.list_folders(
            owner_ids=owner_ids,
            visibility_scopes=visibility_scopes,
            include_deleted=include_deleted,
        )

        return [self._serialize_folder(folder) for folder in folders]

    def create_folder(self, user: UserModel, form: MediaFolderForm) -> Dict[str, Any]:
        context = self._resolve_scope(user, form.visibility_scope)
        is_admin = user.role == "admin"

        if not is_admin and form.visibility_scope == VISIBILITY_GROUP:
            if form.owner_id not in context.manageable_owner_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to create folders for this scope",
                )
        if (
            not is_admin
            and form.visibility_scope == VISIBILITY_USER
            and form.owner_id != user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create folders for other users",
            )

        folder = self.folders.create_folder(form)
        return self._serialize_folder(folder)

    def update_folder(
        self, user: UserModel, folder_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        folder = self.folders.get_folder_by_id(folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
            )

        context = self._resolve_scope(user, folder.visibility_scope)
        is_admin = user.role == "admin"

        if not is_admin and folder.owner_id not in context.manageable_owner_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this folder",
            )

        allowed_fields = {"name", "sort_order", "parent_id"}
        updates = {k: v for k, v in payload.items() if k in allowed_fields}
        if not updates:
            return self._serialize_folder(folder)

        updated = self.folders.update_folder(folder_id, updates)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update folder",
            )
        return self._serialize_folder(updated)

    def delete_folder(self, user: UserModel, folder_id: str) -> Dict[str, Any]:
        folder = self.folders.get_folder_by_id(folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
            )

        context = self._resolve_scope(user, folder.visibility_scope)
        is_admin = user.role == "admin"

        if not is_admin and folder.owner_id not in context.manageable_owner_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to remove this folder",
            )

        updated = self.folders.set_deleted(folder_id, True)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove folder",
            )
        return self._serialize_folder(updated)

    def restore_folder(self, user: UserModel, folder_id: str) -> Dict[str, Any]:
        folder = self.folders.get_folder_by_id(folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
            )

        context = self._resolve_scope(user, folder.visibility_scope)
        is_admin = user.role == "admin"

        if not is_admin and folder.owner_id not in context.manageable_owner_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to restore this folder",
            )

        updated = self.folders.set_deleted(folder_id, False)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore folder",
            )
        return self._serialize_folder(updated)

    def _serialize_folder(self, folder: MediaFolder) -> Dict[str, Any]:
        return {
            "id": folder.id,
            "parent_id": folder.parent_id,
            "visibility_scope": folder.visibility_scope,
            "owner_id": folder.owner_id,
            "name": folder.name,
            "slug": folder.slug,
            "preset_key": folder.preset_key,
            "sort_order": folder.sort_order,
            "is_locked": folder.is_locked,
            "created_at": folder.created_at.isoformat(),
            "updated_at": folder.updated_at.isoformat(),
            "deleted_at": folder.deleted_at.isoformat() if folder.deleted_at else None,
        }

    # ------------------------------
    # Asset creation entry point
    # ------------------------------

    def record_generated_asset(
        self,
        *,
        file_id: str,
        owner_id: str,
        display_name: str,
        media_type: str,
        visibility_scope: str,
        mime_type: Optional[str] = None,
        source: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
        created_by_task_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        thumbnail_url: Optional[str] = None,
        checksum: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[float] = None,
    ) -> MediaAsset:
        form = MediaAssetForm(
            file_id=file_id,
            owner_id=owner_id,
            display_name=display_name,
            media_type=media_type,
            visibility_scope=visibility_scope,
            mime_type=mime_type,
            source=source,
            created_by_user_id=created_by_user_id,
            created_by_task_id=created_by_task_id,
            folder_id=folder_id,
            tags=tags,
            metadata=metadata,
            thumbnail_url=thumbnail_url,
            checksum=checksum,
            width=width,
            height=height,
            duration=duration,
        )
        return self.assets.create_asset(form)


media_library_service = MediaLibraryService()
