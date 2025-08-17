"""
Midjourney 工具类
包含API客户端、积分管理、Prompt构建等工具
"""

import httpx
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from open_webui.models.midjourney import MJConfig, MJCredit, MJGenerateRequest


class MJApiClient:
    """Midjourney API客户端"""

    def __init__(self, config: MJConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _get_mode_url(self, mode: str = "fast") -> str:
        """根据模式获取URL"""
        if mode == "fast":
            return f"{self.base_url}/mj"
        elif mode == "turbo":
            return f"{self.base_url}/mj-turbo/mj"
        elif mode == "relax":
            return f"{self.base_url}/mj-relax/mj"
        else:
            return f"{self.base_url}/mj"

    def build_prompt(self, request: MJGenerateRequest) -> str:
        """构建完整的MJ Prompt"""
        prompt = request.prompt.strip()

        # 🔥 调试信息：检查参考图片数据
        if hasattr(request, "reference_images") and request.reference_images:
            print(f"🖼️ 【调试】参考图片数量: {len(request.reference_images)}")
            for i, img in enumerate(request.reference_images):
                print(
                    f"🖼️ 【调试】图片{i+1}: 类型={img.type}, 权重={img.weight}, Base64长度={len(img.base64) if img.base64 else 0}"
                )
        else:
            print("🖼️ 【调试】没有参考图片数据")

        # 添加高级参数
        if request.advanced_params:
            params = request.advanced_params

            # 图片比例
            if (
                hasattr(params, "aspect_ratio")
                and params.aspect_ratio
                and params.aspect_ratio != "custom"
            ):
                prompt += f" --ar {params.aspect_ratio}"
            elif (
                hasattr(params, "aspectRatio")
                and params.aspectRatio
                and params.aspectRatio != "custom"
            ):
                prompt += f" --ar {params.aspectRatio}"
            elif hasattr(params, "custom_aspect_ratio") and params.custom_aspect_ratio:
                prompt += f" --ar {params.custom_aspect_ratio['width']}:{params.custom_aspect_ratio['height']}"
            elif hasattr(params, "customAspectRatio") and params.customAspectRatio:
                prompt += f" --ar {params.customAspectRatio['width']}:{params.customAspectRatio['height']}"

            # 混乱程度
            if params.chaos is not None and params.chaos > 0:
                prompt += f" --chaos {params.chaos}"

            # 风格化程度 - 显示所有stylize设置，不只是非默认值
            if params.stylize is not None:
                prompt += f" --stylize {params.stylize}"

            # 奇异程度
            if params.weird is not None and params.weird > 0:
                prompt += f" --weird {params.weird}"

            # 种子值
            if params.seed is not None:
                prompt += f" --seed {params.seed}"

            # 质量 - 显示所有质量设置，不只是非默认值
            if params.quality is not None:
                # 格式化数字：整数不显示小数点，小数保持原样
                quality_str = (
                    str(int(params.quality))
                    if params.quality == int(params.quality)
                    else str(params.quality)
                )
                prompt += f" --q {quality_str}"

            # 版本
            if params.version:
                # 去掉 'v' 前缀，因为 --v 参数不需要 'v' 前缀
                version_number = (
                    params.version.replace("v", "")
                    if isinstance(params.version, str)
                    else params.version
                )
                prompt += f" --v {version_number}"

            # 平铺模式
            if params.tile:
                prompt += " --tile"

        # 🔥 添加参考图片参数到prompt（备用方案）
        # 注意：大多数MJ API通过base64Array处理图片，但某些情况下可能需要prompt参数
        if hasattr(request, "reference_images") and request.reference_images:
            # 对于需要在prompt中指定图片URL的API，这里可以扩展
            # 目前主要通过base64Array发送，这里保留扩展性
            pass

        # 添加负面提示词
        if request.negative_prompt:
            prompt += f" --no {request.negative_prompt}"

        print(f"🖼️ 【构建完成】最终prompt: {prompt}")
        return prompt

    async def submit_imagine(self, data: dict) -> dict:
        """提交Imagine任务"""
        url = f"{self._get_mode_url(data.get('mode', 'fast'))}/submit/imagine"

        # 🔥 调试信息：检查发送到MJ API的数据
        print(f"🚀 【MJ API调试】发送到 {url}")
        print(f"🚀 【MJ API调试】请求数据keys: {list(data.keys())}")
        if "base64Array" in data:
            print(f"🚀 【MJ API调试】base64Array数量: {len(data['base64Array'])}")
        if "imageWeights" in data:
            print(f"🚀 【MJ API调试】imageWeights: {data['imageWeights']}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=self.headers)
            print(f"🚀 【MJ API调试】响应状态: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            print(f"🚀 【MJ API调试】响应结果: {result}")
            return result

    async def submit_blend(self, data: dict) -> dict:
        """提交Blend任务"""
        url = f"{self._get_mode_url('fast')}/submit/blend"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def submit_describe(self, data: dict) -> dict:
        """提交Describe任务"""
        url = f"{self._get_mode_url('fast')}/submit/describe"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def submit_action(self, data: dict) -> dict:
        """提交Action任务"""
        url = f"{self._get_mode_url('fast')}/submit/action"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def submit_modal(self, data: dict) -> dict:
        """提交Modal任务"""
        url = f"{self._get_mode_url('fast')}/submit/modal"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        url = f"{self._get_mode_url('fast')}/task/{task_id}/fetch"

        print(f"🔍 查询任务状态 - URL: {url}")
        print(f"🔍 查询任务状态 - TaskID: {task_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            print(f"🔍 API响应状态码: {response.status_code}")

            response.raise_for_status()
            result = response.json()

            print(f"🔍 API响应内容: {result}")
            return result

    async def get_image_seed(self, task_id: str) -> dict:
        """获取图片seed"""
        url = f"{self._get_mode_url('fast')}/task/{task_id}/image-seed"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()


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
                desc=f"Midjourney: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "midjourney", "credits": amount},
            ),
        )

        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        print(f"Error deducting credits: {e}")
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
                desc=f"Midjourney: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "midjourney", "credits": amount},
            ),
        )

        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        print(f"Error adding credits: {e}")
        return 0.0


