"""Utilities for Banana image generation"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Iterable, List, Optional

import httpx

from open_webui.models.banana import BananaConfig, BananaConfigForm, BananaTask
from open_webui.services.file_manager import get_file_manager

logger = logging.getLogger(__name__)


class BananaApiError(Exception):
    """Raised when Banana API returns an error."""


class BananaApiClient:
    """HTTP client wrapper for Banana image APIs."""

    def __init__(self, config: BananaConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {config.api_key}" if config.api_key else "",
            "Content-Type": "application/json",
        }

    async def generate_text(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/images/generations"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
        return await _handle_response(response)

    async def generate_edit(
        self, payload: Dict[str, Any], files: Iterable[tuple[str, bytes, str]]
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/images/edits"
        headers = {k: v for k, v in self.headers.items() if k.lower() != "content-type"}

        data = {"model": payload.get("model", "")}
        if prompt := payload.get("prompt"):
            data["prompt"] = prompt
        if response_format := payload.get("response_format"):
            data["response_format"] = response_format

        files_payload = []
        for idx, (filename, content, content_type) in enumerate(files):
            files_payload.append(
                (
                    "image",
                    (
                        filename or f"reference-{idx}.png",
                        content,
                        content_type or "application/octet-stream",
                    ),
                )
            )

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url, headers=headers, data=data, files=files_payload
            )
        return await _handle_response(response)


def _normalize_resolution(value: str) -> str:
    return value.replace("×", "x").replace("\u00d7", "x").replace(" ", "")


async def _handle_response(response: httpx.Response) -> Dict[str, Any]:
    if response.status_code >= 400:
        detail = await _safe_parse_error(response)
        logger.error("Banana API error %s: %s", response.status_code, detail)
        raise BananaApiError(str(detail))

    data = response.json()
    logger.debug("Banana API response: %s", data)
    return data


async def _safe_parse_error(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:  # noqa: BLE001
        try:
            body = await response.aread()
            if isinstance(body, bytes):
                try:
                    return body.decode("utf-8")
                except UnicodeDecodeError:
                    return body.decode("utf-8", errors="ignore")
            return body
        except Exception:  # noqa: BLE001
            return response.text


async def persist_generated_images(
    task: BananaTask, api_response: Dict[str, Any]
) -> Dict[str, Any]:
    data = api_response.get("data") or []
    urls = []
    for item in data:
        if isinstance(item, dict) and item.get("url"):
            urls.append(item["url"])

    file_manager = get_file_manager()
    stored_urls: List[str] = []
    response_urls: List[str] = []

    async def _download(url: str, index: int) -> None:
        response_urls.append(url)
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "image/png")
                success, message, record = await file_manager.save_generated_content(
                    user_id=task.user_id,
                    file_data=resp.content,
                    filename=f"banana_{task.id}_{index}.png",
                    file_type="image",
                    source_type="banana",
                    source_task_id=task.id,
                    metadata={
                        "source_url": url,
                        "content_type": content_type,
                        "provider": "banana",
                    },
                )
                if success and record:
                    stored_urls.append(record.cloud_url or record.local_path)
                else:
                    logger.warning(
                        "Banana image store failed (%s): %s", task.id, message
                    )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Downloading Banana image failed: %s", exc)

    if urls and file_manager:
        await asyncio.gather(*[_download(url, idx) for idx, url in enumerate(urls)])
    else:
        stored_urls = []

    return {"response_urls": response_urls, "cloud_urls": stored_urls}


def normalize_config_form(data: Dict[str, Any]) -> Dict[str, Any]:
    form = BananaConfigForm(**data)
    normalized = form.model_dump()
    normalized["default_aspect_ratio"] = normalized["default_aspect_ratio"].strip()
    return normalized


def deduct_user_credits(
    user_id: str, amount: int, reason: str, task_id: Optional[str] = None
) -> float:
    from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail

    try:
        form = AddCreditForm(
            user_id=user_id,
            amount=-amount,
            detail=SetCreditFormDetail(
                desc=f"Banana: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "banana", "credits": amount},
            ),
        )
        result = Credits.add_credit_by_user_id(form)
        return float(result.credit) if result else 0.0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to deduct Banana credits: %s", exc)
        return 0.0


def refund_user_credits(
    user_id: str, amount: int, reason: str, task_id: Optional[str] = None
) -> float:
    from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail

    try:
        form = AddCreditForm(
            user_id=user_id,
            amount=amount,
            detail=SetCreditFormDetail(
                desc=f"Banana refund: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "banana", "credits": amount},
            ),
        )
        result = Credits.add_credit_by_user_id(form)
        return float(result.credit) if result else 0.0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to refund Banana credits: %s", exc)
        return 0.0
