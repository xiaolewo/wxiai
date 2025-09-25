import json
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import httpx
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import Response
from pydantic import BaseModel, Field

from open_webui.models.media_library import (
    MediaFolderForm,
    MediaLibrarySettingsForm,
    VISIBILITY_GROUP,
    VISIBILITY_USER,
)
from open_webui.services.media_library import media_library_service
from open_webui.services.file_manager import get_file_manager
from open_webui.utils.auth import get_verified_user
from open_webui.storage.provider import Storage

try:  # pragma: no cover - optional dependency
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover
    Image = None

logger = logging.getLogger(__name__)

router = APIRouter()


class MediaAssetUpdateForm(BaseModel):
    display_name: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[dict] = None
    metadata: Optional[dict] = None
    thumbnail_url: Optional[str] = None


class MediaFolderCreateForm(BaseModel):
    name: str
    owner_id: str
    visibility_scope: str = Field(default="user")
    parent_id: Optional[str] = None
    sort_order: int = 0
    preset_key: Optional[str] = None
    slug: Optional[str] = None


class MediaFolderUpdateForm(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    parent_id: Optional[str] = None


@router.get("/settings")
async def get_media_library_settings(user=Depends(get_verified_user)):
    """Return media library configuration visible to the current user."""
    try:
        return media_library_service.get_settings()
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Failed to read media library settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read settings: {exc}",
        ) from exc


@router.get("/assets")
async def list_media_assets(
    scope: Optional[str] = Query(default="mine", description="mine|group|all"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    media_type: Optional[str] = Query(default=None),
    folder_id: Optional[str] = Query(default=None),
    include_deleted: bool = Query(default=False),
    search: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    user=Depends(get_verified_user),
):
    return media_library_service.list_assets(
        user=user,
        scope=scope,
        page=page,
        limit=limit,
        media_type=media_type,
        folder_id=folder_id,
        include_deleted=include_deleted,
        search=search,
        source=source,
    )


@router.get("/assets/{asset_id}/content")
async def get_media_asset_content(
    asset_id: str,
    attachment: bool = Query(default=False),
    user=Depends(get_verified_user),
):
    asset = media_library_service.assets.get_asset_by_id(asset_id)
    if not asset or asset.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="媒体资源不存在或已删除",
        )

    is_admin = getattr(user, "role", "") == "admin"
    if not is_admin:
        context = media_library_service._resolve_scope(user, "all")
        allowed_owner_ids = set(context.owner_ids or [])
        allowed_visibilities = set(context.visibility_scopes or [])
        if asset.owner_id not in allowed_owner_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该媒体资源",
            )
        if allowed_visibilities and asset.visibility_scope not in allowed_visibilities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该媒体资源",
            )

    file_record = None
    if asset.file_id:
        file_record = media_library_service.generated_files.get_file_by_id(
            asset.file_id
        )

    display_name = (
        asset.display_name
        or (
            getattr(file_record, "original_filename", None)
            or getattr(file_record, "filename", None)
        )
        or f"asset-{asset_id}"
    )
    mime_type = (
        asset.mime_type
        or (getattr(file_record, "mime_type", None))
        or "application/octet-stream"
    )

    headers = {}
    if attachment:
        headers["Content-Disposition"] = (
            f"attachment; filename*=UTF-8''{quote(display_name)}"
        )

    # Prefer local cache when available
    if file_record and getattr(file_record, "local_path", None):
        try:
            file_path = Storage.get_file(file_record.local_path)
            path_obj = Path(file_path)
            if path_obj.is_file():
                with path_obj.open("rb") as local_fp:
                    return Response(
                        content=local_fp.read(), media_type=mime_type, headers=headers
                    )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("读取本地媒体库文件失败: %s", exc)

    candidate_urls: list[str] = []
    if file_record and getattr(file_record, "cloud_url", None):
        candidate_urls.append(file_record.cloud_url)
    metadata = getattr(asset, "metadata_json", None)
    if isinstance(metadata, dict):
        metadata_url = metadata.get("cloud_url") or metadata.get("download_url")
        if metadata_url:
            candidate_urls.append(str(metadata_url))
    if asset.thumbnail_url:
        candidate_urls.append(asset.thumbnail_url)

    candidate_urls = [
        url
        for idx, url in enumerate(candidate_urls)
        if url and url not in candidate_urls[:idx]
    ]

    if not candidate_urls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="媒体资源缺少可用下载链接",
        )

    errors: list[str] = []
    for url in candidate_urls:
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
            if response.status_code != status.HTTP_200_OK:
                errors.append(f"{url} -> HTTP {response.status_code}")
                continue
            return Response(
                content=response.content, media_type=mime_type, headers=headers
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            errors.append(f"{url} -> {exc}")

    logger.warning(
        "无法获取媒体资源内容",
        extra={
            "asset_id": asset_id,
            "candidate_urls": candidate_urls,
            "errors": errors,
        },
    )
    detail = "无法获取媒体资源内容"
    if errors:
        detail = f"{detail}：{errors[-1]}"
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.patch("/assets/{asset_id}")
async def update_media_asset(
    asset_id: str,
    form: MediaAssetUpdateForm,
    user=Depends(get_verified_user),
):
    return media_library_service.update_asset(
        user=user, asset_id=asset_id, payload=form.model_dump(exclude_unset=True)
    )


@router.delete("/assets/{asset_id}")
async def delete_media_asset(asset_id: str, user=Depends(get_verified_user)):
    return media_library_service.delete_asset(user=user, asset_id=asset_id)


@router.post("/assets/{asset_id}/restore")
async def restore_media_asset(asset_id: str, user=Depends(get_verified_user)):
    return media_library_service.restore_asset(user=user, asset_id=asset_id)


@router.post("/upload")
async def upload_media_asset(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    visibility_scope: str = Form(VISIBILITY_USER),
    owner_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    user=Depends(get_verified_user),
):
    visibility_scope = (visibility_scope or VISIBILITY_USER).lower()
    if visibility_scope not in {VISIBILITY_USER, VISIBILITY_GROUP}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="可见范围必须是 user 或 group",
        )

    resolved_owner_id = owner_id
    if visibility_scope == VISIBILITY_USER:
        resolved_owner_id = user.id
    elif visibility_scope == VISIBILITY_GROUP and not resolved_owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传到工作组时必须提供 owner_id",
        )

    content_type = (file.content_type or "").lower()
    if content_type.startswith("video"):
        media_type = "video"
    elif content_type.startswith("image"):
        media_type = "image"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="暂仅支持上传图片或视频文件"
        )

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="文件内容为空"
        )

    original_name = file.filename or "uploaded_file"
    extension = Path(original_name).suffix
    if not extension:
        extension = ".mp4" if media_type == "video" else ".png"
    safe_filename = original_name

    metadata_payload: dict[str, str] = {
        "original_filename": original_name,
        "uploader": user.id,
    }
    if title:
        metadata_payload["title"] = title
        metadata_payload["prompt"] = title
    if folder_id:
        metadata_payload["folder_id"] = folder_id
    metadata_payload["visibility_scope"] = visibility_scope
    metadata_payload["owner_id"] = resolved_owner_id or user.id
    metadata_payload["size"] = str(len(raw_bytes))

    tags_payload: Optional[dict] = None
    if tags:
        try:
            parsed = json.loads(tags)
            if isinstance(parsed, dict):
                tags_payload = parsed
            else:
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            tags_payload = {"label": tags}
    if tags_payload:
        metadata_payload["tags"] = tags_payload

    width = height = None
    if media_type == "image" and Image is not None:
        try:  # pragma: no cover - trivial pillow usage
            with Image.open(BytesIO(raw_bytes)) as img:
                width, height = img.size
        except Exception:  # pragma: no cover - best effort only
            width = height = None

    file_manager = get_file_manager()
    success, message, generated_file = await file_manager.save_generated_content(
        user_id=user.id,
        file_data=raw_bytes,
        filename=safe_filename,
        file_type=media_type,
        source_type="user_upload",
        source_task_id=None,
        metadata=metadata_payload,
        visibility_scope=visibility_scope,
        owner_id=resolved_owner_id,
        created_by_user_id=user.id,
        folder_id=folder_id,
        tags=tags_payload,
        width=width,
        height=height,
    )

    if not success or not generated_file:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message or "文件上传失败",
        )
    asset = media_library_service.assets.get_asset_by_file_id(generated_file.id)
    if asset is None:
        asset = media_library_service.record_generated_asset(
            file_id=generated_file.id,
            owner_id=resolved_owner_id or user.id,
            display_name=title or original_name,
            media_type=media_type,
            visibility_scope=visibility_scope,
            mime_type=content_type or None,
            source="user-upload",
            created_by_user_id=user.id,
            folder_id=folder_id,
            tags=tags_payload,
            metadata=metadata_payload,
            width=width,
            height=height,
        )
    elif title and title != asset.display_name:
        media_library_service.update_asset(
            user=user,
            asset_id=asset.id,
            payload={"display_name": title},
        )
        asset = media_library_service.assets.get_asset_by_id(asset.id) or asset

    return media_library_service._serialize_asset(asset, include_file=True)


