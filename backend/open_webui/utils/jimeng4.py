"""Utilities for Jimeng4 image generation"""

from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from open_webui.models.jimeng4 import (
    Jimeng4Config,
    Jimeng4ConfigForm,
    Jimeng4GenerateRequest,
    Jimeng4Task,
)
from open_webui.services.file_manager import get_file_manager


def deduct_user_credits(
    user_id: str, amount: int, reason: str, task_id: Optional[str] = None
) -> float:
    """Deduct credits from user using shared credit table."""
    from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail

    try:
        form = AddCreditForm(
            user_id=user_id,
            amount=Decimal(-amount),
            detail=SetCreditFormDetail(
                desc=f"Jimeng4: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "jimeng4", "credits": amount},
            ),
        )
        result = Credits.add_credit_by_user_id(form)
        return float(result.credit) if result else 0.0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to deduct Jimeng4 credits: %s", exc)
        return 0.0


def refund_user_credits(
    user_id: str, amount: int, reason: str, task_id: Optional[str] = None
) -> float:
    """Refund credits to user when task fails."""
    from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail

    try:
        form = AddCreditForm(
            user_id=user_id,
            amount=Decimal(amount),
            detail=SetCreditFormDetail(
                desc=f"Jimeng4 Refund: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "jimeng4", "credits": amount},
            ),
        )
        result = Credits.add_credit_by_user_id(form)
        return float(result.credit) if result else 0.0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to refund Jimeng4 credits: %s", exc)
        return 0.0


logger = logging.getLogger(__name__)


class Jimeng4ApiError(Exception):
    """Raised when Jimeng4 API returns an error."""


