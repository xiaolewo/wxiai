"""Seedance (新即梦) 视频生成 API 路由"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from open_webui.models.seedance import (
    SeedanceConfig,
    SeedanceConfigForm,
    SeedanceGenerateRequestModel,
    SeedanceTask,
    SeedanceCreditsResponse,
)
from open_webui.services.file_manager import get_file_manager
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.seedance import (
    SeedanceApiClient,
    add_user_credits,
    deduct_user_credits,
    get_user_credit_balance,
    validate_user_credits,
)
from open_webui.internal.db import get_db

router = APIRouter(prefix="/seedance", tags=["seedance"])

SEEDANCE_LITE_IMAGE_MODEL = "doubao-seedance-1-0-lite-i2v-250428"

_seedance_client: Optional[SeedanceApiClient] = None
_seedance_config: Optional[SeedanceConfig] = None


def get_seedance_client() -> SeedanceApiClient:
    global _seedance_client, _seedance_config
    config = SeedanceConfig.get_config()
    if not config:
        raise HTTPException(status_code=400, detail="Seedance 服务未配置")
    if not config.enabled:
        raise HTTPException(status_code=400, detail="Seedance 服务未启用")
    if (
        (_seedance_client is None)
        or (_seedance_config is None)
        or (_seedance_config.updated_at != config.updated_at)
    ):
        _seedance_client = SeedanceApiClient(config)
        _seedance_config = config
    return _seedance_client


# ======================== 配置管理 ========================


@router.get("/config", response_model=dict)
async def get_seedance_config(user=Depends(get_admin_user)):
    config = SeedanceConfig.get_config()
    if not config:
        return SeedanceConfig().to_dict()
    return config.to_dict()


@router.post("/config")
async def save_seedance_config(
    config_form: SeedanceConfigForm, user=Depends(get_admin_user)
):
    config = SeedanceConfig.save_config(config_form.model_dump())
    # 重置缓存客户端
    global _seedance_client, _seedance_config
    _seedance_client = None
    _seedance_config = config
    return {"success": True, "message": "配置保存成功"}


@router.get("/test")
async def test_seedance_connection(user=Depends(get_admin_user)):
    config = SeedanceConfig.get_config()
    if not config or not config.enabled:
        raise HTTPException(status_code=400, detail="Seedance 服务未启用或未配置")
    client = SeedanceApiClient(config)
    # 简单调用任务列表接口验证连通性
    result = await client.query_task("invalid-test-task")
    if result and result.get("status") == "FAILURE":
        return {"status": "success", "message": "连接成功"}
    return {"status": "success", "message": "接口可访问"}


@router.get("/config/user", response_model=dict)
async def get_seedance_user_config(user=Depends(get_verified_user)):
    config = SeedanceConfig.get_config()
    if not config:
        config = SeedanceConfig()
    return {
        "enabled": config.enabled,
        "default_model": config.default_model,
        "default_duration": config.default_duration,
        "default_resolution": config.default_resolution,
        "default_ratio": config.default_ratio,
        "default_watermark": config.default_watermark,
        "default_camera_fixed": config.default_camera_fixed,
        "default_return_last_frame": config.default_return_last_frame,
        "credits_per_5s": config.credits_per_5s,
        "credits_per_10s": config.credits_per_10s,
        "query_interval": config.query_interval,
    }


# ======================== 任务提交 ========================


async def _submit_seedance_task(
    *,
    user,
    request: SeedanceGenerateRequestModel,
    action: str,
    background_tasks: BackgroundTasks,
):
    config = SeedanceConfig.get_config()
    if not config or not config.enabled:
        raise HTTPException(status_code=400, detail="Seedance 服务未启用")

    mode = (request.mode or "").strip().lower()
    mode_to_action = {
        "text_to_video": "TEXT_TO_VIDEO",
        "image_to_video": "IMAGE_TO_VIDEO",
        "image_to_video_first_last": "IMAGE_TO_VIDEO_FIRST_LAST",
    }
    if not mode:
        raise HTTPException(status_code=400, detail="请选择生成模式")
    if mode not in mode_to_action:
        raise HTTPException(status_code=400, detail="不支持的生成模式")

    resolved_action = mode_to_action[mode]

    if action == "TEXT_TO_VIDEO" and resolved_action != "TEXT_TO_VIDEO":
        raise HTTPException(status_code=400, detail="文生视频请求的模式无效")
    if action == "IMAGE_TO_VIDEO" and resolved_action == "TEXT_TO_VIDEO":
        raise HTTPException(status_code=400, detail="图生视频请求的模式无效")

    prompt = (request.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="请输入提示词")

    credits_cost = config.get_credits_cost(request.duration or config.default_duration)
    if not validate_user_credits(user.id, credits_cost):
        raise HTTPException(status_code=400, detail="积分不足")

    client = get_seedance_client()
    requested_model = request.model or config.default_model
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "model": requested_model,
    }

    if request.duration:
        try:
            payload["duration"] = int(request.duration)
        except ValueError:
            payload["duration"] = int(config.default_duration or "5")
    else:
        payload["duration"] = int(config.default_duration or "5")

    if request.resolution or config.default_resolution:
        payload["resolution"] = request.resolution or config.default_resolution
    if request.ratio or config.default_ratio:
        payload["ratio"] = request.ratio or config.default_ratio
    if request.watermark is not None:
        payload["watermark"] = bool(request.watermark)
    else:
        payload["watermark"] = bool(config.default_watermark)
    if request.seed is not None:
        payload["seed"] = int(request.seed)
    if request.camera_fixed is not None:
        payload["camerafixed"] = bool(request.camera_fixed)
    else:
        payload["camerafixed"] = bool(config.default_camera_fixed)
    if request.return_last_frame is not None:
        payload["return_last_frame"] = bool(request.return_last_frame)
    else:
        payload["return_last_frame"] = bool(config.default_return_last_frame)

    images: List[str] = request.images or []
    if resolved_action != "TEXT_TO_VIDEO":
        if not images:
            raise HTTPException(status_code=400, detail="图生视频需要提供图片")
        if resolved_action == "IMAGE_TO_VIDEO_FIRST_LAST" and len(images) < 2:
            raise HTTPException(
                status_code=400, detail="首尾帧模式需要提供首帧和尾帧图片"
            )
        payload["images"] = await client.prepare_image_urls(user.id, images)

    model_overridden = False
    if (
        resolved_action == "IMAGE_TO_VIDEO_FIRST_LAST"
        and payload["model"] != SEEDANCE_LITE_IMAGE_MODEL
    ):
        payload["model"] = SEEDANCE_LITE_IMAGE_MODEL
        model_overridden = True

    task_request_snapshot = json.loads(json.dumps(payload))
    task_properties: Dict[str, Any] = {
        "serviceType": "seedance",
        "action": resolved_action,
    }
    if model_overridden:
        task_properties["model_override"] = {
            "from": requested_model,
            "to": SEEDANCE_LITE_IMAGE_MODEL,
        }

    # 记录任务
    task = SeedanceTask.create_task(
        user_id=user.id,
        action=resolved_action,
        prompt=prompt,
        model=payload["model"],
        duration=str(payload.get("duration")),
        resolution=payload.get("resolution"),
        ratio=payload.get("ratio"),
        watermark=payload.get("watermark"),
        seed=payload.get("seed"),
        camera_fixed=bool(payload.get("camerafixed")),
        return_last_frame=bool(payload.get("return_last_frame")),
        images=payload.get("images"),
        credits_cost=credits_cost,
        request_data=task_request_snapshot,
        properties=task_properties,
    )

    try:
        deduct_user_credits(user.id, credits_cost, resolved_action, task.id)
        api_result = await client.submit_video_generation(payload)
        if not api_result.get("success"):
            raise HTTPException(
                status_code=400, detail=api_result.get("message", "提交失败")
            )

        task.external_task_id = api_result.get("task_id")
        task.response_data = json.dumps(api_result, ensure_ascii=False)
        task.status = "processing"
        task.updated_at = datetime.utcnow()
        with get_db() as db:
            db_task = db.query(SeedanceTask).filter(SeedanceTask.id == task.id).first()
            if db_task:
                db_task.external_task_id = task.external_task_id
                db_task.status = task.status
                db_task.response_data = task.response_data
                db_task.updated_at = task.updated_at
                db.commit()

        background_tasks.add_task(poll_seedance_task_status, task.id, user.id)
        return {"success": True, "task_id": task.id, "message": "任务提交成功"}
    except HTTPException:
        add_user_credits(user.id, credits_cost, "任务提交失败退款", task.id)
        raise
    except Exception as exc:  # noqa: BLE001
        add_user_credits(user.id, credits_cost, "任务提交失败退款", task.id)
        raise HTTPException(status_code=500, detail=f"提交任务失败: {exc}")


@router.post("/submit/text-to-video")
async def submit_seedance_text_to_video(
    request: SeedanceGenerateRequestModel,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    return await _submit_seedance_task(
        user=user,
        request=request,
        action="TEXT_TO_VIDEO",
        background_tasks=background_tasks,
    )


@router.post("/submit/image-to-video")
async def submit_seedance_image_to_video(
    request: SeedanceGenerateRequestModel,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    return await _submit_seedance_task(
        user=user,
        request=request,
        action="IMAGE_TO_VIDEO",
        background_tasks=background_tasks,
    )


# ======================== 任务查询 ========================


@router.get("/task/{task_id}")
async def get_seedance_task(
    task_id: str, user=Depends(get_verified_user)
) -> Dict[str, Any]:
    task = SeedanceTask.get_task_by_id(task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in ("succeed", "failed") and task.external_task_id:
        client = get_seedance_client()
        remote_status = await client.query_task(task.external_task_id)
        if remote_status:
            task.update_from_api_response(remote_status)

    return task.to_dict()


@router.get("/history")
async def get_seedance_history(
    page: int = 1, limit: int = 20, user=Depends(get_verified_user)
) -> Dict[str, Any]:
    tasks, total = SeedanceTask.get_user_tasks(user.id, page, limit)
    return {
        "data": [task.to_dict() for task in tasks],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.delete("/task/{task_id}")
async def delete_seedance_task(task_id: str, user=Depends(get_verified_user)):
    task = SeedanceTask.get_task_by_id(task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="任务不存在")

    with get_db() as db:
        db.query(SeedanceTask).filter(SeedanceTask.id == task_id).delete()
        db.commit()
    return {"success": True, "message": "任务已删除"}


@router.get("/credits")
async def get_seedance_credits(
    user=Depends(get_verified_user),
) -> SeedanceCreditsResponse:
    return SeedanceCreditsResponse(balance=get_user_credit_balance(user.id))


# ======================== 后台轮询 ========================


async def poll_seedance_task_status(task_id: str, user_id: str):
    max_attempts = 60
    interval = 10

    for _ in range(max_attempts):
        await asyncio.sleep(interval)
        task = SeedanceTask.get_task_by_id(task_id)
        if not task:
            break

        if task.status in ("succeed", "failed"):
            break

        if not task.external_task_id:
            continue

        try:
            client = get_seedance_client()
            remote_status = await client.query_task(task.external_task_id)
            if remote_status:
                task.update_from_api_response(remote_status)

                if task.status == "succeed" and task.video_url:
                    await _persist_seedance_outputs(task, user_id)
                    break

                if task.status == "failed":
                    break
        except Exception as exc:  # noqa: BLE001
            logger = get_seedance_logger()
            logger.warning("轮询 Seedance 任务失败: %s", exc)


async def _persist_seedance_outputs(task: SeedanceTask, user_id: str):
    file_manager = get_file_manager()

    if task.video_url and not task.cloud_video_url:
        success, message, file_record = await file_manager.save_generated_content(
            user_id=user_id,
            file_url=task.video_url,
            filename=f"seedance_{task.id}.mp4",
            file_type="video",
            source_type="seedance",
            source_task_id=task.id,
            metadata={
                "prompt": task.prompt,
                "model": task.model,
                "duration": task.duration,
                "resolution": task.resolution,
                "ratio": task.ratio,
                "original_url": task.video_url,
            },
        )
        if success and file_record and file_record.cloud_url:
            presigned = file_manager.get_presigned_download_url(
                file_record.cloud_url, expires_in=3600
            )
            with get_db() as db:
                db_task = (
                    db.query(SeedanceTask).filter(SeedanceTask.id == task.id).first()
                )
                if db_task:
                    db_task.cloud_video_url = presigned or file_record.cloud_url
                    db_task.video_url = task.video_url
                    db_task.updated_at = datetime.utcnow()
                    db.commit()
                    task.cloud_video_url = db_task.cloud_video_url

    if task.last_frame_url and not task.cloud_last_frame_url:
        success, message, file_record = await file_manager.save_generated_content(
            user_id=user_id,
            file_url=task.last_frame_url,
            filename=f"seedance_last_frame_{task.id}.png",
            file_type="image",
            source_type="seedance",
            source_task_id=task.id,
            metadata={"original_url": task.last_frame_url},
        )
        if success and file_record and file_record.cloud_url:
            presigned = file_manager.get_presigned_download_url(
                file_record.cloud_url, expires_in=3600
            )
            with get_db() as db:
                db_task = (
                    db.query(SeedanceTask).filter(SeedanceTask.id == task.id).first()
                )
                if db_task:
                    db_task.cloud_last_frame_url = presigned or file_record.cloud_url
                    db_task.last_frame_url = task.last_frame_url
                    db_task.updated_at = datetime.utcnow()
                    db.commit()
                    task.cloud_last_frame_url = db_task.cloud_last_frame_url


def get_seedance_logger():
    import logging

    return logging.getLogger("seedance")