@router.get("/folders")
async def list_media_folders(
    scope: Optional[str] = Query(default="mine"),
    user=Depends(get_verified_user),
):
    return media_library_service.list_folders(user=user, scope=scope)


@router.post("/folders")
async def create_media_folder(
    form: MediaFolderCreateForm, user=Depends(get_verified_user)
):
    folder_form = MediaFolderForm(
        name=form.name,
        parent_id=form.parent_id,
        visibility_scope=form.visibility_scope,
        owner_id=form.owner_id,
        preset_key=form.preset_key,
        sort_order=form.sort_order,
        slug=form.slug,
    )
    return media_library_service.create_folder(user=user, form=folder_form)


@router.patch("/folders/{folder_id}")
async def update_media_folder(
    folder_id: str,
    form: MediaFolderUpdateForm,
    user=Depends(get_verified_user),
):
    return media_library_service.update_folder(
        user=user,
        folder_id=folder_id,
        payload=form.model_dump(exclude_unset=True),
    )


@router.delete("/folders/{folder_id}")
async def delete_media_folder(folder_id: str, user=Depends(get_verified_user)):
    return media_library_service.delete_folder(user=user, folder_id=folder_id)


@router.post("/folders/{folder_id}/restore")
async def restore_media_folder(folder_id: str, user=Depends(get_verified_user)):
    return media_library_service.restore_folder(user=user, folder_id=folder_id)
