import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from open_webui.models.media_library import MediaLibrarySettingsForm
from open_webui.services.media_library import media_library_service
from open_webui.utils.auth import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()


class MediaLibrarySettingsUpdateForm(MediaLibrarySettingsForm):
    pass


class ReassignAssetForm(BaseModel):
    owner_id: str = Field(..., description="New owner identifier (user or group)")
    visibility_scope: str = Field(..., description="user|group")


@router.get("/settings")
async def admin_get_media_library_settings(user=Depends(get_admin_user)):
    return media_library_service.get_settings()


@router.patch("/settings")
async def admin_update_media_library_settings(
    form: MediaLibrarySettingsUpdateForm,
    user=Depends(get_admin_user),
):
    try:
        return media_library_service.update_settings(form)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Failed to update media library settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {exc}",
        ) from exc


@router.get("/assets")
async def admin_list_media_assets(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    media_type: Optional[str] = Query(default=None),
    folder_id: Optional[str] = Query(default=None),
    include_deleted: bool = Query(default=False),
    search: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    owner_id: Optional[str] = Query(default=None),
    visibility_scope: Optional[str] = Query(default=None),
    user=Depends(get_admin_user),
):
    return media_library_service.list_assets(
        user=user,
        scope="admin",
        page=page,
        limit=limit,
        media_type=media_type,
        folder_id=folder_id,
        include_deleted=include_deleted,
        search=search,
        source=source,
        owner_id=owner_id,
        visibility_scope_filter=visibility_scope,
    )


@router.post("/assets/{asset_id}/reassign")
async def admin_reassign_media_asset(
    asset_id: str,
    form: ReassignAssetForm,
    user=Depends(get_admin_user),
):
    return media_library_service.reassign_asset(
        user=user,
        asset_id=asset_id,
        owner_id=form.owner_id,
        visibility_scope=form.visibility_scope,
    )


@router.patch("/assets/{asset_id}")
async def admin_update_media_asset(
    asset_id: str,
    payload: dict,
    user=Depends(get_admin_user),
):
    return media_library_service.update_asset(
        user=user,
        asset_id=asset_id,
        payload=payload,
    )


@router.delete("/assets/{asset_id}")
async def admin_delete_media_asset(asset_id: str, user=Depends(get_admin_user)):
    return media_library_service.delete_asset(user=user, asset_id=asset_id)


@router.post("/assets/{asset_id}/restore")
async def admin_restore_media_asset(asset_id: str, user=Depends(get_admin_user)):
    return media_library_service.restore_asset(user=user, asset_id=asset_id)


@router.get("/folders")
async def admin_list_folders(
    user=Depends(get_admin_user),
    visibility_scope: Optional[str] = Query(default=None),
    owner_id: Optional[str] = Query(default=None),
):
    scope_param = visibility_scope or "admin"
    folders = media_library_service.list_folders(user=user, scope=scope_param)
    if owner_id:
        folders = [folder for folder in folders if folder.get("owner_id") == owner_id]
    return folders
