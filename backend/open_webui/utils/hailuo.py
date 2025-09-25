"""
海螺（MiniMax Hailuo）视频生成工具
API客户端、任务处理、云存储迁移
"""

import asyncio
import base64
import binascii
import imghdr
import json
import logging
from datetime import datetime
from mimetypes import guess_extension
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx

from open_webui.models.hailuo import HailuoConfig, HailuoTask, HailuoGenerateRequest
from open_webui.models.credits import Credits
from open_webui.services.file_manager import get_file_manager


logger = logging.getLogger(__name__)


class HailuoApiClient:
    def __init__(self, config: HailuoConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        self.timeout = httpx.Timeout(60.0)

    async def create_task(self, req: HailuoGenerateRequest) -> Dict[str, Any]:
        url = f"{self.base_url}/minimax/v1/video_generation"
        payload = {
            "model": req.model or self.config.default_model,
            "prompt": req.prompt.strip(),
        }
        if req.duration:
            payload["duration"] = int(req.duration)
        if req.resolution:
            payload["resolution"] = req.resolution
        if req.prompt_optimizer is not None:
            payload["prompt_optimizer"] = bool(req.prompt_optimizer)
        # first/last frame
        if req.first_frame_image:
            payload["first_frame_image"] = req.first_frame_image
        if req.last_frame_image:
            payload["last_frame_image"] = req.last_frame_image

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, headers=self.headers, json=payload)
        except httpx.HTTPError as exc:
            logger.exception("Hailuo create_task network error: %s", exc)
            return {"success": False, "error": f"网络请求失败: {exc}"}

        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
            }

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            logger.warning("Hailuo create_task JSON decode error: %s", exc)
            return {"success": False, "error": "服务返回格式异常"}

        if data.get("base_resp", {}).get("status_code") == 0:
            return {"success": True, "task_id": data.get("task_id"), "raw": data}

        error_msg = (
            data.get("base_resp", {}).get("status_msg")
            or data.get("message")
            or data.get("error")
            or "create failed"
        )
        return {
            "success": False,
            "error": error_msg,
            "raw": data,
        }

    async def query_task(self, task_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/minimax/v1/query/video_generation?task_id={task_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self.headers)
        except httpx.HTTPError as exc:
            logger.exception("Hailuo query_task network error: %s", exc)
            return {"success": False, "error": f"网络请求失败: {exc}"}

        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
            }

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            logger.warning("Hailuo query_task JSON decode error: %s", exc)
            return {"success": False, "error": "服务返回格式异常"}

        ok = data.get("base_resp", {}).get("status_code") == 0
        return {"success": ok, **data}

    async def retrieve_file(self, file_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/minimax/v1/files/retrieve?file_id={file_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self.headers)
        except httpx.HTTPError as exc:
            logger.exception("Hailuo retrieve_file network error: %s", exc)
            return {"success": False, "error": f"网络请求失败: {exc}"}

        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
            }

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            logger.warning("Hailuo retrieve_file JSON decode error: %s", exc)
            return {"success": False, "error": "服务返回格式异常"}

        ok = data.get("base_resp", {}).get("status_code") == 0
        return {"success": ok, **data}


def _status_map(remote: str) -> str:
    r = (remote or "").lower()
    if r in ("success", "succeed", "completed", "complete"):
        return "succeed"
    if r in ("failure", "failed", "error"):
        return "failed"
    return "processing"


def _decode_base64_payload(data: str) -> bytes:
    cleaned = data.strip()
    if not cleaned:
        raise ValueError("图片数据为空")

    padding = len(cleaned) % 4
    if padding:
        cleaned += "=" * (4 - padding)

    try:
        return base64.b64decode(cleaned, validate=True)
    except binascii.Error as exc:
        raise ValueError(f"图片数据不是有效的Base64编码: {exc}") from exc


async def _prepare_image_reference(
    user_id: str, raw_value: Optional[str], label: str
) -> Optional[str]:
    if not raw_value:
        return None

    value = raw_value.strip()
    if not value:
        return None

    if value.startswith("http://") or value.startswith("https://"):
        return value

    base64_payload = value
    mime_hint = None
    if value.startswith("data:"):
        parts = value.split(",", 1)
        if len(parts) < 2 or not parts[1].strip():
            raise ValueError("图片数据为空")
        header = parts[0]
        base64_payload = parts[1]
        if ";" in header:
            mime_hint = header.split(";", 1)[0].removeprefix("data:")
        else:
            mime_hint = header.removeprefix("data:")

    image_bytes = _decode_base64_payload(base64_payload)

    extension = None
    if mime_hint:
        extension = guess_extension(mime_hint) or None

    detected_format = imghdr.what(None, h=image_bytes)
    if detected_format:
        detected_ext = (
            f".{detected_format}"
            if not detected_format.startswith(".")
            else detected_format
        )
        extension = extension or detected_ext

    if not extension:
        extension = ".png"

    file_manager = get_file_manager()
    filename = f"hailuo_input_{label}_{uuid4().hex}{extension}"

    upload_success, message, record = await file_manager.save_generated_content(
        user_id=user_id,
        file_data=image_bytes,
        filename=filename,
        file_type="image",
        source_type="hailuo_input",
        source_task_id=None,
        metadata={
            "kind": "hailuo_input",
            "label": label,
        },
    )

    if not upload_success or not record or not record.cloud_url:
        detail = message or "图片上传失败"
        raise ValueError(detail)

    return record.cloud_url


def _deduct_credits(user_id: str, amount: int, desc: str) -> bool:
    try:
        credits = Credits.get_user_credits(user_id)
        if not credits:
            return False
        new_val = int(credits.credit) - amount
        return Credits.update_user_credits(user_id, new_val)
    except Exception:
        return False


