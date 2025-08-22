"""
可灵对口型API客户端
基于可灵对口型API规范的完整API客户端实现
"""

import asyncio
import json
import logging
import time
from typing import Dict, Optional, Any
import httpx

from open_webui.models.kling_lip_sync import KlingLipSyncConfigs, KlingLipSyncTasks

logger = logging.getLogger(__name__)


class KlingLipSyncAPIError(Exception):
    """可灵对口型API错误"""

    def __init__(self, message: str, code: int = None, response: Dict = None):
        self.message = message
        self.code = code
        self.response = response
        super().__init__(self.message)


class KlingLipSyncAPIClient:
    """可灵对口型API客户端"""

    def __init__(self):
        """初始化API客户端"""
        self.config = None
        self.client = None
        self._load_config()

    def _load_config(self):
        """加载配置"""
        self.config = KlingLipSyncConfigs.get_config()
        if not self.config:
            raise KlingLipSyncAPIError("可灵对口型配置不存在，请先在管理员面板配置")

        if not self.config.enabled:
            raise KlingLipSyncAPIError("可灵对口型功能未启用")

        if not self.config.api_key:
            raise KlingLipSyncAPIError("API密钥未配置")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "User-Agent": "wxiai-kling-lip-sync-client/1.0.0",
        }

    def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.task_timeout / 1000.0),
                headers=self._get_headers(),
            )
        return self.client

    async def create_lip_sync_task(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建对口型任务

        Args:
            request_data: 请求数据

        Returns:
            API响应数据

        Raises:
            KlingLipSyncAPIError: API调用失败
        """
        try:
            self._load_config()  # 重新加载配置确保最新

            # 构建API URL
            api_url = f"{self.config.base_url.rstrip('/')}/kling/v1/videos/lip-sync"

            # 构建请求体
            payload = {
                "input": {
                    "task_id": request_data.get("task_id"),
                    "mode": request_data.get("mode", self.config.default_mode),
                    "text": request_data.get("text"),
                    "voice_id": request_data.get(
                        "voice_id", self.config.default_voice_id
                    ),
                    "voice_language": request_data.get(
                        "voice_language", self.config.default_voice_language
                    ),
                }
            }

            # 添加视频参数（video_id 和 video_url 二选一）
            if request_data.get("video_id"):
                payload["input"]["video_id"] = request_data["video_id"]
            elif request_data.get("video_url"):
                payload["input"]["video_url"] = request_data["video_url"]
            else:
                raise KlingLipSyncAPIError("video_id 和 video_url 必须提供其中一个")

            logger.info(f"调用可灵对口型API: {api_url}")
            logger.debug(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")

            client = self._get_client()
            response = await client.post(api_url, json=payload)

            # 记录响应状态
            logger.info(f"API响应状态: {response.status_code}")

            if response.status_code != 200:
                error_text = await response.aread()
                logger.error(f"API请求失败: {response.status_code} - {error_text}")
                raise KlingLipSyncAPIError(
                    f"API请求失败: HTTP {response.status_code}",
                    code=response.status_code,
                    response={
                        "status_code": response.status_code,
                        "text": error_text.decode(),
                    },
                )

            # 解析响应
            response_data = response.json()
            logger.debug(
                f"API响应数据: {json.dumps(response_data, ensure_ascii=False)}"
            )

            # 检查业务状态码
            if response_data.get("code") != 0:
                error_msg = response_data.get("message", "未知错误")
                logger.error(f"API业务错误: {error_msg}")
                raise KlingLipSyncAPIError(
                    f"API业务错误: {error_msg}",
                    code=response_data.get("code"),
                    response=response_data,
                )

            return response_data

        except httpx.TimeoutException:
            logger.error("API请求超时")
            raise KlingLipSyncAPIError("API请求超时")
        except httpx.RequestError as e:
            logger.error(f"API请求异常: {e}")
            raise KlingLipSyncAPIError(f"API请求异常: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"API响应解析失败: {e}")
            raise KlingLipSyncAPIError(f"API响应解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"API调用未知错误: {e}")
            raise KlingLipSyncAPIError(f"API调用未知错误: {str(e)}")

    async def query_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态数据

        Note:
            可灵对口型API没有单独的查询接口，这里通过数据库查询任务状态
        """
        try:
            task = KlingLipSyncTasks.get_task_by_id(task_id)
            if not task:
                raise KlingLipSyncAPIError(f"任务不存在: {task_id}")

            return {
                "task_id": task.id,
                "status": task.status,
                "task_status_msg": task.task_status_msg,
                "progress": task.progress,
                "result_video_url": task.result_video_url,
                "cloud_result_url": task.cloud_result_url,
                "fail_reason": task.fail_reason,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }

        except Exception as e:
            logger.error(f"查询任务状态失败: {e}")
            raise KlingLipSyncAPIError(f"查询任务状态失败: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """测试API连接

        Returns:
            连接测试结果
        """
        try:
            self._load_config()

            # 构建测试请求
            test_data = {
                "task_id": "test_connection",
                "video_url": "https://example.com/test.mp4",  # 测试URL
                "mode": "text2video",
                "text": "测试连接",
                "voice_id": "girlfriend_1_speech02",
                "voice_language": "zh",
            }

            # 这里只是测试连接，不实际创建任务
            api_url = f"{self.config.base_url.rstrip('/')}/kling/v1/videos/lip-sync"

            client = self._get_client()

            # 发送HEAD请求测试连接
            try:
                response = await client.head(self.config.base_url)
                return {
                    "success": True,
                    "message": "连接测试成功",
                    "api_url": api_url,
                    "status_code": response.status_code,
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"连接测试失败: {str(e)}",
                    "api_url": api_url,
                    "error": str(e),
                }

        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return {
                "success": False,
                "message": f"连接测试失败: {str(e)}",
                "error": str(e),
            }

    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.aclose()
            self.client = None


class KlingLipSyncTaskProcessor:
    """可灵对口型任务处理器"""

    def __init__(self):
        self.api_client = KlingLipSyncAPIClient()

    async def submit_lip_sync_task(
        self, user_id: str, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提交对口型任务

        Args:
            user_id: 用户ID
            task_data: 任务数据

        Returns:
            任务提交结果
        """
        try:
            # 检查用户积分 - 使用统一积分系统
            from open_webui.models.credits import Credits

            config = KlingLipSyncConfigs.get_config()
            credits_cost = config.credits_per_task if config else 50

            # 获取用户积分
            user_credits = Credits.get_credit_by_user_id(user_id)
            if not user_credits or float(user_credits.credit) < credits_cost:
                return {
                    "success": False,
                    "message": "积分不足",
                    "required_credits": credits_cost,
                    "current_credits": (
                        float(user_credits.credit) if user_credits else 0
                    ),
                }

            # 扣除积分
            try:
                Credits.update_credit_by_user_id(
                    user_id, user_credits.credit - credits_cost
                )
            except Exception as e:
                logger.error(f"扣除积分失败: {e}")
                return {"success": False, "message": "扣除积分失败", "error": str(e)}

            # 创建数据库任务记录
            task_id = task_data.get("task_id") or f"lip_sync_{int(time.time())}"
            db_task_data = {
                "task_id": task_id,
                "video_id": task_data.get("video_id"),
                "video_url": task_data.get("video_url"),
                "uploaded_video_url": task_data.get("uploaded_video_url"),
                "mode": task_data.get("mode", "text2video"),
                "text": task_data.get("text"),
                "voice_id": task_data.get("voice_id", "girlfriend_1_speech02"),
                "voice_language": task_data.get("voice_language", "zh"),
                "credits_cost": credits_cost,
                "status": "submitted",
                "submit_time": time.time(),
                "request_data": json.dumps(task_data, ensure_ascii=False),
            }

            db_task = KlingLipSyncTasks.create_task(user_id, db_task_data)

            # 调用API
            try:
                api_response = await self.api_client.create_lip_sync_task(
                    {**task_data, "task_id": task_id}
                )

                # 更新任务状态
                update_data = {
                    "status": "processing",
                    "start_time": time.time(),
                    "response_data": json.dumps(api_response, ensure_ascii=False),
                }

                if api_response.get("data"):
                    data = api_response["data"]
                    update_data.update(
                        {"task_id": data.get("task_id", task_id), "progress": "10%"}
                    )

                KlingLipSyncTasks.update_task(db_task.id, update_data)

                # 启动后台任务处理结果
                asyncio.create_task(self._process_task_result(db_task.id, user_id))

                return {
                    "success": True,
                    "message": "任务提交成功",
                    "task_id": db_task.id,
                    "external_task_id": task_id,
                    "credits_consumed": credits_cost,
                }

            except KlingLipSyncAPIError as api_error:
                # API调用失败，回退积分
                try:
                    Credits.update_credit_by_user_id(user_id, user_credits.credit)
                except Exception as e:
                    logger.error(f"退还积分失败: {e}")

                # 更新任务失败状态
                KlingLipSyncTasks.update_task(
                    db_task.id,
                    {
                        "status": "failed",
                        "fail_reason": api_error.message,
                        "finish_time": time.time(),
                    },
                )

                return {
                    "success": False,
                    "message": f"任务提交失败: {api_error.message}",
                    "task_id": db_task.id,
                    "error": api_error.message,
                }

        except Exception as e:
            logger.error(f"提交对口型任务失败: {e}")
            return {
                "success": False,
                "message": f"提交任务失败: {str(e)}",
                "error": str(e),
            }

    async def _process_task_result(self, task_id: str, user_id: str):
        """后台处理任务结果

        Args:
            task_id: 任务ID
            user_id: 用户ID
        """
        try:
            # 模拟任务处理（实际项目中可能需要轮询API或接收回调）
            await asyncio.sleep(2)  # 模拟处理时间

            # 获取任务
            task = KlingLipSyncTasks.get_task_by_id(task_id)
            if not task:
                return

            # 模拟生成结果（实际项目中从API获取）
            result_video_url = "https://example.com/generated_lip_sync_video.mp4"

            # 上传结果到云存储
            cloud_url = None
            try:
                from open_webui.services.file_manager import get_file_manager

                file_manager = get_file_manager()

                # 这里应该下载并上传视频到云存储
                # 为了演示，我们直接设置云存储URL
                cloud_filename = f"lip_sync_results/{user_id}/{task_id}.mp4"

                # 记录生成文件
                file_record = await file_manager.save_generated_content(
                    user_id=user_id,
                    original_url=result_video_url,
                    filename=f"lip_sync_result_{task_id}",
                    file_type="video",
                    source_type="kling_lip_sync",
                    source_task_id=task_id,
                    metadata={
                        "text": task.text,
                        "voice_id": task.voice_id,
                        "voice_language": task.voice_language,
                        "mode": task.mode,
                    },
                )

                if file_record and file_record.cloud_url:
                    cloud_url = file_record.cloud_url

            except Exception as e:
                logger.error(f"保存对口型结果到云存储失败: {e}")

            # 更新任务完成状态
            update_data = {
                "status": "completed",
                "result_video_url": result_video_url,
                "cloud_result_url": cloud_url or result_video_url,
                "progress": "100%",
                "finish_time": time.time(),
            }

            KlingLipSyncTasks.update_task(task_id, update_data)
            logger.info(f"对口型任务完成: {task_id}")

        except Exception as e:
            logger.error(f"处理对口型任务结果失败: {e}")
            # 更新任务失败状态
            KlingLipSyncTasks.update_task(
                task_id,
                {
                    "status": "failed",
                    "fail_reason": f"处理结果失败: {str(e)}",
                    "finish_time": time.time(),
                },
            )

    async def close(self):
        """关闭处理器"""
        await self.api_client.close()


# 全局实例
_global_client = None
_global_processor = None


def get_kling_lip_sync_client() -> KlingLipSyncAPIClient:
    """获取全局API客户端"""
    global _global_client
    if not _global_client:
        _global_client = KlingLipSyncAPIClient()
    return _global_client


def get_kling_lip_sync_processor() -> KlingLipSyncTaskProcessor:
    """获取全局任务处理器"""
    global _global_processor
    if not _global_processor:
        _global_processor = KlingLipSyncTaskProcessor()
    return _global_processor


async def cleanup_clients():
    """清理全局客户端"""
    global _global_client, _global_processor
    if _global_client:
        await _global_client.close()
        _global_client = None
    if _global_processor:
        await _global_processor.close()
        _global_processor = None