class Jimeng4ApiClient:
    """Simple HTTP client for Jimeng4 image generation API."""

    def __init__(self, config: Jimeng4Config):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_images(self, payload: Jimeng4GenerateRequest) -> Dict[str, Any]:
        """Submit generation request and return JSON response."""
        url = f"{self.base_url}/v1/images/generations"
        request_body: Dict[str, Any] = {
            "model": payload.model or self.config.default_model,
            "prompt": payload.prompt,
            "n": payload.n or self.config.default_n,
            "response_format": payload.response_format or "url",
            "size": payload.size or self.config.default_size,
            "watermark": (
                self.config.default_watermark
                if payload.watermark is None
                else payload.watermark
            ),
        }

        if payload.image:
            request_body["image"] = payload.image
        if payload.sequential_image_generation or self.config.default_sequential_mode:
            request_body["sequential_image_generation"] = (
                payload.sequential_image_generation
                or self.config.default_sequential_mode
            )
        if payload.stream:
            request_body["stream"] = True

        logger.info(
            "Jimeng4 request -> model=%s, n=%s, seq=%s, stream=%s, refs=%s",
            request_body.get("model"),
            request_body.get("n"),
            request_body.get("sequential_image_generation"),
            request_body.get("stream"),
            len(request_body.get("image") or []),
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            if payload.stream:
                async with client.stream(
                    "POST", url, json=request_body, headers=self.headers
                ) as response:
                    if response.status_code >= 400:
                        detail = await _safe_parse_error(response)
                        logger.error(
                            "Jimeng4 API stream error %s: %s",
                            response.status_code,
                            detail,
                        )
                        raise Jimeng4ApiError(str(detail))

                    content_type = response.headers.get("content-type", "")
                    if "text/event-stream" in content_type.lower():
                        events, raw_stream = await _collect_sse_events(response)
                        merged = _merge_stream_events(events)
                        if merged is None:
                            merged = {}
                        merged.setdefault("stream_events", events)
                        merged.setdefault("raw_stream", raw_stream)
                        logger.debug("Jimeng4 streaming merged response: %s", merged)
                        return merged

                    # Fallback: treat as normal response
                    body_bytes = await response.aread()
                    try:
                        data = json.loads(body_bytes)
                        logger.info(
                            "Jimeng4 streaming fallback returned %s images",
                            len(data.get("data") or []),
                        )
                        return data
                    except (ValueError, TypeError) as exc:  # noqa: BLE001
                        logger.error("Jimeng4 stream response parse error: %s", exc)
                        raise Jimeng4ApiError("Invalid stream response") from exc
            else:
                response = await client.post(
                    url, json=request_body, headers=self.headers
                )

        if response.status_code >= 400:
            detail = await _safe_parse_error(response)
            logger.error("Jimeng4 API error %s: %s", response.status_code, detail)
            raise Jimeng4ApiError(str(detail))

        data = response.json()
        logger.info("Jimeng4 response returned %s images", len(data.get("data") or []))
        return data


async def _safe_parse_error(response: httpx.Response) -> Any:
    try:
        return await response.json()
    except Exception:  # noqa: BLE001
        try:
            data = await response.aread()
            if isinstance(data, bytes):
                try:
                    return data.decode("utf-8")
                except UnicodeDecodeError:
                    return data.decode("utf-8", errors="ignore")
            return data
        except Exception:  # noqa: BLE001
            return response.text


async def _collect_sse_events(
    response: httpx.Response,
) -> tuple[List[Any], List[str]]:
    events: List[Any] = []
    raw_lines: List[str] = []

    async for line in response.aiter_lines():
        if line is None:
            continue
        raw_lines.append(line)

        stripped = line.strip()
        if not stripped or stripped.startswith(":"):
            continue

        if stripped.startswith("data:"):
            payload = stripped[5:].strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                events.append(json.loads(payload))
            except json.JSONDecodeError:
                logger.debug("Unable to decode Jimeng4 SSE payload: %s", payload)

    return events, raw_lines


def _merge_stream_events(events: List[Any]) -> Optional[Dict[str, Any]]:
    if not events:
        return None

    result: Dict[str, Any] = {}
    final_payload: Optional[Dict[str, Any]] = None
    data_list: List[Any] = []

    for event in events:
        if not isinstance(event, dict):
            continue

        for key in ("result", "output"):
            payload = event.get(key)
            if isinstance(payload, dict):
                final_payload = payload

        if "data" in event:
            data_value = event["data"]
            if isinstance(data_value, dict):
                final_payload = data_value
            elif isinstance(data_value, list):
                data_list = data_value

        if "usage" in event and isinstance(event["usage"], dict):
            result["usage"] = event["usage"]

        if "created" in event and "created" not in result:
            result["created"] = event["created"]

        # 有些事件直接携带完整响应
        if not final_payload and all(key in event for key in ("data", "usage")):
            final_payload = event

    if final_payload is None:
        last_event = events[-1]
        if isinstance(last_event, dict):
            final_payload = last_event

    if final_payload:
        result.update(final_payload)

    if data_list and "data" not in result:
        result["data"] = data_list

    return result


async def persist_generated_images(
    task: Jimeng4Task,
    api_response: Dict[str, Any],
) -> Dict[str, Any]:
    """Download generated images and store them via GeneratedFileManager."""
    images = api_response.get("data") or []
    if not images:
        logger.warning("Jimeng4 response lacks data field: %s", api_response)
        return {"response_urls": [], "cloud_urls": []}

    file_manager = get_file_manager()
    stored_urls: List[str] = []
    response_urls: List[str] = []

    async def _download_and_store(idx: int, url: str) -> None:
        response_urls.append(url)
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "image/jpeg")
                success, message, record = await file_manager.save_generated_content(
                    user_id=task.user_id,
                    file_data=resp.content,
                    filename=f"jimeng4_{task.id}_{idx}.jpg",
                    file_type="image",
                    source_type="jimeng4",
                    source_task_id=task.id,
                    metadata={
                        "source_url": url,
                        "content_type": content_type,
                        "provider": "jimeng4",
                    },
                )
                if success and record:
                    stored_urls.append(record.cloud_url or record.local_path)
                else:
                    logger.warning(
                        "Jimeng4 image store failed (%s): %s", task.id, message
                    )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Downloading Jimeng4 image failed: %s", exc)

    await asyncio.gather(
        *[
            _download_and_store(idx, item.get("url"))
            for idx, item in enumerate(images)
            if item.get("url")
        ]
    )

    logger.info("Jimeng4 stored %s/%s images", len(stored_urls), len(images))

    return {"response_urls": response_urls, "cloud_urls": stored_urls}


def build_user_config_dict(config: Any) -> Dict[str, Any]:
    return {
        "enabled": getattr(config, "enabled", False),
        "default_model": getattr(config, "default_model", "doubao-seedream-4-0-250828"),
        "default_size": getattr(config, "default_size", "2K"),
        "default_watermark": getattr(config, "default_watermark", True),
        "default_sequential_mode": getattr(config, "default_sequential_mode", "auto"),
        "default_n": getattr(config, "default_n", 1),
        "credits_per_image": getattr(config, "credits_per_image", 30),
        "max_concurrent_tasks": getattr(config, "max_concurrent_tasks", 5),
        "task_timeout": getattr(config, "task_timeout", 300000),
    }


def sanitize_config_form(data: Dict[str, Any]) -> Dict[str, Any]:
    form = Jimeng4ConfigForm(**data)
    return form.model_dump()
