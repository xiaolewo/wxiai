"""
即梦视频生成工具类
包含API客户端、积分管理、任务处理等工具
"""

import httpx
import asyncio
import json
import base64
import os
import tempfile
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from open_webui.models.jimeng import JimengConfig, JimengTask, JimengGenerateRequest
from open_webui.config import CACHE_DIR


def save_base64_to_temp_file(base64_data: str) -> str:
    """将base64数据保存为临时文件并返回可访问的URL"""
    try:
        # 解析base64数据
        if base64_data.startswith("data:"):
            # 提取格式和数据
            header, data = base64_data.split(",", 1)
            # 提取文件格式
            if "image/jpeg" in header or "image/jpg" in header:
                ext = ".jpg"
            elif "image/png" in header:
                ext = ".png"
            elif "image/webp" in header:
                ext = ".webp"
            else:
                ext = ".jpg"  # 默认格式
        else:
            # 纯base64数据，默认jpg格式
            data = base64_data
            ext = ".jpg"

        # 创建临时文件
        temp_dir = os.path.join(CACHE_DIR, "jimeng_temp_images")
        os.makedirs(temp_dir, exist_ok=True)

        filename = f"jimeng_temp_{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(temp_dir, filename)

        # 解码并保存文件
        image_data = base64.b64decode(data)
        with open(file_path, "wb") as f:
            f.write(image_data)

        # 构建可访问的URL - 使用正确的API端点
        relative_path = f"api/v1/jimeng/temp-image/{filename}"

        print(f"🎬 【即梦】Base64图片已保存为临时文件: {file_path}")
        print(f"🎬 【即梦】临时文件相对路径: {relative_path}")

        return relative_path

    except Exception as e:
        print(f"❌ 【即梦】保存临时文件失败: {e}")
        raise ValueError(f"无法处理图片数据: {e}")


