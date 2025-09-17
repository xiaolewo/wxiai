"""Jimeng4 image generation router"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from open_webui.internal.db import engine
from open_webui.models.jimeng4 import (
    Jimeng4Config,
    Jimeng4ConfigForm,
    Jimeng4GenerateRequest,
    Jimeng4Task,
    Jimeng4UploadResponse,
)
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.credit.utils import check_credit_by_user_id
from open_webui.utils.jimeng4 import (
    Jimeng4ApiClient,
    Jimeng4ApiError,
    build_user_config_dict,
    deduct_user_credits,
    persist_generated_images,
    refund_user_credits,
    sanitize_config_form,
)
from open_webui.services.file_manager import get_file_manager

router = APIRouter(prefix="/jimeng4", tags=["jimeng4"])

_jimeng4_client: Jimeng4ApiClient | None = None

logger = logging.getLogger(__name__)


def ensure_jimeng4_tables() -> None:
    try:
        Jimeng4Config.__table__.create(bind=engine, checkfirst=True)
        Jimeng4Task.__table__.create(bind=engine, checkfirst=True)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("jimeng4_tasks")}
        needed = {
            "stream_events": "TEXT",
            "raw_stream": "TEXT",
        }
        with engine.begin() as conn:
            for name, col_type in needed.items():
                if name not in columns:
                    logger.info("Adding jimeng4_tasks.%s column", name)
                    conn.execute(
                        text(f"ALTER TABLE jimeng4_tasks ADD COLUMN {name} {col_type}")
                    )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to ensure Jimeng4 tables: %s", exc)


def get_jimeng4_client(reset: bool = False) -> Jimeng4ApiClient:
    global _jimeng4_client

    if reset:
        _jimeng4_client = None

    if _jimeng4_client is None:
        ensure_jimeng4_tables()
        config = Jimeng4Config.get_config()
        if not config or not config.enabled:
            raise HTTPException(
                status_code=400, detail="Jimeng4 service is not enabled"
            )
        if not config.base_url or not config.api_key:
            raise HTTPException(
                status_code=400, detail="Jimeng4 service not configured"
            )
        _jimeng4_client = Jimeng4ApiClient(config)
    return _jimeng4_client


@router.get("/config")
async def get_jimeng4_config(user=Depends(get_admin_user)):
    ensure_jimeng4_tables()
    config = Jimeng4Config.get_config()
    if not config:
        return Jimeng4ConfigForm().model_dump()
    return config.to_dict()


@router.post("/config")
async def save_jimeng4_config(config_data: dict, user=Depends(get_admin_user)):
    try:
        sanitized = sanitize_config_form(config_data)
        config = Jimeng4Config.save_config(sanitized)
        get_jimeng4_client(reset=True)
        return {"message": "配置保存成功", "config": config.to_dict()}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"保存配置失败: {exc}") from exc


@router.get("/config/test")
async def test_jimeng4_connection(user=Depends(get_admin_user)):
    try:
        client = get_jimeng4_client()
        payload = Jimeng4GenerateRequest(prompt="ping test", n=1, stream=False)
        await client.generate_images(payload)
        return {"success": True, "message": "连接测试成功"}
    except Jimeng4ApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/config/user")
async def get_jimeng4_user_config(user=Depends(get_verified_user)):
    ensure_jimeng4_tables()
    config = Jimeng4Config.get_config()
    if not config:
        defaults = Jimeng4ConfigForm()
        return build_user_config_dict(defaults)
    return build_user_config_dict(config)


@router.post("/reference/upload", response_model=Jimeng4UploadResponse)
async def upload_jimeng4_reference_image(
    file: UploadFile = File(...),
    user=Depends(get_verified_user),
):
    ensure_jimeng4_tables()
    if not file.content_type or not file.content_type.startswith("image/"):
        return Jimeng4UploadResponse(success=False, message="仅支持图片文件")

    file_content = await file.read()
    if not file_content:
        return Jimeng4UploadResponse(success=False, message="文件内容不能为空")

    if len(file_content) > 10 * 1024 * 1024:
        return Jimeng4UploadResponse(success=False, message="文件大小不能超过10MB")

    file_manager = get_file_manager()
    if not file_manager:
        return Jimeng4UploadResponse(success=False, message="文件存储服务不可用")

    filename = f"jimeng4_reference_{uuid.uuid4().hex}.jpg"
    success, message, record = await file_manager.save_generated_content(
        user_id=user.id,
        file_data=file_content,
        filename=filename,
        file_type="image",
        source_type="jimeng4_reference",
        metadata={
            "original_filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(file_content),
        },
    )

    if success and record:
        url = record.cloud_url or record.local_path
        logger.info("Jimeng4 reference image uploaded: %s", url)
        return Jimeng4UploadResponse(
            success=True,
            message="图片上传成功",
            url=url,
            file_id=record.id,
        )

    logger.error("Jimeng4 reference image upload failed: %s", message)
    return Jimeng4UploadResponse(success=False, message=f"上传失败: {message}")


@router.post("/generate")
async def generate_jimeng4_images(
    request: Jimeng4GenerateRequest,
    user=Depends(get_verified_user),
):
    ensure_jimeng4_tables()
    config = Jimeng4Config.get_config()
    if not config or not config.enabled:
        raise HTTPException(status_code=400, detail="即梦4服务未启用")

    n = request.n or config.default_n
    credits_cost = config.credits_per_image * max(1, n)

    check_credit_by_user_id(
        user.id,
        {
            "model": request.model or config.default_model,
            "metadata": {"features": {"image_generation": True}},
        },
    )

    task = Jimeng4Task.create_task(
        user_id=user.id,
        prompt=request.prompt,
        model=request.model or config.default_model,
        size=request.size or config.default_size,
        sequential_mode=request.sequential_image_generation
        or config.default_sequential_mode,
        n=n,
        request_image_urls=request.image,
        response_format=request.response_format,
        stream=bool(request.stream),
        watermark=(
            config.default_watermark if request.watermark is None else request.watermark
        ),
        credits_cost=credits_cost,
    )

    deduct_user_credits(user.id, credits_cost, "jimeng4-generate", task.id)

    try:
        client = get_jimeng4_client()
        response = await client.generate_images(request)
        storage_result = await persist_generated_images(task, response)

        Jimeng4Task.update_task(
            task.id,
            status="success",
            response_urls=storage_result["response_urls"],
            cloud_image_urls=storage_result["cloud_urls"],
            stream_events=response.get("stream_events"),
            raw_stream=response.get("raw_stream"),
            usage=response.get("usage"),
            completed_at=datetime.utcnow(),
        )
        task = Jimeng4Task.get_task(task.id)
        return {"task": task.to_dict(), "raw": response}
    except Jimeng4ApiError as exc:
        Jimeng4Task.update_task(task.id, status="failed", fail_reason=str(exc))
        refund_user_credits(user.id, credits_cost, "jimeng4-failed", task.id)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        Jimeng4Task.update_task(task.id, status="failed", fail_reason=str(exc))
        refund_user_credits(user.id, credits_cost, "jimeng4-failed", task.id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tasks")
async def list_jimeng4_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(get_verified_user),
):
    ensure_jimeng4_tables()
    try:
        tasks = Jimeng4Task.list_tasks(user.id, limit=limit, offset=offset)
    except OperationalError as exc:
        if "no such table" in str(exc).lower():
            ensure_jimeng4_tables()
            tasks = Jimeng4Task.list_tasks(user.id, limit=limit, offset=offset)
        else:
            logger.exception("Failed to list Jimeng4 tasks: %s", exc)
            raise HTTPException(status_code=500, detail="无法获取即梦4任务") from exc
    return {"items": [task.to_dict() for task in tasks]}


@router.get("/tasks/{task_id}")
async def get_jimeng4_task(task_id: str, user=Depends(get_verified_user)):
    ensure_jimeng4_tables()
    task = Jimeng4Task.get_task(task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task.to_dict()


@router.delete("/tasks/{task_id}")
async def delete_jimeng4_task(task_id: str, user=Depends(get_verified_user)):
    ensure_jimeng4_tables()
    task = Jimeng4Task.get_task(task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="任务不存在")
    Jimeng4Task.update_task(task_id, status="deleted")
    return {"success": True}
