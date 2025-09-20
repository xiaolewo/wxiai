"""Utilities for Jimeng4 image generation"""

from __future__ import annotations

import asyncio
import json
import logging
import re
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
        requested_n = payload.n or self.config.default_n
        request_body: Dict[str, Any] = {
            "model": payload.model or self.config.default_model,
            "prompt": payload.prompt,
            "n": requested_n,
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
        logger.debug("Jimeng4 raw response: %s", data)
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
    merged_data: List[Any] = []
    last_payload: Optional[Dict[str, Any]] = None

    for event in events:
        if not isinstance(event, dict):
            continue

        data_value = event.get("data")
        if isinstance(data_value, list):
            merged_data.extend(data_value)
        elif isinstance(data_value, dict):
            merged_data.append(data_value)
            last_payload = data_value

        for key in ("result", "output"):
            payload = event.get(key)
            if isinstance(payload, dict):
                last_payload = payload

        if "usage" in event and isinstance(event["usage"], dict):
            result["usage"] = event["usage"]

        if "created" in event and "created" not in result:
            result["created"] = event["created"]

    if last_payload:
        # 将最后一次有效负载中的非 data 字段合并，避免覆盖 merged_data
        for key, value in last_payload.items():
            if key == "data":
                continue
            result.setdefault(key, value)

    if merged_data:
        result["data"] = merged_data

    if result:
        result.setdefault("stream_events", events)

    return result if result else None


def _extract_urls_from_string(value: str) -> List[str]:
    if not value:
        return []
    pattern = re.compile(r"https?://[^\s'\"<>;,|]+", re.IGNORECASE)
    matches = pattern.findall(value)
    if matches:
        return matches
    # fallback split by common delimiters
    parts = re.split(r"[\s;,]+", value)
    return [part for part in parts if part.startswith("http")]


async def persist_generated_images(
    task: Jimeng4Task,
    api_response: Dict[str, Any],
) -> Dict[str, Any]:
    """Download generated images and store them via GeneratedFileManager."""

    def _collect_urls(item: Any) -> List[str]:
        urls: List[str] = []
        if isinstance(item, str):
            urls.extend(_extract_urls_from_string(item))
            return urls
        if isinstance(item, list):
            for sub in item:
                urls.extend(_collect_urls(sub))
            return urls
        if isinstance(item, dict):
            single = item.get("url") or item.get("image_url")
            if isinstance(single, str) and single:
                urls.extend(_extract_urls_from_string(single))
            nested_keys = (
                "urls",
                "images",
                "image_urls",
                "image_list",
                "data",
                "results",
            )
            for key in nested_keys:
                value = item.get(key)
                if value:
                    urls.extend(_collect_urls(value))
        return urls

    primary_data = api_response.get("data")
    candidate_urls = _collect_urls(primary_data)
    if not candidate_urls:
        candidate_urls = _collect_urls(api_response)
    raw_stream = api_response.get("raw") or api_response.get("raw_stream")
    if raw_stream:
        candidate_urls.extend(
            _extract_urls_from_string(
                raw_stream if isinstance(raw_stream, str) else json.dumps(raw_stream)
            )
        )

    unique_urls: List[str] = []
    for url in candidate_urls:
        if url and url not in unique_urls:
            unique_urls.append(url)

    if not unique_urls:
        logger.warning(
            "Jimeng4 response contains no downloadable urls: %s", api_response
        )
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
        *[_download_and_store(idx, url) for idx, url in enumerate(unique_urls) if url]
    )

    logger.info("Jimeng4 stored %s/%s images", len(stored_urls), len(unique_urls))
    expected = getattr(task, "n", None) or 0
    if expected and len(unique_urls) < expected:
        logger.warning(
            "Jimeng4 expected %s images but only saw %s. Raw response keys: %s",
            expected,
            len(unique_urls),
            list(api_response.keys()),
        )
        logger.debug("Jimeng4 shortfall response: %s", api_response)

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
