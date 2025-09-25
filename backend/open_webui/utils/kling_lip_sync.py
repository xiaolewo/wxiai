import aiohttp
import asyncio
import json
import base64
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from open_webui.services.file_manager import get_file_manager

logger = logging.getLogger(__name__)


class KlingLipSyncAPI:
    """可灵对口型API客户端"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        try:
            # 构建测试请求（查询任务列表来测试连接）
            url = f"{self.base_url}/kling/v1/videos/lip-sync"
            params = {"pageNum": 1, "pageSize": 1}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == 0:
                            return {"status": "success", "message": "连接成功"}
                        else:
                            return {
                                "status": "error",
                                "message": f"API返回错误: {result.get('message', '未知错误')}",
                            }
                    elif response.status == 401:
                        return {"status": "error", "message": "API密钥无效或已过期"}
                    elif response.status == 403:
                        return {"status": "error", "message": "API密钥权限不足"}
                    else:
                        return {
                            "status": "error",
                            "message": f"连接失败: HTTP {response.status}",
                        }
        except aiohttp.ClientTimeout:
            return {"status": "error", "message": "连接超时，请检查网络和API地址"}
        except Exception as e:
            logger.error(f"测试可灵对口型API连接失败: {str(e)}")
            return {"status": "error", "message": f"连接异常: {str(e)}"}

    async def _download_audio_to_base64(self, audio_url: str) -> str:
        """从URL下载音频文件并转换为base64"""
        try:
            accessible_url = audio_url
            try:
                file_manager = get_file_manager()
                url = file_manager.get_presigned_download_url(
                    audio_url, expires_in=3600
                )
                if url:
                    accessible_url = url
            except Exception as exc:  # pragma: no cover - 防御性的日志
                logger.warning(f"🎬 【可灵对口型】生成音频预签名URL失败: {exc}")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    accessible_url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        base64_data = base64.b64encode(audio_data).decode("utf-8")
                        logger.info(
                            f"🎬 【可灵对口型】音频文件下载成功，大小: {len(audio_data)} bytes, base64长度: {len(base64_data)}"
                        )
                        return base64_data
                    else:
                        raise Exception(f"下载音频文件失败: HTTP {response.status}")
        except Exception as e:
            logger.error(f"🎬 【可灵对口型】下载音频文件失败: {str(e)}")
            raise

    async def submit_lip_sync_task(self, request_data: dict) -> Dict[str, Any]:
        """提交对口型任务"""
        try:
            logger.info(f"🎬 【可灵对口型API】收到request_data: {request_data}")
            # 构建请求数据
            data = {"input": {"mode": request_data["mode"]}}

            # 添加视频输入参数
            if request_data["input_type"] == "video_url":
                data["input"]["video_url"] = request_data["video_input"]
            elif request_data["input_type"] == "video_id":
                data["input"]["video_id"] = request_data["video_input"]
            else:
                # 默认使用video_url
                data["input"]["video_url"] = request_data["video_input"]

            if request_data["mode"] == "text2video":
                data["input"].update(
                    {
                        "text": request_data["text"],
                        "voice_id": request_data["voice_id"],
                        "voice_language": request_data.get("voice_language", "zh"),
                        "voice_speed": request_data.get("voice_speed", 1.0),
                    }
                )
            elif request_data["mode"] == "audio2video":
                # 统一使用base64方式，因为可灵API的URL方式可能有问题
                if request_data.get("audio_url"):
                    # 从URL下载音频并转换为base64
                    logger.info(
                        f"🎬 【可灵对口型】从URL下载音频: {request_data['audio_url']}"
                    )
                    audio_base64 = await self._download_audio_to_base64(
                        request_data["audio_url"]
                    )
                    data["input"].update(
                        {"audio_type": "file", "audio_file": audio_base64}
                    )
                elif request_data.get("audio_file"):
                    # 直接使用提供的base64数据
                    data["input"].update(
                        {"audio_type": "file", "audio_file": request_data["audio_file"]}
                    )
                else:
                    # 既没有URL也没有文件，这应该在验证阶段被捕获
                    logger.error("🎬 【可灵对口型】既没有audio_url也没有audio_file")
                    pass

            if request_data.get("callback_url"):
                data["callback_url"] = request_data["callback_url"]

            # 打印完整的请求数据（隐藏敏感信息）
            log_data = json.dumps(
                {
                    **data,
                    "input": {
                        **data["input"],
                        "audio_file": (
                            f'[base64_data_{len(data["input"]["audio_file"])}chars]'
                            if data["input"].get("audio_file")
                            else None
                        ),
                        "video_file": (
                            "[base64_data_hidden]"
                            if data["input"].get("video_file")
                            else data["input"].get("video_file")
                        ),
                    },
                },
                ensure_ascii=False,
            )
            logger.info(f"🎬 【可灵对口型】提交任务完整请求: {log_data}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/kling/v1/videos/lip-sync",
                    headers=self.headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    result = await response.json()

                    logger.info(
                        f"🎬 【可灵对口型】API响应: {json.dumps(result, ensure_ascii=False)}"
                    )

                    if response.status == 200 and result.get("code") == 0:
                        return {
                            "success": True,
                            "task_id": result["data"]["task_id"],
                            "message": "任务提交成功",
                            "external_task_id": result["data"][
                                "task_id"
                            ],  # 可灵返回的任务ID
                        }
                    else:
                        error_msg = result.get("message", f"HTTP {response.status}")
                        logger.error(f"🎬 【可灵对口型】提交任务失败: {error_msg}")
                        return {"success": False, "message": error_msg}
        except aiohttp.ClientTimeout:
            error_msg = "请求超时，请稍后重试"
            logger.error(f"🎬 【可灵对口型】提交任务超时")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"API调用异常: {str(e)}"
            logger.error(f"🎬 【可灵对口型】提交任务异常: {error_msg}")
            return {"success": False, "message": error_msg}

    async def get_task_status(self, external_task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/kling/v1/videos/lip-sync/{external_task_id}",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 404:
                        logger.warning(
                            f"🎬 【可灵对口型】任务不存在: {external_task_id}"
                        )
                        return {"status": "failed", "fail_reason": "任务不存在或已过期"}

                    result = await response.json()

                    if response.status == 200 and result.get("code") == 0:
                        data = result["data"]

                        # 转换状态映射
                        status_mapping = {
                            "submitted": "submitted",
                            "processing": "processing",
                            "succeed": "succeed",
                            "failed": "failed",
                        }

                        status = status_mapping.get(data["task_status"], "processing")
                        progress = (
                            "100%"
                            if status == "succeed"
                            else ("50%" if status == "processing" else "0%")
                        )

                        # 获取结果视频URL
                        video_url = None
                        video_duration = None
                        if status == "succeed" and data.get("task_result", {}).get(
                            "videos"
                        ):
                            video_info = data["task_result"]["videos"][0]
                            video_url = video_info.get("url")
                            video_duration = video_info.get("duration")

                        result_data = {
                            "status": status,
                            "progress": progress,
                            "video_url": video_url,
                            "video_duration": video_duration,
                            "fail_reason": (
                                data.get("task_status_msg")
                                if status == "failed"
                                else None
                            ),
                        }

                        logger.info(
                            f"🎬 【可灵对口型】获取任务状态: {external_task_id} -> {status}"
                        )
                        return result_data

                    logger.error(
                        f"🎬 【可灵对口型】获取任务状态失败: {result.get('message', '未知错误')}"
                    )
                    return None
        except aiohttp.ClientTimeout:
            logger.warning(f"🎬 【可灵对口型】获取任务状态超时: {external_task_id}")
            return None
        except Exception as e:
            logger.error(f"🎬 【可灵对口型】获取任务状态异常: {str(e)}")
            return None

    async def get_task_list(
        self, page: int = 1, page_size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """获取任务列表"""
        try:
            params = {"pageNum": page, "pageSize": page_size}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v1/videos/lip-sync",
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    result = await response.json()

                    if response.status == 200 and result.get("code") == 0:
                        return result
                    else:
                        logger.error(
                            f"🎬 【可灵对口型】获取任务列表失败: {result.get('message', '未知错误')}"
                        )
                        return None
        except Exception as e:
            logger.error(f"🎬 【可灵对口型】获取任务列表异常: {str(e)}")
            return None


class KlingLipSyncService:
    """可灵对口型服务管理器"""

    def __init__(self):
        self.api_client = None
        self.config = None

    def initialize(self, config):
        """初始化服务"""
        self.config = config
        if config and config.enabled and config.api_key:
            self.api_client = KlingLipSyncAPI(config.base_url, config.api_key)
            logger.info("🎬 【可灵对口型】服务初始化成功")
        else:
            self.api_client = None
            logger.warning("🎬 【可灵对口型】服务未启用或配置不完整")

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.api_client is not None

    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        if not self.api_client:
            return {"status": "error", "message": "服务未初始化或未启用"}
        return await self.api_client.test_connection()

    async def submit_task(self, request_data: dict) -> Dict[str, Any]:
        """提交任务"""
        if not self.api_client:
            return {"success": False, "message": "服务未初始化或未启用"}
        return await self.api_client.submit_lip_sync_task(request_data)

    async def get_task_status(self, external_task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if not self.api_client:
            return None
        return await self.api_client.get_task_status(external_task_id)

    def get_credits_cost(self) -> int:
        """获取积分消耗"""
        if self.config:
            return self.config.credits_cost
        return 50  # 默认消耗


# 全局服务实例
kling_lip_sync_service = KlingLipSyncService()