class JimengApiClient:
    """即梦API客户端"""

    def __init__(self, config: JimengConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 确定API路径前缀
        if config.detected_api_path:
            # 使用已检测到的有效路径
            self.api_path_prefix = config.detected_api_path
            print(f"🎬 【即梦客户端】使用已检测的API路径: {self.api_path_prefix}")
        else:
            # 使用默认路径
            self.api_path_prefix = "/jimeng/submit/videos"
            print(f"🎬 【即梦客户端】使用默认API路径: {self.api_path_prefix}")

    def _get_api_url(self, endpoint: str = "") -> str:
        """构建完整的API URL"""
        if endpoint:
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.base_url}{self.api_path_prefix}"

        print(f"🎬 【即梦客户端】构建API URL: {url}")
        return url

    async def generate_video(self, request: JimengGenerateRequest) -> dict:
        """生成视频（文生视频或图生视频）"""
        url = self._get_api_url()

        # 构建请求数据
        request_data = {
            "prompt": request.prompt.strip(),
            "duration": int(request.duration),
            "aspect_ratio": request.aspect_ratio,
            "cfg_scale": float(request.cfg_scale),
        }

        # 如果有图片URL，添加图生视频参数
        if request.image_url:
            request_data["image_url"] = request.image_url
            print(f"🎬 【即梦API】使用提供的图片URL: {request.image_url}")
        elif request.image:
            # 尝试直接发送base64数据给即梦API
            print("🎬 【即梦API】检测到base64图片数据...")
            try:
                # 先尝试直接将base64数据作为image字段发送
                if request.image.startswith("data:"):
                    # 如果是完整的data URL，直接使用
                    request_data["image"] = request.image
                    print(f"🎬 【即梦API】使用完整data URL格式发送图片")
                else:
                    # 如果是纯base64数据，添加适当的前缀
                    request_data["image"] = f"data:image/jpeg;base64,{request.image}"
                    print(f"🎬 【即梦API】添加data URL前缀后发送图片")

                print(f"🎬 【即梦API】图片数据长度: {len(request_data['image'])} 字符")

            except Exception as e:
                print(f"❌ 【即梦API】处理base64图片数据失败: {e}")
                raise ValueError(f"无法处理图片数据: {e}")
        else:
            # 没有提供图片，这是正常的文生视频模式
            print("🎬 【即梦API】文生视频模式，不需要图片数据")

        print(f"🎬 【即梦API】视频生成请求URL: {url}")
        print(
            f"🎬 【即梦API】请求头: {json.dumps({k: '***' if k == 'Authorization' else v for k, v in self.headers.items()}, ensure_ascii=False)}"
        )
        print(f"🎬 【即梦API】请求参数: {json.dumps(request_data, ensure_ascii=False)}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"🎬 【即梦API】开始发送HTTP请求到: {url}")
                response = await client.post(
                    url, json=request_data, headers=self.headers
                )
                print(f"🎬 【即梦API】响应状态: {response.status_code}")
                print(f"🎬 【即梦API】响应头: {dict(response.headers)}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"🎬 【即梦API】响应成功: {result}")
                    return result
                else:
                    error_text = response.text
                    print(
                        f"🎬 【即梦API】响应错误 ({response.status_code}): {error_text}"
                    )

                    try:
                        error_json = response.json()
                        error_message = error_json.get("message", "API请求失败")
                        print(f"🎬 【即梦API】解析错误JSON: {error_json}")
                        raise ValueError(
                            f"即梦API错误 ({response.status_code}): {error_message}"
                        )
                    except json.JSONDecodeError:
                        print(f"🎬 【即梦API】无法解析错误响应为JSON")
                        raise ValueError(
                            f"即梦API错误 ({response.status_code}): {error_text[:200]}"
                        )

        except httpx.TimeoutException:
            raise ValueError("即梦API请求超时，请稍后重试")
        except httpx.ConnectError as e:
            raise ValueError(f"无法连接到即梦API: {e}")
        except Exception as e:
            if "即梦API错误" in str(e):
                raise
            print(f"🎬 【即梦API】请求异常: {e}")
            import traceback

            traceback.print_exc()
            raise ValueError(f"即梦API请求失败: {e}")

    async def query_task(self, task_id: str) -> dict:
        """查询任务状态"""
        print(f"🔍 【即梦API】查询任务状态: {task_id}")

        # 使用正确的即梦API查询端点
        query_path = f"/jimeng/fetch/{task_id}"
        url = f"{self.base_url}{query_path}"

        try:
            print(f"🔍 【即梦API】查询URL: {url}")

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self.headers)

                print(f"🔍 【即梦API】查询响应状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(
                        f"✅ 【即梦API】查询成功: {json.dumps(result, ensure_ascii=False)}"
                    )

                    # 解析即梦API响应
                    if result.get("code") == "success":
                        data = result.get("data", {})
                        task_status = data.get("status", "UNKNOWN")
                        progress = data.get("progress", "0%")

                        # 状态映射：即梦状态 -> 系统状态
                        status_map = {
                            "NOT_START": "submitted",
                            "SUBMITTED": "submitted",
                            "QUEUED": "processing",
                            "IN_PROGRESS": "processing",
                            "SUCCESS": "succeed",
                            "FAILURE": "failed",
                        }

                        mapped_status = status_map.get(task_status, "processing")

                        # 构建返回数据
                        response_data = {
                            "code": "success",
                            "message": "查询成功",
                            "data": {
                                "status": mapped_status,
                                "progress": progress,
                                "task_id": task_id,
                            },
                        }

                        # 如果任务成功完成，提取视频URL
                        if task_status == "SUCCESS":
                            video_url = None

                            # 从多层嵌套结构中提取视频URL
                            try:
                                # 方法1: 直接从 data.data.video 获取
                                nested_data = data.get("data", {})
                                if isinstance(nested_data, dict):
                                    video_url = nested_data.get("video")

                                # 方法2: 从 data.data.data.video 获取（适应不同的响应结构）
                                if not video_url and "data" in nested_data:
                                    deep_data = nested_data.get("data", {})
                                    if isinstance(deep_data, dict):
                                        video_url = deep_data.get("video")

                                # 方法3: 从复杂的嵌套结构中提取
                                if not video_url:
                                    metadata = nested_data.get("metadata", {})
                                    if isinstance(metadata, dict):
                                        metadata_data = metadata.get("data", {})
                                        if isinstance(metadata_data, dict):
                                            task_map = metadata_data.get("task_map", {})
                                            if (
                                                isinstance(task_map, dict)
                                                and task_id in task_map
                                            ):
                                                task_info = task_map[task_id]
                                                item_list = task_info.get(
                                                    "item_list", []
                                                )
                                                if item_list and len(item_list) > 0:
                                                    item = item_list[0]
                                                    transcoded_video = item.get(
                                                        "transcoded_video", {}
                                                    )
                                                    if (
                                                        transcoded_video
                                                        and "origin" in transcoded_video
                                                    ):
                                                        video_url = transcoded_video[
                                                            "origin"
                                                        ].get("video_url")

                                if video_url:
                                    response_data["data"]["video_url"] = video_url
                                    print(f"✅ 【即梦API】提取到视频URL: {video_url}")
                                else:
                                    print(f"⚠️ 【即梦API】任务成功但未找到视频URL")

                            except Exception as e:
                                print(f"❌ 【即梦API】提取视频URL失败: {e}")

                        # 如果任务失败，提取失败原因
                        elif task_status == "FAILURE":
                            fail_reason = data.get("fail_reason", "生成失败")
                            response_data["data"]["fail_reason"] = fail_reason

                        return response_data
                    else:
                        # API返回错误
                        error_message = result.get("message", "查询失败")
                        print(f"❌ 【即梦API】API返回错误: {error_message}")
                        return {
                            "code": "error",
                            "message": error_message,
                            "data": {
                                "status": "failed",
                                "progress": "0%",
                                "fail_reason": error_message,
                            },
                        }
                else:
                    error_text = response.text
                    print(
                        f"❌ 【即梦API】HTTP错误 ({response.status_code}): {error_text}"
                    )
                    return {
                        "code": "error",
                        "message": f"HTTP错误: {response.status_code}",
                        "data": {
                            "status": "failed",
                            "progress": "0%",
                            "fail_reason": f"HTTP {response.status_code}: {error_text[:100]}",
                        },
                    }

        except httpx.TimeoutException:
            print(f"❌ 【即梦API】查询超时: {task_id}")
            return {
                "code": "error",
                "message": "查询超时",
                "data": {"status": "processing", "progress": "50%"},
            }
        except Exception as e:
            print(f"❌ 【即梦API】查询异常: {e}")
            return {
                "code": "error",
                "message": str(e),
                "data": {"status": "failed", "progress": "0%", "fail_reason": str(e)},
            }


# ======================== 积分管理 ========================


def get_user_credit_balance(user_id: str) -> float:
    """获取用户积分余额 - 使用系统积分"""
    from open_webui.models.credits import Credits
    from decimal import Decimal

    try:
        credit_model = Credits.get_credit_by_user_id(user_id)
        if credit_model:
            return float(credit_model.credit)
        return 0.0
    except Exception:
        return 0.0


def validate_user_credits(user_id: str, required_credits: int) -> bool:
    """验证用户积分是否足够"""
    balance = get_user_credit_balance(user_id)
    return balance >= required_credits


def deduct_user_credits(
    user_id: str, amount: int, reason: str, task_id: Optional[str] = None
) -> float:
    """扣除用户积分 - 使用系统积分"""
    from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
    from decimal import Decimal

    try:
        # 扣除积分（负数）
        form_data = AddCreditForm(
            user_id=user_id,
            amount=Decimal(-amount),
            detail=SetCreditFormDetail(
                desc=f"即梦视频生成: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "jimeng", "credits": amount},
            ),
        )

        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        print(f"Error deducting Jimeng credits: {e}")
        return 0.0


def add_user_credits(
    user_id: str, amount: int, reason: str, task_id: Optional[str] = None
) -> float:
    """增加用户积分 - 使用系统积分"""
    from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
    from decimal import Decimal

    try:
        form_data = AddCreditForm(
            user_id=user_id,
            amount=Decimal(amount),
            detail=SetCreditFormDetail(
                desc=f"即梦视频生成: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "jimeng", "credits": amount},
            ),
        )

        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        print(f"Error adding Jimeng credits: {e}")
        return 0.0


# ======================== 管理员功能 ========================


def admin_add_credits_to_user(
    admin_id: str, target_user_id: str, amount: int, reason: str = ""
) -> float:
    """管理员给用户充值积分"""
    full_reason = (
        f"Admin {admin_id} added Jimeng credits: {reason}"
        if reason
        else f"Admin {admin_id} added Jimeng credits"
    )
    return add_user_credits(target_user_id, amount, full_reason)


def admin_deduct_credits_from_user(
    admin_id: str, target_user_id: str, amount: int, reason: str = ""
) -> float:
    """管理员扣除用户积分"""
    full_reason = (
        f"Admin {admin_id} deducted Jimeng credits: {reason}"
        if reason
        else f"Admin {admin_id} deducted Jimeng credits"
    )
    return deduct_user_credits(target_user_id, amount, full_reason)


# ======================== 统计功能 ========================


def get_system_jimeng_stats() -> dict:
    """获取系统即梦统计"""
    from open_webui.models.jimeng import JimengTask
    from open_webui.internal.db import get_db
    from sqlalchemy import func

    with get_db() as db:
        # 总任务数
        total_tasks = db.query(JimengTask).count()

        # 成功任务数
        success_tasks = (
            db.query(JimengTask).filter(JimengTask.status == "succeed").count()
        )

        # 今日任务数
        today = datetime.utcnow().date()
        today_tasks = (
            db.query(JimengTask)
            .filter(func.date(JimengTask.created_at) == today)
            .count()
        )

        # 各状态任务数
        status_stats = (
            db.query(JimengTask.status, func.count(JimengTask.id))
            .group_by(JimengTask.status)
            .all()
        )

        # 各动作类型统计
        action_stats = (
            db.query(JimengTask.action, func.count(JimengTask.id))
            .group_by(JimengTask.action)
            .all()
        )

        return {
            "total_tasks": total_tasks,
            "success_tasks": success_tasks,
            "today_tasks": today_tasks,
            "success_rate": (
                round(success_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
            ),
            "status_distribution": dict(status_stats),
            "action_distribution": dict(action_stats),
        }


def get_user_jimeng_stats(user_id: str) -> dict:
    """获取用户即梦统计"""
    from open_webui.models.jimeng import JimengTask
    from open_webui.internal.db import get_db
    from sqlalchemy import func

    with get_db() as db:
        # 用户任务数
        user_tasks = db.query(JimengTask).filter(JimengTask.user_id == user_id).count()

        # 用户成功任务数
        user_success = (
            db.query(JimengTask)
            .filter(JimengTask.user_id == user_id, JimengTask.status == "succeed")
            .count()
        )

        # 用户今日任务数
        today = datetime.utcnow().date()
        user_today = (
            db.query(JimengTask)
            .filter(
                JimengTask.user_id == user_id, func.date(JimengTask.created_at) == today
            )
            .count()
        )

        # 用户积分余额
        balance = get_user_credit_balance(user_id)

        # 用户总消费积分
        total_spent = (
            db.query(func.sum(JimengTask.credits_cost))
            .filter(JimengTask.user_id == user_id)
            .scalar()
            or 0
        )

        return {
            "total_tasks": user_tasks,
            "success_tasks": user_success,
            "today_tasks": user_today,
            "success_rate": (
                round(user_success / user_tasks * 100, 2) if user_tasks > 0 else 0
            ),
            "credit_balance": balance,
            "total_credits_spent": total_spent,
        }


# ======================== 任务处理 ========================


async def process_jimeng_generation(
    user_id: str, request: JimengGenerateRequest, action: str = "TEXT_TO_VIDEO"
) -> JimengTask:
    """处理即梦视频生成任务"""
    config = JimengConfig.get_config()
    if not config or not config.enabled:
        raise Exception("即梦服务未配置或已禁用")

    print(f"🎬 【即梦处理】开始处理: {action}, 用户: {user_id}")
    print(f"🎬 【即梦处理】配置: base_url={config.base_url}")
    print(
        f"🎬 【即梦处理】请求: prompt={request.prompt[:50]}..., duration={request.duration}"
    )

    # 计算积分消耗
    credits_cost = config.get_credits_cost(request.duration)

    # 验证积分
    if not validate_user_credits(user_id, credits_cost):
        raise Exception("积分不足")

    # 扣除积分
    deduct_user_credits(user_id, credits_cost, f"即梦-{action}")

    # 创建任务记录
    task = JimengTask.create_task(
        user_id=user_id,
        action=action,
        prompt=request.prompt,
        duration=request.duration,
        aspect_ratio=request.aspect_ratio,
        cfg_scale=request.cfg_scale,
        credits_cost=credits_cost,
        image_url=request.image_url if action == "IMAGE_TO_VIDEO" else None,
        input_image=request.image if action == "IMAGE_TO_VIDEO" else None,
        properties={
            "serviceType": "jimeng",
            "action": action,
            "duration": request.duration,
        },
    )

    try:
        # 调用API
        client = JimengApiClient(config)
        api_response = await client.generate_video(request)

        # 更新任务状态
        task.update_from_api_response(api_response)

        return task

    except Exception as e:
        print(f"❌ 【即梦处理】生成失败: {e}")
        import traceback

        traceback.print_exc()

        # 发生错误时退还积分
        add_user_credits(user_id, credits_cost, f"即梦-{action}-error-refund", task.id)
        task.update_status("failed")
        task.fail_reason = str(e)
        raise


# ======================== 任务清理 ========================


def cleanup_old_tasks(days: int = 30):
    """清理旧任务记录"""
    from open_webui.models.jimeng import JimengTask
    from open_webui.internal.db import get_db
    from datetime import timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    with get_db() as db:
        deleted_count = (
            db.query(JimengTask).filter(JimengTask.created_at < cutoff_date).delete()
        )
        db.commit()
        return deleted_count


# ======================== 错误处理 ========================


class JimengApiError(Exception):
    """即梦API错误"""

    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class JimengInsufficientCreditsError(Exception):
    """积分不足错误"""

    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient credits: required {required}, available {available}"
        )


class JimengConfigError(Exception):
    """配置错误"""

    pass


class JimengVideoError(Exception):
    """视频处理错误"""

    pass
