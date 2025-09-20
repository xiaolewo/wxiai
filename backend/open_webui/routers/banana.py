"""Banana image generation router"""

from __future__ import annotations

import base64
import logging
from datetime import datetime
from typing import List, Optional

import httpx

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import inspect, text

from open_webui.internal.db import engine
from open_webui.models.banana import BananaConfig, BananaConfigForm, BananaTask
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.credit.utils import check_credit_by_user_id
from open_webui.utils.banana import (
    BananaApiClient,
    BananaApiError,
    deduct_user_credits,
    refund_user_credits,
    normalize_config_form,
    persist_generated_images,
)

router = APIRouter(prefix="/banana", tags=["banana"])

logger = logging.getLogger(__name__)

_banana_client: Optional[BananaApiClient] = None


class BananaConfigUpdate(BaseModel):
    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    default_model: str = "nano-banana"
    default_output_format: str = "url"
    default_aspect_ratio: str = "1:1"
    credits_per_generation: int = 10
    credits_per_edit: int = 10
    max_concurrent_tasks: int = 5
    task_timeout: int = 300000


class BananaGenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    aspect_ratio: Optional[str] = None
    response_format: Optional[str] = None
    reference_urls: Optional[List[str]] = None
    images: Optional[List[str]] = None  # base64 data URLs


class BananaTaskResponse(BaseModel):
    task: dict
    raw: dict


from pydantic import BaseModel


def ensure_banana_tables() -> None:
    try:
        BananaConfig.__table__.create(bind=engine, checkfirst=True)
        BananaTask.__table__.create(bind=engine, checkfirst=True)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("banana_tasks")}
        needed = {
            "usage": "JSON",
            "response_urls": "JSON",
        }
        with engine.begin() as conn:
            for name, col_type in needed.items():
                if name not in columns:
                    conn.execute(
                        text(f"ALTER TABLE banana_tasks ADD COLUMN {name} {col_type}")
                    )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to ensure banana tables: %s", exc)


def get_banana_client(reset: bool = False) -> BananaApiClient:
    global _banana_client
    if reset:
        _banana_client = None

    if _banana_client is None:
        ensure_banana_tables()
        config = BananaConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="Banana service not configured")
        if not config.base_url:
            raise HTTPException(status_code=400, detail="Banana base URL missing")
        _banana_client = BananaApiClient(config)
    return _banana_client


@router.get("/config")
async def get_banana_config(user=Depends(get_admin_user)):
    ensure_banana_tables()
    config = BananaConfig.get_config()
    if not config:
        return BananaConfigForm().model_dump()
    return config.to_dict()


@router.post("/config")
async def save_banana_config(
    config_data: BananaConfigUpdate, user=Depends(get_admin_user)
):
    try:
        normalized = normalize_config_form(config_data.model_dump())
        config = BananaConfig.save_config(normalized)
        get_banana_client(reset=True)
        return {"message": "配置已保存", "config": config.to_dict()}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"保存配置失败: {exc}") from exc


@router.get("/config/user")
async def get_banana_user_config(user=Depends(get_verified_user)):
    ensure_banana_tables()
    config = BananaConfig.get_config()
    if not config:
        defaults = BananaConfigForm()
        return defaults.model_dump()
    data = config.to_dict()
    data.pop("api_key", None)
    return data


def _prepare_files(file_list: Optional[List[str]]) -> List[tuple[str, bytes, str]]:
    prepared: List[tuple[str, bytes, str]] = []
    if not file_list:
        return prepared

    for index, encoded in enumerate(file_list):
        if not encoded:
            continue
        try:
            if encoded.startswith("data:"):
                metadata, b64data = encoded.split(",", 1)
                content_type = metadata.split(";")[0][5:]
            else:
                content_type = "image/png"
                b64data = encoded
            binary = base64.b64decode(b64data)
            prepared.append((f"reference-{index}.png", binary, content_type))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to decode reference image: %s", exc)
    return prepared