# ======================== 管理员功能 ========================


def admin_add_credits_to_user(
    admin_id: str, target_user_id: str, amount: int, reason: str = ""
) -> float:
    """管理员给用户充值积分"""
    full_reason = (
        f"Admin {admin_id} added credits: {reason}"
        if reason
        else f"Admin {admin_id} added credits"
    )
    return add_user_credits(target_user_id, amount, full_reason)


def admin_deduct_credits_from_user(
    admin_id: str, target_user_id: str, amount: int, reason: str = ""
) -> float:
    """管理员扣除用户积分"""
    full_reason = (
        f"Admin {admin_id} deducted credits: {reason}"
        if reason
        else f"Admin {admin_id} deducted credits"
    )
    return deduct_user_credits(target_user_id, amount, full_reason)


# ======================== 统计功能 ========================


def get_system_mj_stats() -> dict:
    """获取系统MJ统计"""
    from open_webui.models.midjourney import MJTask
    from open_webui.internal.db import get_db
    from sqlalchemy import func

    with get_db() as db:
        # 总任务数
        total_tasks = db.query(MJTask).count()

        # 成功任务数
        success_tasks = db.query(MJTask).filter(MJTask.status == "SUCCESS").count()

        # 今日任务数
        today = datetime.utcnow().date()
        today_tasks = (
            db.query(MJTask).filter(func.date(MJTask.created_at) == today).count()
        )

        # 各状态任务数
        status_stats = (
            db.query(MJTask.status, func.count(MJTask.id)).group_by(MJTask.status).all()
        )

        # 各模式使用统计
        mode_stats = (
            db.query(MJTask.mode, func.count(MJTask.id)).group_by(MJTask.mode).all()
        )

        return {
            "total_tasks": total_tasks,
            "success_tasks": success_tasks,
            "today_tasks": today_tasks,
            "success_rate": (
                round(success_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
            ),
            "status_distribution": dict(status_stats),
            "mode_distribution": dict(mode_stats),
        }


def get_user_mj_stats(user_id: str) -> dict:
    """获取用户MJ统计"""
    from open_webui.models.midjourney import MJTask
    from open_webui.internal.db import get_db
    from sqlalchemy import func

    with get_db() as db:
        # 用户任务数
        user_tasks = db.query(MJTask).filter(MJTask.user_id == user_id).count()

        # 用户成功任务数
        user_success = (
            db.query(MJTask)
            .filter(MJTask.user_id == user_id, MJTask.status == "SUCCESS")
            .count()
        )

        # 用户今日任务数
        today = datetime.utcnow().date()
        user_today = (
            db.query(MJTask)
            .filter(MJTask.user_id == user_id, func.date(MJTask.created_at) == today)
            .count()
        )

        # 用户积分余额
        balance = get_user_credit_balance(user_id)

        # 用户总消费积分
        total_spent = (
            db.query(func.sum(MJTask.credits_cost))
            .filter(MJTask.user_id == user_id)
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


# ======================== 任务清理 ========================


def cleanup_old_tasks(days: int = 30):
    """清理旧任务记录"""
    from open_webui.models.midjourney import MJTask
    from open_webui.internal.db import get_db
    from datetime import timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    with get_db() as db:
        deleted_count = (
            db.query(MJTask).filter(MJTask.created_at < cutoff_date).delete()
        )
        db.commit()
        return deleted_count


# ======================== 错误处理 ========================


class MJApiError(Exception):
    """MJ API错误"""

    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class MJInsufficientCreditsError(Exception):
    """积分不足错误"""

    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient credits: required {required}, available {available}"
        )


class MJConfigError(Exception):
    """配置错误"""

    pass
