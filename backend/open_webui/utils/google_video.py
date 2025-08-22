"""
谷歌视频生成工具类
包含API客户端、积分管理、任务处理等工具
"""

import httpx
import asyncio
import json
import base64
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from open_webui.models.google_video import (
    GoogleVideoConfig,
    GoogleVideoTask,
    GoogleVideoTextToVideoRequest,
    GoogleVideoImageToVideoRequest,
    validate_image_to_video_request,
)
from open_webui.internal.db import get_db


class GoogleVideoApiClient:
    """谷歌视频API客户端"""

    def __init__(self, config: GoogleVideoConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def submit_text_to_video(
        self, request: GoogleVideoTextToVideoRequest
    ) -> dict:
        """提交文生视频任务"""
        url = f"{self.base_url}/google/v1/models/veo/videos"

        # 构建请求数据
        request_data = {
            "prompt": request.prompt.strip(),
            "model": request.model,
            "enhance_prompt": request.enhance_prompt,
        }

        print(f"🎬 【谷歌视频API】文生视频请求URL: {url}")
        print(
            f"🎬 【谷歌视频API】请求参数: {json.dumps(request_data, ensure_ascii=False)}"
        )

        return await self._make_request("POST", url, request_data)

    async def submit_image_to_video(
        self, request: GoogleVideoImageToVideoRequest
    ) -> dict:
        """提交图生视频任务"""
        url = f"{self.base_url}/google/v1/models/veo/videos"

        # 构建请求数据
        request_data = {
            "prompt": request.prompt.strip(),
            "model": request.model,
            "enhance_prompt": request.enhance_prompt,
            "images": request.images,  # URL或base64数组
        }

        print(f"🎬 【谷歌视频API】图生视频请求URL: {url}")
        print(
            f"🎬 【谷歌视频API】请求参数: {json.dumps(request_data, ensure_ascii=False)}"
        )

        return await self._make_request("POST", url, request_data)

    async def get_task_status(self, task_id: str) -> dict:
        """查询任务状态"""
        url = f"{self.base_url}/google/v1/tasks/{task_id}"

        print(f"🎬 【谷歌视频API】查询任务状态URL: {url}")
        return await self._make_request("GET", url)

    async def _make_request(self, method: str, url: str, data: dict = None) -> dict:
        """统一HTTP请求处理"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"🎬 【谷歌视频API】开始发送 {method} 请求到: {url}")

                if method == "GET":
                    response = await client.get(url, headers=self.headers)
                else:
                    response = await client.post(url, json=data, headers=self.headers)

                print(f"🎬 【谷歌视频API】响应状态: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(
                            f"🎬 【谷歌视频API】响应成功: {json.dumps(result, ensure_ascii=False)}"
                        )
                        return result
                    except Exception as json_error:
                        # JSON解析失败，返回错误格式的字典
                        error_text = response.text
                        print(f"🎬 【谷歌视频API】JSON解析失败: {error_text}")
                        return {
                            "code": "error",
                            "message": f"响应格式错误: {error_text[:200]}",
                            "data": None,
                        }
                else:
                    error_text = response.text
                    print(f"🎬 【谷歌视频API】响应失败: {error_text}")
                    # 返回错误格式的字典而不是抛出异常
                    return {
                        "code": "error",
                        "message": f"API请求失败: {response.status_code} - {error_text[:200]}",
                        "data": None,
                    }

        except httpx.TimeoutException:
            print("🎬 【谷歌视频API】请求超时")
            return {"code": "error", "message": "API请求超时", "data": None}
        except Exception as e:
            print(f"🎬 【谷歌视频API】请求异常: {str(e)}")
            return {
                "code": "error",
                "message": f"请求异常: {str(e)[:200]}",
                "data": None,
            }

    async def test_connection(self) -> bool:
        """测试API连接"""
        try:
            # 尝试提交一个简单的测试任务来验证连接
            test_request = GoogleVideoTextToVideoRequest(
                prompt="test connection", model="veo3-fast", enhance_prompt=False
            )

            response = await self.submit_text_to_video(test_request)

            # 检查响应格式
            if isinstance(response, dict):
                if response.get("code") == "success":
                    return True
                elif response.get("code") == "error":
                    print(f"🎬 【谷歌视频API】连接测试失败: {response.get('message')}")
                    return False

            # 其他情况也认为失败
            print(f"🎬 【谷歌视频API】连接测试失败: 响应格式异常")
            return False

        except Exception as e:
            print(f"🎬 【谷歌视频API】连接测试失败: {str(e)}")
            return False


# ======================== 积分管理工具 ========================

# 用于缓存积分系统可用性的全局变量
_credit_system_available = None
_credit_import_error_logged = False


def get_user_google_video_credits(user_id: str) -> int:
    """获取用户谷歌视频积分余额"""
    global _credit_system_available, _credit_import_error_logged

    # 只在第一次检查时打印警告信息
    if _credit_system_available is None:
        try:
            from open_webui.utils.kling import get_user_credit_balance

            _credit_system_available = True
        except ImportError:
            _credit_system_available = False
            if not _credit_import_error_logged:
                print("⚠️ 【谷歌视频】无法导入Kling积分系统，使用默认积分1000")
                _credit_import_error_logged = True

    if _credit_system_available:
        try:
            from open_webui.utils.kling import get_user_credit_balance

            return get_user_credit_balance(user_id)
        except Exception as e:
            print(f"⚠️ 【谷歌视频】获取积分失败: {e}")
            return 1000
    else:
        return 1000


def deduct_user_google_video_credits(
    user_id: str, amount: int, task_id: str, reason: str
) -> bool:
    """扣除用户谷歌视频积分"""
    try:
        from open_webui.utils.kling import deduct_user_credits

        return deduct_user_credits(user_id, amount, task_id, reason)
    except ImportError:
        print("⚠️ 【谷歌视频】无法导入Kling积分系统，跳过积分扣除")
        return True


def validate_user_google_video_credits(user_id: str, required_credits: int) -> bool:
    """验证用户积分是否足够"""
    current_credits = get_user_google_video_credits(user_id)
    return current_credits >= required_credits


# ======================== 任务处理工具 ========================


async def process_google_video_task_polling(
    task: GoogleVideoTask, client: GoogleVideoApiClient
):
    """轮询任务状态直到完成"""
    max_attempts = 180  # 最多轮询30分钟（每10秒一次）
    poll_interval = 10  # 10秒轮询一次，提高频率以快速获取结果

    for attempt in range(max_attempts):
        try:
            # 检查是否有有效的external_task_id
            if not task.external_task_id:
                print(f"🎬 【谷歌视频】任务 {task.id} 缺少external_task_id，停止轮询")
                task.status = "FAILURE"
                task.fail_reason = "缺少第三方任务ID"
                with get_db() as db:
                    db.merge(task)
                    db.commit()
                break

            # 查询任务状态
            response = await client.get_task_status(task.external_task_id)

            # 检查response格式
            if not isinstance(response, dict):
                print(f"🎬 【谷歌视频】任务 {task.id} 响应格式错误: {str(response)}")
                continue

            if response.get("code") == "success":
                # 更新任务信息
                task.update_from_api_response(response)

                # 检查任务是否完成
                status = response.get("data", {}).get("status", "")
                if status in ["SUCCESS", "FAILURE"]:
                    print(f"🎬 【谷歌视频】任务 {task.id} 已完成，状态: {status}")

                    # 如果成功且有视频URL，立即触发云存储上传
                    if status == "SUCCESS" and task.video_url:
                        print(f"🎬 【谷歌视频】任务 {task.id} 立即开始云存储上传...")
                        try:
                            await upload_video_to_cloud_storage(task)
                            print(f"🎬 【谷歌视频】任务 {task.id} 云存储上传完成")
                        except Exception as upload_error:
                            print(
                                f"🎬 【谷歌视频】任务 {task.id} 云存储上传失败: {upload_error}"
                            )

                    break
                else:
                    # 打印详细的进度信息
                    video_url_status = "有视频URL" if task.video_url else "暂无视频URL"
                    print(
                        f"🎬 【谷歌视频】任务 {task.id} 进行中 - 状态: {status}, 进度: {task.progress}, {video_url_status}"
                    )

                    # 如果已经有视频URL但状态还不是SUCCESS，也尝试上传
                    if task.video_url and task.cloud_upload_status == "pending":
                        print(
                            f"🎬 【谷歌视频】任务 {task.id} 提前发现视频URL，开始预上传..."
                        )
                        try:
                            await upload_video_to_cloud_storage(task)
                        except Exception as upload_error:
                            print(
                                f"🎬 【谷歌视频】任务 {task.id} 预上传失败: {upload_error}"
                            )
            else:
                # API返回错误
                error_msg = response.get("message", "未知查询错误")
                print(f"🎬 【谷歌视频】任务 {task.id} 查询失败: {error_msg}")

                # 如果是严重错误，停止轮询
                if "不存在" in error_msg or "invalid" in error_msg.lower():
                    task.status = "FAILURE"
                    task.fail_reason = error_msg
                    with get_db() as db:
                        db.merge(task)
                        db.commit()
                    break

        except Exception as e:
            print(f"🎬 【谷歌视频】轮询任务 {task.id} 异常: {str(e)}")

        # 等待下次轮询
        if attempt < max_attempts - 1:
            await asyncio.sleep(poll_interval)

    else:
        # 超时处理
        print(f"🎬 【谷歌视频】任务 {task.id} 轮询超时")
        task.status = "FAILURE"
        task.fail_reason = "任务轮询超时"
        with get_db() as db:
            db.merge(task)
            db.commit()


async def upload_video_to_cloud_storage(task: GoogleVideoTask):
    """上传视频到云存储"""
    try:
        from open_webui.services.file_manager import get_file_manager

        file_manager = get_file_manager()

        # 上传视频到云存储
        success, message, file_record = await file_manager.save_generated_content(
            user_id=task.user_id,
            file_url=task.video_url,
            filename=f"google_video_{task.id}.mp4",
            file_type="video",
            source_type="google_video",
            source_task_id=task.id,
            metadata={
                "model": task.model,
                "prompt": task.prompt,
                "task_type": task.task_type,
            },
        )

        if success and file_record and file_record.cloud_url:
            task.cloud_video_url = file_record.cloud_url
            task.cloud_upload_status = "uploaded"
            print(
                f"🎬 【谷歌视频】任务 {task.id} 视频已上传到云存储: {file_record.cloud_url}"
            )
        else:
            task.cloud_upload_status = "failed"
            print(f"🎬 【谷歌视频】任务 {task.id} 视频上传到云存储失败: {message}")

        with get_db() as db:
            db.merge(task)
            db.commit()

    except Exception as e:
        print(f"🎬 【谷歌视频】上传视频到云存储异常: {str(e)}")
        task.cloud_upload_status = "failed"
        with get_db() as db:
            db.merge(task)
            db.commit()
