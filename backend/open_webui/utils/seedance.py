"""Seedance (新即梦) 视频生成 API 客户端"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from open_webui.models.seedance import SeedanceConfig
from open_webui.services.file_manager import get_file_manager
from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
from decimal import Decimal


logger = logging.getLogger(__name__)


class SeedanceApiClient:
    """封装 Seedance 视频生成 API"""

    def __init__(self, config: SeedanceConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json",
        }

    def _get_endpoint(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    async def submit_video_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self._get_endpoint("v2/videos/generations")
        logger.info(
            "🎬 【Seedance】提交任务: %s", json.dumps(payload, ensure_ascii=False)
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            logger.info("🎬 【Seedance】提交成功: %s", result)
            return {"success": True, **result}

        try:
            error_json = response.json()
        except json.JSONDecodeError:
            error_json = {"status": response.status_code, "message": response.text}

        message = error_json.get("message") or response.text
        logger.error(
            "🎬 【Seedance】提交失败: HTTP %s %s", response.status_code, message
        )
        return {"success": False, "message": message, "status": response.status_code}

    async def query_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        url = self._get_endpoint(f"v2/videos/generations/{task_id}")
        logger.info("🎬 【Seedance】查询任务: %s", task_id)
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            logger.info("🎬 【Seedance】查询成功: %s", result)
            return result

        if response.status_code == 404:
            logger.warning("🎬 【Seedance】任务不存在: %s", task_id)
            return {
                "status": "FAILURE",
                "fail_reason": "任务不存在",
                "task_id": task_id,
            }

        logger.error(
            "🎬 【Seedance】查询任务失败: HTTP %s %s",
            response.status_code,
            response.text,
        )
        return None

    async def prepare_image_urls(self, user_id: str, images: List[str]) -> List[str]:
        """将前端上传的图片转换成 Seedance 可访问的 URL"""
        file_manager = get_file_manager()
        result: List[str] = []

        for index, image in enumerate(images):
            image = image.strip()
            if not image:
                continue

            # 如果已经是URL，则尝试生成预签名链接
            if image.startswith("http://") or image.startswith("https://"):
                presigned = file_manager.get_presigned_download_url(
                    image, expires_in=3600
                )
                result.append(presigned or image)
                continue

            if image.startswith("data:"):
                _, base64_data = image.split(",", 1)
            else:
                base64_data = image

            try:
                image_bytes = base64.b64decode(base64_data)
            except Exception as exc:  # noqa: BLE001
                logger.error("🎬 【Seedance】解析图片失败: %s", exc)
                continue

            filename = f"seedance_input_{user_id}_{index}.png"
            success, message, file_record = await file_manager.save_generated_content(
                user_id=user_id,
                file_data=image_bytes,
                filename=filename,
                file_type="image",
                source_type="seedance",
                metadata={
                    "description": "seedance_input_image",
                    "original_filename": filename,
                    "index": index,
                },
            )

            if not success or not file_record or not file_record.cloud_url:
                logger.error("🎬 【Seedance】上传图片到云存储失败: %s", message)
                continue

            accessible_url = file_manager.get_presigned_download_url(
                file_record.cloud_url, expires_in=3600
            )
            result.append(accessible_url or file_record.cloud_url)

        return result


async def build_seedance_payload(
    config: SeedanceConfig,
    user_id: str,
    request_data: Dict[str, Any],
) -> Dict[str, Any]:
    """根据请求构建 Seedance API payload，并处理图片上传"""

    payload: Dict[str, Any] = {
        "prompt": request_data.get("prompt"),
        "model": request_data.get("model") or config.default_model,
    }

    if request_data.get("duration"):
        try:
            payload["duration"] = int(request_data["duration"])
        except (TypeError, ValueError):
            payload["duration"] = int(config.default_duration or "5")
    else:
        payload["duration"] = int(config.default_duration or "5")

    if request_data.get("resolution"):
        payload["resolution"] = request_data["resolution"]
    elif config.default_resolution:
        payload["resolution"] = config.default_resolution

    if request_data.get("ratio"):
        payload["ratio"] = request_data["ratio"]
    elif config.default_ratio:
        payload["ratio"] = config.default_ratio

    if request_data.get("watermark") is not None:
        payload["watermark"] = bool(request_data["watermark"])
    else:
        payload["watermark"] = bool(config.default_watermark)

    if request_data.get("seed") is not None:
        payload["seed"] = int(request_data["seed"])

    if request_data.get("camera_fixed") is not None:
        payload["camerafixed"] = bool(request_data["camera_fixed"])
    else:
        payload["camerafixed"] = bool(config.default_camera_fixed)

    if request_data.get("return_last_frame") is not None:
        payload["return_last_frame"] = bool(request_data["return_last_frame"])
    else:
        payload["return_last_frame"] = bool(config.default_return_last_frame)

    images = request_data.get("images") or []
    if images:
        client = SeedanceApiClient(config)
        payload["images"] = await client.prepare_image_urls(user_id, images)

    return payload


def get_user_credit_balance(user_id: str) -> float:
    credit_model = Credits.get_credit_by_user_id(user_id)
    return float(credit_model.credit) if credit_model else 0.0


def validate_user_credits(user_id: str, required_credits: int) -> bool:
    return get_user_credit_balance(user_id) >= required_credits


def deduct_user_credits(
    user_id: str, amount: int, reason: str, task_id: Optional[str] = None
) -> float:
    try:
        form_data = AddCreditForm(
            user_id=user_id,
            amount=Decimal(-amount),
            detail=SetCreditFormDetail(
                desc=f"Seedance视频生成: {reason}",
                usage={"service": "seedance", "credits": amount},
                api_params={"task_id": task_id} if task_id else {},
            ),
        )
        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as exc:  # pragma: no cover - 防御性
        logger.error("扣除 Seedance 积分失败: %s", exc)
        return 0.0


def add_user_credits(
    user_id: str, amount: int, reason: str, task_id: Optional[str] = None
) -> float:
    try:
        form_data = AddCreditForm(
            user_id=user_id,
            amount=Decimal(amount),
            detail=SetCreditFormDetail(
                desc=f"Seedance视频生成: {reason}",
                usage={"service": "seedance", "credits": amount},
                api_params={"task_id": task_id} if task_id else {},
            ),
        )
        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as exc:  # pragma: no cover - 防御性
        logger.error("退还 Seedance 积分失败: %s", exc)
        return 0.0