def _refund_credits(user_id: str, amount: int, desc: str) -> bool:
    try:
        credits = Credits.get_user_credits(user_id)
        if not credits:
            return False
        new_val = int(credits.credit) + amount
        return Credits.update_user_credits(user_id, new_val)
    except Exception:
        return False


async def process_hailuo_generation(
    user_id: str, req: HailuoGenerateRequest
) -> HailuoTask:
    cfg = HailuoConfig.get_config()
    if not cfg or not cfg.enabled:
        raise Exception("海螺服务未启用")

    model = req.model or cfg.default_model
    duration = int(req.duration or cfg.default_duration)
    resolution = req.resolution or cfg.default_resolution

    try:
        cloud_first = await _prepare_image_reference(
            user_id, req.first_frame_image, "first"
        )
        cloud_last = await _prepare_image_reference(
            user_id, req.last_frame_image, "last"
        )
    except ValueError as exc:
        raise Exception(str(exc)) from exc

    is_first_last = bool(cloud_first and cloud_last)
    cost = cfg.get_credits_cost(model, resolution, duration, first_last=is_first_last)

    if not _deduct_credits(user_id, cost, f"hailuo-{model}"):
        raise Exception("积分不足或扣费失败")

    task = HailuoTask.create_task(
        {
            "user_id": user_id,
            "prompt": req.prompt,
            "model": model,
            "duration": duration,
            "resolution": resolution,
            "prompt_optimizer": bool(
                req.prompt_optimizer
                if req.prompt_optimizer is not None
                else cfg.prompt_optimizer
            ),
            "first_frame_url": cloud_first,
            "last_frame_url": cloud_last,
            "credits_cost": cost,
            "status": "submitted",
            "properties": {"serviceType": "hailuo"},
            "cloud_input_images": [url for url in [cloud_first, cloud_last] if url],
        }
    )

    client = HailuoApiClient(cfg)
    try:
        payload_dict = req.model_dump()
        payload_dict["first_frame_image"] = cloud_first
        payload_dict["last_frame_image"] = cloud_last
        sanitized_request = HailuoGenerateRequest(**payload_dict)

        created = await client.create_task(sanitized_request)
        if not created.get("success"):
            _refund_credits(user_id, cost, "hailuo-create-failed")
            HailuoTask.update_task_status(
                task.id, {"status": "failed", "fail_reason": created.get("error")}
            )
            raise Exception(created.get("error") or "创建任务失败")

        HailuoTask.update_task_status(
            task.id,
            {
                "status": "processing",
                "external_task_id": created.get("task_id"),
                "progress": "5%",
            },
        )
        return HailuoTask.get_task_by_id(task.id)

    except Exception as e:
        _refund_credits(user_id, cost, "hailuo-exception")
        HailuoTask.update_task_status(
            task.id, {"status": "failed", "fail_reason": str(e)}
        )
        raise


async def monitor_hailuo_task(task_id: str, cfg: HailuoConfig):
    client = HailuoApiClient(cfg)
    max_attempts = max(
        1, int((cfg.task_timeout_ms or 900000) / (cfg.query_interval_ms or 10000))
    )
    attempt = 0
    while attempt < max_attempts:
        await asyncio.sleep((cfg.query_interval_ms or 10000) / 1000)
        t = HailuoTask.get_task_by_id(task_id)
        if not t or not t.external_task_id:
            break
        res = await client.query_task(t.external_task_id)
        if not res.get("success"):
            HailuoTask.update_task_status(
                task_id, {"status": "failed", "fail_reason": res.get("error")}
            )
            # refund
            if t:
                _refund_credits(t.user_id, t.credits_cost or 0, "hailuo-query-failed")
            break

        status = _status_map(res.get("status"))
        updates = {"status": status, "progress": res.get("progress") or t.progress}

        if status == "succeed":
            file_id = str(res.get("file_id") or "")
            updates["file_id"] = file_id
            # fetch download url
            file_res = await client.retrieve_file(file_id)
            if file_res.get("success"):
                file = file_res.get("file", {})
                video_url = file.get("download_url") or file.get("backup_download_url")
                updates["result_video_url"] = video_url
                # upload to cloud
                if video_url:
                    fm = get_file_manager()
                    ok, msg, rec = await fm.save_generated_content(
                        user_id=t.user_id,
                        file_url=video_url,
                        filename=f"hailuo_{task_id}.mp4",
                        file_type="video",
                        source_type="hailuo",
                        source_task_id=task_id,
                        metadata={
                            "model": t.model,
                            "duration": t.duration,
                            "resolution": t.resolution,
                            "original_url": video_url,
                        },
                    )
                    if ok and rec and rec.cloud_url:
                        updates["cloud_video_url"] = rec.cloud_url
                        updates["progress"] = "100%"
            HailuoTask.update_task_status(task_id, updates)
            break
        elif status == "failed":
            updates["fail_reason"] = (
                res.get("base_resp", {}).get("status_msg") or "生成失败"
            )
            HailuoTask.update_task_status(task_id, updates)
            # refund
            if t:
                _refund_credits(t.user_id, t.credits_cost or 0, "hailuo-failed")
            break
        else:
            HailuoTask.update_task_status(task_id, updates)
            attempt += 1

    if attempt >= max_attempts:
        HailuoTask.update_task_status(
            task_id, {"status": "timeout", "fail_reason": "任务监控超时"}
        )
        t = HailuoTask.get_task_by_id(task_id)
        if t and t.credits_cost:
            _refund_credits(t.user_id, t.credits_cost, "hailuo-timeout")
