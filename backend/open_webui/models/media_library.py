import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from open_webui.internal.db import Base, JSONField, get_db


VISIBILITY_USER = "user"
VISIBILITY_GROUP = "group"


class MediaFolder(Base):
    __tablename__ = "media_folder"

    id = Column(String(255), primary_key=True)
    parent_id = Column(String(255), ForeignKey("media_folder.id"), nullable=True)
    visibility_scope = Column(String(20), nullable=False, default=VISIBILITY_USER)
    owner_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=True)
    preset_key = Column(String(100), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_locked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_media_folder_owner_scope", "owner_id", "visibility_scope"),
        {"extend_existing": True},
    )


class MediaAsset(Base):
    __tablename__ = "media_asset"

    id = Column(String(255), primary_key=True)
    file_id = Column(String(255), ForeignKey("generated_files.id"), nullable=False)
    visibility_scope = Column(String(20), nullable=False, default=VISIBILITY_USER)
    owner_id = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    media_type = Column(String(20), nullable=False)
    mime_type = Column(String(100), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)
    source = Column(String(100), nullable=True)
    folder_id = Column(String(255), ForeignKey("media_folder.id"), nullable=True)
    tags = Column(JSONField, nullable=True)
    metadata_json = Column("metadata", JSONField, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_by_task_id = Column(String(255), nullable=True)
    created_by_user_id = Column(String(255), nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    checksum = Column(String(128), nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_media_asset_owner_scope", "owner_id", "visibility_scope"),
        Index("ix_media_asset_media_type", "media_type"),
        Index("ix_media_asset_created_at", "created_at"),
        {"extend_existing": True},
    )


class MediaLibrarySettings(Base):
    __tablename__ = "media_library_settings"

    id = Column(String(255), primary_key=True)
    enable_group_sharing = Column(Boolean, nullable=False, default=False)
    allow_bulk_download = Column(Boolean, nullable=False, default=True)
    allowed_media_types = Column(JSONField, nullable=True)
    default_visibility = Column(String(20), nullable=False, default=VISIBILITY_USER)
    max_storage_per_user = Column(BigInteger, nullable=True)
    max_storage_per_group = Column(BigInteger, nullable=True)
    signed_url_ttl_seconds = Column(Integer, nullable=True)
    thumbnail_strategy = Column(String(50), nullable=True)
    extra_config = Column(JSONField, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    __table_args__ = ({"extend_existing": True},)


class MediaAssetAudit(Base):
    __tablename__ = "media_asset_audit"

    id = Column(String(255), primary_key=True)
    asset_id = Column(String(255), ForeignKey("media_asset.id"), nullable=False)
    action = Column(String(50), nullable=False)
    actor_id = Column(String(255), nullable=False)
    actor_role = Column(String(50), nullable=True)
    before = Column(JSONField, nullable=True)
    after = Column(JSONField, nullable=True)
    metadata_json = Column("metadata", JSONField, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_media_asset_audit_asset_id", "asset_id"),
        Index("ix_media_asset_audit_created_at", "created_at"),
        {"extend_existing": True},
    )


# ------------------------------
# Pydantic models
# ------------------------------


class MediaFolderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parent_id: Optional[str] = None
    visibility_scope: str
    owner_id: str
    name: str
    slug: Optional[str] = None
    preset_key: Optional[str] = None
    sort_order: int = 0
    is_locked: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class MediaFolderForm(BaseModel):
    name: str
    parent_id: Optional[str] = None
    visibility_scope: str = Field(default=VISIBILITY_USER)
    owner_id: Optional[str] = None
    preset_key: Optional[str] = None
    sort_order: int = 0
    slug: Optional[str] = None


class MediaAssetModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    file_id: str
    visibility_scope: str
    owner_id: str
    display_name: str
    media_type: str
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    source: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata_json")
    created_at: datetime
    updated_at: datetime
    created_by_task_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    checksum: Optional[str] = None
    deleted_at: Optional[datetime] = None


class MediaAssetForm(BaseModel):
    file_id: str
    display_name: str
    media_type: str
    mime_type: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    visibility_scope: str = Field(default=VISIBILITY_USER)
    owner_id: Optional[str] = None
    source: Optional[str] = None
    created_by_task_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    checksum: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None


class MediaLibrarySettingsModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    enable_group_sharing: bool
    allow_bulk_download: bool
    allowed_media_types: Optional[List[str]] = None
    default_visibility: str
    max_storage_per_user: Optional[int] = None
    max_storage_per_group: Optional[int] = None
    signed_url_ttl_seconds: Optional[int] = None
    thumbnail_strategy: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class MediaLibrarySettingsForm(BaseModel):
    enable_group_sharing: Optional[bool] = None
    allow_bulk_download: Optional[bool] = None
    allowed_media_types: Optional[List[str]] = None
    default_visibility: Optional[str] = None
    max_storage_per_user: Optional[int] = None
    max_storage_per_group: Optional[int] = None
    signed_url_ttl_seconds: Optional[int] = None
    thumbnail_strategy: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None


class MediaAssetAuditRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    asset_id: str
    action: str
    actor_id: str
    actor_role: Optional[str]
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata_json")
    created_at: datetime


# ------------------------------
# Table helpers
# ------------------------------


class MediaFoldersTable:
    def create_folder(self, form: MediaFolderForm) -> MediaFolder:
        if not form.owner_id:
            raise ValueError("owner_id is required for media folders")
        with get_db() as db:
            folder = MediaFolder(
                id=str(uuid.uuid4()),
                parent_id=form.parent_id,
                visibility_scope=form.visibility_scope,
                owner_id=form.owner_id,
                name=form.name,
                slug=form.slug,
                preset_key=form.preset_key,
                sort_order=form.sort_order,
                is_locked=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(folder)
            db.commit()
            db.refresh(folder)
            return folder

    def get_folder_by_id(self, folder_id: str) -> Optional[MediaFolder]:
        with get_db() as db:
            return db.query(MediaFolder).filter(MediaFolder.id == folder_id).first()

    def list_folders(
        self,
        *,
        owner_ids: Optional[List[str]] = None,
        visibility_scopes: Optional[List[str]] = None,
        include_deleted: bool = False,
    ) -> List[MediaFolder]:
        with get_db() as db:
            query = db.query(MediaFolder)
            if owner_ids:
                query = query.filter(MediaFolder.owner_id.in_(owner_ids))
            if visibility_scopes:
                query = query.filter(
                    MediaFolder.visibility_scope.in_(visibility_scopes)
                )
            if not include_deleted:
                query = query.filter(MediaFolder.deleted_at.is_(None))

            return query.order_by(
                MediaFolder.sort_order.asc(), MediaFolder.created_at.asc()
            ).all()

    def update_folder(
        self, folder_id: str, payload: Dict[str, Any]
    ) -> Optional[MediaFolder]:
        with get_db() as db:
            folder = db.query(MediaFolder).filter(MediaFolder.id == folder_id).first()
            if not folder:
                return None

            for key, value in payload.items():
                if hasattr(folder, key):
                    setattr(folder, key, value)
            folder.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(folder)
            return folder

    def set_deleted(self, folder_id: str, deleted: bool) -> Optional[MediaFolder]:
        with get_db() as db:
            folder = db.query(MediaFolder).filter(MediaFolder.id == folder_id).first()
            if not folder:
                return None

            folder.deleted_at = datetime.utcnow() if deleted else None
            folder.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(folder)
            return folder


class MediaAssetsTable:
    def create_asset(self, form: MediaAssetForm) -> MediaAsset:
        if not form.owner_id:
            raise ValueError("owner_id is required for media assets")
        with get_db() as db:
            asset = MediaAsset(
                id=str(uuid.uuid4()),
                file_id=form.file_id,
                visibility_scope=form.visibility_scope,
                owner_id=form.owner_id,
                display_name=form.display_name,
                media_type=form.media_type,
                mime_type=form.mime_type,
                folder_id=form.folder_id,
                tags=form.tags,
                metadata_json=form.metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by_task_id=form.created_by_task_id,
                created_by_user_id=form.created_by_user_id,
                thumbnail_url=form.thumbnail_url,
                checksum=form.checksum,
                width=form.width,
                height=form.height,
                duration=form.duration,
                source=form.source,
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)
            return asset

    def get_asset_by_id(self, asset_id: str) -> Optional[MediaAsset]:
        with get_db() as db:
            return db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()

    def get_asset_by_file_id(self, file_id: str) -> Optional[MediaAsset]:
        with get_db() as db:
            return (
                db.query(MediaAsset)
                .filter(MediaAsset.file_id == file_id)
                .order_by(MediaAsset.created_at.desc())
                .first()
            )

    def list_assets(
        self,
        *,
        owner_ids: Optional[List[str]] = None,
        visibility_scopes: Optional[List[str]] = None,
        media_types: Optional[List[str]] = None,
        folder_id: Optional[str] = None,
        include_deleted: bool = False,
        search: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[MediaAsset], int]:
        with get_db() as db:
            query = db.query(MediaAsset)

            if owner_ids:
                query = query.filter(MediaAsset.owner_id.in_(owner_ids))
            if visibility_scopes:
                query = query.filter(MediaAsset.visibility_scope.in_(visibility_scopes))
            if media_types:
                query = query.filter(MediaAsset.media_type.in_(media_types))
            if folder_id:
                query = query.filter(MediaAsset.folder_id == folder_id)
            if not include_deleted:
                query = query.filter(MediaAsset.deleted_at.is_(None))
            if search:
                like_term = f"%{search}%"
                query = query.filter(MediaAsset.display_name.ilike(like_term))
            if source:
                query = query.filter(MediaAsset.source == source)

            total = query.count()
            items = (
                query.order_by(MediaAsset.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return items, total

    def update_asset(
        self, asset_id: str, payload: Dict[str, Any]
    ) -> Optional[MediaAsset]:
        with get_db() as db:
            asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
            if not asset:
                return None

            for key, value in payload.items():
                if hasattr(asset, key):
                    setattr(asset, key, value)
            asset.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(asset)
            return asset

    def set_deleted(self, asset_id: str, deleted: bool) -> Optional[MediaAsset]:
        with get_db() as db:
            asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
            if not asset:
                return None

            asset.deleted_at = datetime.utcnow() if deleted else None
            asset.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(asset)
            return asset


class MediaLibrarySettingsTable:
    def get_settings(self) -> Optional[MediaLibrarySettings]:
        with get_db() as db:
            return db.query(MediaLibrarySettings).first()

    def upsert_settings(self, form: MediaLibrarySettingsForm) -> MediaLibrarySettings:
        with get_db() as db:
            settings = db.query(MediaLibrarySettings).first()
            now = datetime.utcnow()
            payload = form.model_dump(exclude_unset=True)

            if settings:
                for key, value in payload.items():
                    setattr(settings, key, value)
                settings.updated_at = now
            else:
                settings = MediaLibrarySettings(
                    id=str(uuid.uuid4()),
                    created_at=now,
                    updated_at=now,
                    **payload,
                )
                db.add(settings)

            db.commit()
            db.refresh(settings)
            return settings


class MediaAssetAuditTable:
    def create_record(
        self,
        asset_id: str,
        action: str,
        actor_id: str,
        actor_role: Optional[str] = None,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MediaAssetAudit:
        with get_db() as db:
            record = MediaAssetAudit(
                id=str(uuid.uuid4()),
                asset_id=asset_id,
                action=action,
                actor_id=actor_id,
                actor_role=actor_role,
                before=before,
                after=after,
                metadata_json=metadata,
                created_at=datetime.utcnow(),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record


MediaFolders = MediaFoldersTable
MediaAssets = MediaAssetsTable
MediaLibrarySettingsTableHelper = MediaLibrarySettingsTable
MediaAssetAuditLogs = MediaAssetAuditTable