def _aspect_ratio_to_size(aspect_ratio: Optional[str]) -> str:
    """Map aspect ratio (e.g. 3:4) to a pixel size string for Banana API."""

    default_size = "1024x1024"
    if not aspect_ratio:
        return default_size

    try:
        width_part, height_part = aspect_ratio.split(":", 1)
        width_ratio = float(width_part)
        height_ratio = float(height_part)
        if width_ratio <= 0 or height_ratio <= 0:
            return default_size

        base = 1024.0
        if width_ratio >= height_ratio:
            width = base
            height = base * (height_ratio / width_ratio)
        else:
            height = base
            width = base * (width_ratio / height_ratio)

        width = max(64, int(width // 8 * 8))
        height = max(64, int(height // 8 * 8))
        return f"{width}x{height}"
    except Exception:  # noqa: BLE001
        return default_size


@router.post("/generate", response_model=BananaTaskResponse)
async def generate_banana_images(
    form_data: BananaGenerateRequest,
    user=Depends(get_verified_user),
):
    ensure_banana_tables()
    config = BananaConfig.get_config()
    if not config or not config.enabled:
        raise HTTPException(status_code=400, detail="Banana 服务未启用")

    is_edit = bool((form_data.reference_urls or form_data.images))
    credits_cost = config.credits_per_edit if is_edit else config.credits_per_generation

    check_credit_by_user_id(
        user_id=user.id,
        form_data={
            "model": form_data.model or config.default_model,
            "metadata": {"features": {"image_generation": True}},
        },
    )

    task = BananaTask.create_task(
        user_id=user.id,
        task_type="edit" if is_edit else "generation",
        prompt=form_data.prompt,
        model=form_data.model or config.default_model,
        aspect_ratio=form_data.aspect_ratio or config.default_aspect_ratio,
        response_format=form_data.response_format or config.default_output_format,
        request_image_urls=form_data.reference_urls,
        credits_cost=credits_cost,
    )

    deduct_user_credits(user.id, credits_cost, "banana-generate", task.id)

    try:
        client = get_banana_client()
        payload = {
            "prompt": form_data.prompt,
            "model": form_data.model or config.default_model,
            "response_format": form_data.response_format
            or config.default_output_format,
        }
        if not is_edit:
            aspect_ratio = form_data.aspect_ratio or config.default_aspect_ratio
            payload["aspect_ratio"] = aspect_ratio
            payload["size"] = _aspect_ratio_to_size(aspect_ratio)
            if form_data.reference_urls:
                payload["image_urls"] = form_data.reference_urls
            response = await client.generate_text(payload)
        else:
            aspect_ratio = form_data.aspect_ratio or config.default_aspect_ratio
            payload["size"] = _aspect_ratio_to_size(aspect_ratio)
            reference_files = _prepare_files(form_data.images)
            if not reference_files and form_data.reference_urls:

                async def _download(url: str) -> tuple[str, bytes, str]:
                    async with httpx.AsyncClient(timeout=60.0) as dl:
                        resp = await dl.get(url)
                        resp.raise_for_status()
                        content_type = resp.headers.get("content-type", "image/png")
                        return url.split("/")[-1], resp.content, content_type

                downloads = [_download(url) for url in form_data.reference_urls or []]
                if downloads:
                    reference_files.extend(await asyncio.gather(*downloads))
            if not reference_files:
                raise HTTPException(status_code=400, detail="请至少提供一张参考图")
            response = await client.generate_edit(payload, reference_files)

        storage_result = await persist_generated_images(task, response)
        BananaTask.update_task(
            task.id,
            status="success",
            response_urls=storage_result["response_urls"],
            cloud_image_urls=storage_result["cloud_urls"],
            usage=response.get("usage"),
            completed_at=datetime.utcnow(),
        )
        task = BananaTask.get_task(task.id)
        return {"task": task.to_dict(), "raw": response}
    except (BananaApiError, HTTPException) as exc:
        BananaTask.update_task(task.id, status="failed", fail_reason=str(exc))
        refund_user_credits(user.id, credits_cost, "banana-failed", task.id)
        raise
    except Exception as exc:  # noqa: BLE001
        BananaTask.update_task(task.id, status="failed", fail_reason=str(exc))
        refund_user_credits(user.id, credits_cost, "banana-failed", task.id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tasks")
async def list_banana_tasks(
    limit: int = 20, offset: int = 0, user=Depends(get_verified_user)
):
    ensure_banana_tables()
    tasks = BananaTask.list_tasks(user.id, limit=limit, offset=offset)
    return {"items": [task.to_dict() for task in tasks]}


@router.get("/tasks/{task_id}")
async def get_banana_task(task_id: str, user=Depends(get_verified_user)):
    ensure_banana_tables()
    task = BananaTask.get_task(task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task.to_dict()


@router.delete("/tasks/{task_id}")
async def delete_banana_task(task_id: str, user=Depends(get_verified_user)):
    ensure_banana_tables()
    task = BananaTask.get_task(task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="任务不存在")
    BananaTask.update_task(task_id, status="deleted", completed_at=datetime.utcnow())
    return {"success": True}
