"""
DreamWork (即梦) 工具类
包含API客户端、积分管理、任务处理等工具
"""

import httpx
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import base64

from open_webui.models.dreamwork import (
    DreamWorkConfig,
    DreamWorkTask,
    DreamWorkGenerateRequest,
)
from open_webui.services.file_manager import get_file_manager
from open_webui.internal.db import get_db


class DreamWorkApiClient:
    """DreamWork API客户端"""

    def __init__(self, config: DreamWorkConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_text_to_image(self, request: DreamWorkGenerateRequest) -> dict:
        """文生图"""
        url = f"{self.base_url}/v1/images/generations"

        # 根据请求的模型，确保使用正确的模型
        model_to_use = (
            request.model if request.model else self.config.text_to_image_model
        )
        if not model_to_use or "t2i" not in model_to_use:
            print(
                f"⚠️ 【DreamWork API】模型可能不正确: {model_to_use}，强制使用文生图模型"
            )
            model_to_use = self.config.text_to_image_model

        # 构建符合DreamWork API文档的请求数据
        request_data = {
            "model": model_to_use,
            "prompt": request.prompt.strip(),
            "size": request.size or "1024x1024",
            "response_format": request.response_format or "url",
        }

        # 添加可选参数 - 只在有值时添加
        if request.guidance_scale is not None and request.guidance_scale > 0:
            request_data["guidance_scale"] = float(request.guidance_scale)

        if request.seed is not None and request.seed > 0:
            request_data["seed"] = int(request.seed)

        if request.watermark is not None:
            request_data["watermark"] = bool(request.watermark)

        print(f"🎨 【DreamWork API】文生图请求URL: {url}")
        print(
            f"🎨 【DreamWork API】请求参数: {json.dumps(request_data, ensure_ascii=False)}"
        )

        # 确保headers正确
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OpenWebUI-DreamWork/1.0",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                print(f"🎨 【DreamWork API】发送请求到: {url}")
                response = await client.post(url, json=request_data, headers=headers)
                print(f"🎨 【DreamWork API】响应状态: {response.status_code}")
                print(f"🎨 【DreamWork API】响应头: {dict(response.headers)}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"🎨 【DreamWork API】响应成功: {result}")
                    return result
                else:
                    error_text = response.text
                    print(
                        f"🎨 【DreamWork API】响应错误 ({response.status_code}): {error_text}"
                    )

                    # 尝试解析错误信息
                    try:
                        error_json = response.json()
                        print(f"🎨 【DreamWork API】错误详情JSON: {error_json}")

                        # 提取具体错误信息
                        error_message = "API请求失败"
                        if "error" in error_json:
                            if isinstance(error_json["error"], dict):
                                error_message = error_json["error"].get(
                                    "message", str(error_json["error"])
                                )
                            else:
                                error_message = str(error_json["error"])
                        elif "message" in error_json:
                            error_message = error_json["message"]
                        elif "detail" in error_json:
                            error_message = error_json["detail"]

                        raise ValueError(
                            f"DreamWork API错误 ({response.status_code}): {error_message}"
                        )
                    except json.JSONDecodeError:
                        print(f"🎨 【DreamWork API】无法解析错误响应为JSON")
                        raise ValueError(
                            f"DreamWork API错误 ({response.status_code}): {error_text[:200]}"
                        )

        except httpx.TimeoutException:
            raise ValueError("DreamWork API请求超时，请稍后重试")
        except httpx.ConnectError as e:
            raise ValueError(f"无法连接到DreamWork API: {e}")
        except Exception as e:
            if "DreamWork API错误" in str(e):
                raise
            print(f"🎨 【DreamWork API】请求异常: {e}")
            import traceback

            traceback.print_exc()
            raise ValueError(f"DreamWork API请求失败: {e}")

    async def generate_image_to_image(self, request: DreamWorkGenerateRequest) -> dict:
        """图生图"""
        url = f"{self.base_url}/v1/images/generations"

        # 验证输入数据
        if not request.image:
            raise ValueError("图生图模式需要输入图片")

        # 验证和清理base64数据格式
        image_data = request.image.strip()
        print(f"🎨 【DreamWork API】原始图片数据长度: {len(image_data)}字符")
        print(f"🎨 【DreamWork API】图片数据前缀: {image_data[:50]}...")

        # 处理data URL格式
        if image_data.startswith("data:"):
            if "," in image_data:
                header, image_data = image_data.split(",", 1)
                print(f"🎨 【DreamWork API】移除data URL前缀: {header}")
            else:
                raise ValueError("无效的data URL格式")

        # 清理可能的空白字符
        image_data = (
            image_data.replace("\n", "")
            .replace("\r", "")
            .replace(" ", "")
            .replace("\t", "")
        )

        # 验证base64数据长度
        if len(image_data) < 100:
            raise ValueError(f"图片数据太短: {len(image_data)}字符")

        # 验证base64格式
        try:
            import base64

            # 测试整个数据的解码，而不仅仅是前100字符
            decoded_data = base64.b64decode(image_data)
            print(
                f"🎨 【DreamWork API】成功解码图片，解码后大小: {len(decoded_data)}字节"
            )

            # 验证图片文件头
            if decoded_data[:4] == b"\x89PNG":
                print("🎨 【DreamWork API】检测到PNG图片")
            elif decoded_data[:2] == b"\xff\xd8":
                print("🎨 【DreamWork API】检测到JPEG图片")
            elif decoded_data[:6] in [b"GIF87a", b"GIF89a"]:
                print("🎨 【DreamWork API】检测到GIF图片")
            elif decoded_data[:4] == b"RIFF" and decoded_data[8:12] == b"WEBP":
                print("🎨 【DreamWork API】检测到WebP图片")
            else:
                print(
                    f"🎨 【DreamWork API】警告: 未识别的图片格式，文件头: {decoded_data[:8].hex()}"
                )
        except Exception as e:
            raise ValueError(f"无效的base64格式: {e}")

        # 根据请求的模型，确保使用正确的模型
        model_to_use = (
            request.model if request.model else self.config.image_to_image_model
        )
        if not model_to_use or "i2i" not in model_to_use:
            print(
                f"⚠️ 【DreamWork API】模型可能不正确: {model_to_use}，强制使用图生图模型"
            )
            model_to_use = self.config.image_to_image_model

        # 构建符合DreamWork API文档的请求数据
        request_data = {
            "model": model_to_use,
            "prompt": request.prompt.strip(),
            "image": image_data,
            "size": request.size or "1024x1024",
            "response_format": request.response_format or "url",
        }

        # 添加可选参数 - 只在有值时添加
        if request.guidance_scale is not None and request.guidance_scale > 0:
            request_data["guidance_scale"] = float(request.guidance_scale)

        if request.seed is not None and request.seed > 0:
            request_data["seed"] = int(request.seed)

        if request.watermark is not None:
            request_data["watermark"] = bool(request.watermark)

        print(f"🎨 【DreamWork API】图生图请求URL: {url}")
        print(f"🎨 【DreamWork API】请求参数:")
        for key, value in request_data.items():
            if key == "image":
                print(f"  - {key}: [base64 data, {len(value)} chars]")
            else:
                print(f"  - {key}: {value}")

        # 确保headers正确
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OpenWebUI-DreamWork/1.0",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                print(f"🎨 【DreamWork API】发送请求到: {url}")
                response = await client.post(url, json=request_data, headers=headers)
                print(f"🎨 【DreamWork API】响应状态: {response.status_code}")
                print(f"🎨 【DreamWork API】响应头: {dict(response.headers)}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"🎨 【DreamWork API】响应成功: {result}")
                    return result
                else:
                    error_text = response.text
                    print(
                        f"🎨 【DreamWork API】响应错误 ({response.status_code}): {error_text}"
                    )

                    # 尝试解析错误信息
                    try:
                        error_json = response.json()
                        print(f"🎨 【DreamWork API】错误详情JSON: {error_json}")

                        # 提取具体错误信息
                        error_message = "API请求失败"
                        if "error" in error_json:
                            if isinstance(error_json["error"], dict):
                                error_message = error_json["error"].get(
                                    "message", str(error_json["error"])
                                )
                            else:
                                error_message = str(error_json["error"])
                        elif "message" in error_json:
                            error_message = error_json["message"]
                        elif "detail" in error_json:
                            error_message = error_json["detail"]

                        raise ValueError(
                            f"DreamWork API错误 ({response.status_code}): {error_message}"
                        )
                    except json.JSONDecodeError:
                        print(f"🎨 【DreamWork API】无法解析错误响应为JSON")
                        raise ValueError(
                            f"DreamWork API错误 ({response.status_code}): {error_text[:200]}"
                        )

        except httpx.TimeoutException:
            raise ValueError("DreamWork API请求超时，请稍后重试")
        except httpx.ConnectError as e:
            raise ValueError(f"无法连接到DreamWork API: {e}")
        except Exception as e:
            if "DreamWork API错误" in str(e):
                raise
            print(f"🎨 【DreamWork API】请求异常: {e}")
            import traceback

            traceback.print_exc()
            raise ValueError(f"DreamWork API请求失败: {e}")


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
                desc=f"DreamWork: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "dreamwork", "credits": amount},
            ),
        )

        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        print(f"Error deducting DreamWork credits: {e}")
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
                desc=f"DreamWork: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "dreamwork", "credits": amount},
            ),
        )

        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        print(f"Error adding DreamWork credits: {e}")
        return 0.0


# ======================== 管理员功能 ========================


def admin_add_credits_to_user(
    admin_id: str, target_user_id: str, amount: int, reason: str = ""
) -> float:
    """管理员给用户充值积分"""
    full_reason = (
        f"Admin {admin_id} added DreamWork credits: {reason}"
        if reason
        else f"Admin {admin_id} added DreamWork credits"
    )
    return add_user_credits(target_user_id, amount, full_reason)


def admin_deduct_credits_from_user(
    admin_id: str, target_user_id: str, amount: int, reason: str = ""
) -> float:
    """管理员扣除用户积分"""
    full_reason = (
        f"Admin {admin_id} deducted DreamWork credits: {reason}"
        if reason
        else f"Admin {admin_id} deducted DreamWork credits"
    )
    return deduct_user_credits(target_user_id, amount, full_reason)


# ======================== 统计功能 ========================


def get_system_dreamwork_stats() -> dict:
    """获取系统DreamWork统计"""
    from open_webui.models.dreamwork import DreamWorkTask
    from open_webui.internal.db import get_db
    from sqlalchemy import func

    with get_db() as db:
        # 总任务数
        total_tasks = db.query(DreamWorkTask).count()

        # 成功任务数
        success_tasks = (
            db.query(DreamWorkTask).filter(DreamWorkTask.status == "SUCCESS").count()
        )

        # 今日任务数
        today = datetime.utcnow().date()
        today_tasks = (
            db.query(DreamWorkTask)
            .filter(func.date(DreamWorkTask.created_at) == today)
            .count()
        )

        # 各状态任务数
        status_stats = (
            db.query(DreamWorkTask.status, func.count(DreamWorkTask.id))
            .group_by(DreamWorkTask.status)
            .all()
        )

        # 各动作类型统计
        action_stats = (
            db.query(DreamWorkTask.action, func.count(DreamWorkTask.id))
            .group_by(DreamWorkTask.action)
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


def get_user_dreamwork_stats(user_id: str) -> dict:
    """获取用户DreamWork统计"""
    from open_webui.models.dreamwork import DreamWorkTask
    from open_webui.internal.db import get_db
    from sqlalchemy import func

    with get_db() as db:
        # 用户任务数
        user_tasks = (
            db.query(DreamWorkTask).filter(DreamWorkTask.user_id == user_id).count()
        )

        # 用户成功任务数
        user_success = (
            db.query(DreamWorkTask)
            .filter(DreamWorkTask.user_id == user_id, DreamWorkTask.status == "SUCCESS")
            .count()
        )

        # 用户今日任务数
        today = datetime.utcnow().date()
        user_today = (
            db.query(DreamWorkTask)
            .filter(
                DreamWorkTask.user_id == user_id,
                func.date(DreamWorkTask.created_at) == today,
            )
            .count()
        )

        # 用户积分余额
        balance = get_user_credit_balance(user_id)

        # 用户总消费积分
        total_spent = (
            db.query(func.sum(DreamWorkTask.credits_cost))
            .filter(DreamWorkTask.user_id == user_id)
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


async def process_dreamwork_generation(
    user_id: str, request: DreamWorkGenerateRequest, action: str = "TEXT_TO_IMAGE"
) -> DreamWorkTask:
    """处理DreamWork生成任务"""
    config = DreamWorkConfig.get_config()
    if not config or not config.enabled:
        raise Exception("DreamWork service not configured or disabled")

    print(f"🎨 【DreamWork处理】开始处理: {action}, 用户: {user_id}")
    print(
        f"🎨 【DreamWork处理】配置: base_url={config.base_url}, model={request.model}"
    )
    print(
        f"🎨 【DreamWork处理】请求: prompt={request.prompt[:50]}..., size={request.size}"
    )

    # 验证模型
    if action == "TEXT_TO_IMAGE" and request.model != config.text_to_image_model:
        print(
            f"⚠️ 【DreamWork处理】模型不匹配: 请求={request.model}, 配置={config.text_to_image_model}"
        )
        # 使用配置中的模型
        request.model = config.text_to_image_model
    elif action == "IMAGE_TO_IMAGE" and request.model != config.image_to_image_model:
        print(
            f"⚠️ 【DreamWork处理】模型不匹配: 请求={request.model}, 配置={config.image_to_image_model}"
        )
        # 使用配置中的模型
        request.model = config.image_to_image_model

    # 验证积分
    if not validate_user_credits(user_id, config.credits_per_generation):
        raise Exception("Insufficient credits")

    # 扣除积分
    deduct_user_credits(user_id, config.credits_per_generation, f"DreamWork-{action}")

    # 创建任务记录
    task = DreamWorkTask.create_task(
        user_id=user_id,
        action=action,
        prompt=request.prompt,
        model=request.model,
        size=request.size,
        guidance_scale=request.guidance_scale,
        seed=request.seed,
        watermark=request.watermark,
        credits_cost=config.credits_per_generation,
        input_image=request.image if action == "IMAGE_TO_IMAGE" else None,
        properties={
            "serviceType": "dreamwork",
            "model": request.model,
            "size": request.size,
        },
    )

    try:
        # 调用API
        client = DreamWorkApiClient(config)

        if action == "TEXT_TO_IMAGE":
            api_response = await client.generate_text_to_image(request)
        else:  # IMAGE_TO_IMAGE
            api_response = await client.generate_image_to_image(request)

        # 更新任务状态
        task.update_from_api_response(api_response)

        # 🔥 如果任务成功且有图片URL，自动上传到云存储
        if task.status == "SUCCESS" and task.image_url:
            try:
                file_manager = get_file_manager()
                success, message, file_record = (
                    await file_manager.save_generated_content(
                        user_id=user_id,
                        file_url=task.image_url,
                        filename=f"dreamwork_{task.id}.jpg",
                        file_type="image",
                        source_type="dreamwork",
                        source_task_id=task.id,
                        metadata={
                            "prompt": task.prompt,
                            "model": task.model,
                            "size": task.size,
                            "guidance_scale": task.guidance_scale,
                            "action": action,
                            "original_url": task.image_url,
                        },
                    )
                )
                if success and file_record and file_record.cloud_url:
                    # 更新任务记录中的云存储URL
                    with get_db() as update_db:
                        update_task = (
                            update_db.query(DreamWorkTask)
                            .filter(DreamWorkTask.id == task.id)
                            .first()
                        )
                        if update_task:
                            update_task.cloud_image_url = file_record.cloud_url
                            update_db.commit()
                    print(
                        f"☁️ 【云存储】DreamWork{action}上传成功，已更新URL: {task.id}"
                    )
                else:
                    print(
                        f"☁️ 【云存储】DreamWork{action}上传失败: {task.id} - {message}"
                    )
            except Exception as upload_error:
                print(
                    f"☁️ 【云存储】DreamWork{action}自动上传异常: {task.id} - {upload_error}"
                )

        return task

    except Exception as e:
        print(f"❌ 【DreamWork处理】生成失败: {e}")
        import traceback

        traceback.print_exc()

        # 发生错误时退还积分
        add_user_credits(
            user_id,
            config.credits_per_generation,
            f"DreamWork-{action}-error-refund",
            task.id,
        )
        task.update_status("FAILURE")
        task.fail_reason = str(e)
        raise


# ======================== 任务清理 ========================


def cleanup_old_tasks(days: int = 30):
    """清理旧任务记录"""
    from open_webui.models.dreamwork import DreamWorkTask
    from open_webui.internal.db import get_db
    from datetime import timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    with get_db() as db:
        deleted_count = (
            db.query(DreamWorkTask)
            .filter(DreamWorkTask.created_at < cutoff_date)
            .delete()
        )
        db.commit()
        return deleted_count


# ======================== 图片处理工具 ========================


def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为base64"""
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            return base64.b64encode(image_data).decode("utf-8")
    except Exception as e:
        raise Exception(f"Failed to encode image: {str(e)}")


def decode_base64_to_image(base64_data: str, output_path: str):
    """将base64数据解码为图片文件"""
    try:
        # 去掉可能的data:image前缀
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]

        image_data = base64.b64decode(base64_data)
        with open(output_path, "wb") as image_file:
            image_file.write(image_data)
    except Exception as e:
        raise Exception(f"Failed to decode image: {str(e)}")


def validate_image_format(base64_data: str) -> bool:
    """验证图片格式是否支持"""
    try:
        if "," in base64_data:
            header, data = base64_data.split(",", 1)
            # 检查MIME类型
            if "image/" in header:
                return True
        else:
            # 尝试解码验证
            base64.b64decode(base64_data)
            return True
        return False
    except Exception:
        return False


# ======================== 错误处理 ========================


class DreamWorkApiError(Exception):
    """DreamWork API错误"""

    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class DreamWorkInsufficientCreditsError(Exception):
    """积分不足错误"""

    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient credits: required {required}, available {available}"
        )


class DreamWorkConfigError(Exception):
    """配置错误"""

    pass


class DreamWorkImageError(Exception):
    """图片处理错误"""

    pass
