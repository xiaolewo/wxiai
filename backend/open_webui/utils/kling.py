"""
可灵视频生成工具类
包含API客户端、积分管理、任务处理等工具
"""

import httpx
import asyncio
import json
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime

from open_webui.models.kling import KlingConfig, KlingTask, KlingGenerateRequest


class KlingApiClient:
    """可灵API客户端"""

    def __init__(self, config: KlingConfig):
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
            self.api_path_prefix = config.detected_api_path.replace(
                "/text2video", ""
            ).replace("/image2video", "")
            print(f"🎬 【可灵客户端】使用已检测的API路径前缀: {self.api_path_prefix}")
        else:
            # 使用默认路径（向后兼容）
            self.api_path_prefix = "/kling/v1/videos"
            print(f"🎬 【可灵客户端】使用默认API路径前缀: {self.api_path_prefix}")

    def _get_api_url(self, endpoint: str) -> str:
        """构建完整的API URL"""
        if self.config.detected_api_path:
            # 使用检测到的完整路径，替换端点部分
            base_path = self.config.detected_api_path.replace(
                "/text2video", ""
            ).replace("/image2video", "")
            url = f"{self.base_url}{base_path}/{endpoint}"
        else:
            # 使用默认路径
            url = f"{self.base_url}{self.api_path_prefix}/{endpoint}"

        print(f"🎬 【可灵客户端】构建API URL: {url}")
        return url

    async def generate_text_to_video(self, request: KlingGenerateRequest) -> dict:
        """文生视频"""
        url = self._get_api_url("text2video")

        # 构建请求数据
        request_data = {
            "model_name": request.model_name or self.config.text_to_video_model,
            "prompt": request.prompt.strip(),
            "mode": request.mode or "std",
            "duration": request.duration or "5",
            "aspect_ratio": request.aspect_ratio or "16:9",
        }

        # 添加可选参数
        if request.negative_prompt:
            request_data["negative_prompt"] = request.negative_prompt.strip()

        if request.cfg_scale is not None:
            request_data["cfg_scale"] = float(request.cfg_scale)

        if request.camera_control:
            request_data["camera_control"] = request.camera_control.dict(
                exclude_none=True
            )

        if request.callback_url:
            request_data["callback_url"] = request.callback_url

        if request.external_task_id:
            request_data["external_task_id"] = request.external_task_id

        print(f"🎬 【可灵API】文生视频请求URL: {url}")
        print(
            f"🎬 【可灵API】请求头: {json.dumps({k: '***' if k == 'Authorization' else v for k, v in self.headers.items()}, ensure_ascii=False)}"
        )
        print(f"🎬 【可灵API】请求参数: {json.dumps(request_data, ensure_ascii=False)}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"🎬 【可灵API】开始发送HTTP请求到: {url}")
                response = await client.post(
                    url, json=request_data, headers=self.headers
                )
                print(f"🎬 【可灵API】响应状态: {response.status_code}")
                print(f"🎬 【可灵API】响应头: {dict(response.headers)}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"🎬 【可灵API】响应成功: {result}")
                    return result
                else:
                    error_text = response.text
                    print(
                        f"🎬 【可灵API】响应错误 ({response.status_code}): {error_text}"
                    )

                    try:
                        error_json = response.json()
                        error_message = error_json.get("message", "API请求失败")
                        print(f"🎬 【可灵API】解析错误JSON: {error_json}")
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_message}"
                        )
                    except json.JSONDecodeError:
                        print(f"🎬 【可灵API】无法解析错误响应为JSON")
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_text[:200]}"
                        )

        except httpx.TimeoutException:
            raise ValueError("可灵API请求超时，请稍后重试")
        except httpx.ConnectError as e:
            raise ValueError(f"无法连接到可灵API: {e}")
        except Exception as e:
            if "可灵API错误" in str(e):
                raise
            print(f"🎬 【可灵API】请求异常: {e}")
            import traceback

            traceback.print_exc()
            raise ValueError(f"可灵API请求失败: {e}")

    async def generate_image_to_video(self, request: KlingGenerateRequest) -> dict:
        """图生视频"""
        url = self._get_api_url("image2video")

        # 验证输入数据
        if not request.image:
            raise ValueError("图生视频模式需要输入图片")

        # 处理图片数据 - 注意：可灵API要求纯base64，不要data URL前缀
        image_data = self._process_image_data(request.image, "输入图片")

        # 构建请求数据
        request_data = {
            "model_name": request.model_name or self.config.image_to_video_model,
            "image": image_data,
            "mode": request.mode or "std",
            "duration": request.duration or "5",
        }

        # 添加可选参数
        if request.prompt:
            request_data["prompt"] = request.prompt.strip()

        if request.negative_prompt:
            request_data["negative_prompt"] = request.negative_prompt.strip()

        if request.cfg_scale is not None:
            request_data["cfg_scale"] = float(request.cfg_scale)

        if request.image_tail:
            request_data["image_tail"] = self._process_image_data(
                request.image_tail, "尾帧图片"
            )

        if request.static_mask:
            request_data["static_mask"] = self._process_image_data(
                request.static_mask, "静态笔刷"
            )

        if request.dynamic_masks:
            dynamic_masks_data = []
            for i, dm in enumerate(request.dynamic_masks):
                mask_data = self._process_image_data(dm.mask, f"动态笔刷{i+1}")
                trajectories = [{"x": p.x, "y": p.y} for p in dm.trajectories]
                dynamic_masks_data.append(
                    {"mask": mask_data, "trajectories": trajectories}
                )
            request_data["dynamic_masks"] = dynamic_masks_data

        if request.camera_control:
            request_data["camera_control"] = request.camera_control.dict(
                exclude_none=True
            )

        if request.callback_url:
            request_data["callback_url"] = request.callback_url

        if request.external_task_id:
            request_data["external_task_id"] = request.external_task_id

        print(f"🎬 【可灵API】图生视频请求URL: {url}")
        print(f"🎬 【可灵API】请求参数:")
        for key, value in request_data.items():
            if key in ["image", "image_tail", "static_mask"] or "mask" in key:
                print(f"  - {key}: [base64 data, {len(str(value))} chars]")
            else:
                print(f"  - {key}: {value}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url, json=request_data, headers=self.headers
                )
                print(f"🎬 【可灵API】响应状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"🎬 【可灵API】响应成功: {result}")
                    return result
                else:
                    error_text = response.text
                    print(
                        f"🎬 【可灵API】响应错误 ({response.status_code}): {error_text}"
                    )

                    try:
                        error_json = response.json()
                        error_message = error_json.get("message", "API请求失败")
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_message}"
                        )
                    except json.JSONDecodeError:
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_text[:200]}"
                        )

        except httpx.TimeoutException:
            raise ValueError("可灵API请求超时，请稍后重试")
        except httpx.ConnectError as e:
            raise ValueError(f"无法连接到可灵API: {e}")
        except Exception as e:
            if "可灵API错误" in str(e):
                raise
            print(f"🎬 【可灵API】请求异常: {e}")
            import traceback

            traceback.print_exc()
            raise ValueError(f"可灵API请求失败: {e}")

    async def generate_multi_image_to_video(
        self, request: KlingGenerateRequest
    ) -> dict:
        """多图参考生视频"""
        url = self._get_api_url("multi-image2video")

        # 验证模型版本
        if request.model_name != "kling-v1-6":
            raise ValueError("多图参考生视频只支持 kling-v1-6 模型")

        # 验证图片数量
        if not request.image_list or len(request.image_list) > 4:
            raise ValueError("多图参考需要1-4张图片")

        # 处理图片数据
        processed_images = []
        for i, img_data in enumerate(request.image_list):
            if not isinstance(img_data, dict) or "image" not in img_data:
                raise ValueError(f"第{i+1}张图片数据格式错误")

            processed_img = self._process_image_data(
                img_data["image"], f"参考图片{i+1}"
            )
            processed_images.append({"image": processed_img})

        # 构建请求数据
        request_data = {
            "model_name": "kling-v1-6",
            "image_list": processed_images,
            "mode": request.mode or "std",
            "duration": request.duration or "5",
            "aspect_ratio": request.aspect_ratio or "16:9",
        }

        # 添加可选参数
        if request.prompt:
            request_data["prompt"] = request.prompt.strip()

        if request.negative_prompt:
            request_data["negative_prompt"] = request.negative_prompt.strip()

        if request.callback_url:
            request_data["callback_url"] = request.callback_url

        if request.external_task_id:
            request_data["external_task_id"] = request.external_task_id

        print(f"🎬 【可灵API】多图生视频请求URL: {url}")
        print(f"🎬 【可灵API】图片数量: {len(processed_images)}")
        print(f"🎬 【可灵API】请求参数:")
        for key, value in request_data.items():
            if key == "image_list":
                print(f"  - {key}: [{len(value)} images with base64 data]")
            else:
                print(f"  - {key}: {value}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url, json=request_data, headers=self.headers
                )
                print(f"🎬 【可灵API】响应状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"🎬 【可灵API】多图生成响应成功: {result}")
                    return result
                else:
                    error_text = response.text
                    print(
                        f"🎬 【可灵API】响应错误 ({response.status_code}): {error_text}"
                    )

                    try:
                        error_json = response.json()
                        error_message = error_json.get("message", "API请求失败")
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_message}"
                        )
                    except json.JSONDecodeError:
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_text[:200]}"
                        )

        except httpx.TimeoutException:
            raise ValueError("可灵多图API请求超时，请稍后重试")
        except httpx.ConnectError as e:
            raise ValueError(f"无法连接到可灵多图API: {e}")
        except Exception as e:
            if "可灵API错误" in str(e):
                raise
            print(f"🎬 【可灵API】多图请求异常: {e}")
            import traceback

            traceback.print_exc()
            raise ValueError(f"可灵多图API请求失败: {e}")

    async def query_task(self, task_id: str) -> dict:
        """查询任务状态"""
        # 任务查询通常使用text2video路径
        if (
            self.config.detected_api_path
            and "/text2video" in self.config.detected_api_path
        ):
            url = f"{self.base_url}{self.config.detected_api_path}/{task_id}"
        else:
            url = self._get_api_url(f"text2video/{task_id}")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code == 200:
                    return response.json()
                else:
                    error_text = response.text
                    try:
                        error_json = response.json()
                        error_message = error_json.get("message", "查询任务失败")
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_message}"
                        )
                    except json.JSONDecodeError:
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_text}"
                        )

        except Exception as e:
            if "可灵API错误" in str(e):
                raise
            raise ValueError(f"查询任务失败: {e}")

    async def extend_video(
        self,
        video_id: str,
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        cfg_scale: Optional[float] = None,
    ) -> dict:
        """视频延长"""
        url = self._get_api_url("video-extend")

        # 构建请求数据
        request_data = {"video_id": video_id}

        # 添加可选参数
        if prompt:
            request_data["prompt"] = prompt.strip()

        if negative_prompt:
            request_data["negative_prompt"] = negative_prompt.strip()

        if cfg_scale is not None:
            request_data["cfg_scale"] = float(cfg_scale)

        print(f"🎬 【可灵API】视频延长请求URL: {url}")
        print(
            f"🎬 【可灵API】延长请求参数: {json.dumps(request_data, ensure_ascii=False)}"
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url, json=request_data, headers=self.headers
                )
                print(f"🎬 【可灵API】延长响应状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"🎬 【可灵API】延长响应成功: {result}")
                    return result
                else:
                    error_text = response.text
                    print(
                        f"🎬 【可灵API】延长响应错误 ({response.status_code}): {error_text}"
                    )

                    try:
                        error_json = response.json()
                        error_message = error_json.get("message", "视频延长API请求失败")
                        raise ValueError(
                            f"可灵视频延长API错误 ({response.status_code}): {error_message}"
                        )
                    except json.JSONDecodeError:
                        raise ValueError(
                            f"可灵视频延长API错误 ({response.status_code}): {error_text[:200]}"
                        )

        except httpx.TimeoutException:
            raise ValueError("可灵视频延长API请求超时，请稍后重试")
        except httpx.ConnectError as e:
            raise ValueError(f"无法连接到可灵视频延长API: {e}")
        except Exception as e:
            if "可灵" in str(e) and "API错误" in str(e):
                raise
            print(f"🎬 【可灵API】延长请求异常: {e}")
            import traceback

            traceback.print_exc()
            raise ValueError(f"可灵视频延长API请求失败: {e}")

    async def query_video_extend_task(self, task_id: str) -> dict:
        """查询视频延长任务状态"""
        url = self._get_api_url(f"video-extend/{task_id}")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code == 200:
                    result = response.json()
                    print(f"🎬 【可灵API】延长任务查询成功: {result}")
                    return result
                else:
                    error_text = response.text
                    try:
                        error_json = response.json()
                        error_message = error_json.get(
                            "message", "查询视频延长任务失败"
                        )
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_message}"
                        )
                    except json.JSONDecodeError:
                        raise ValueError(
                            f"可灵API错误 ({response.status_code}): {error_text}"
                        )

        except Exception as e:
            if "可灵API错误" in str(e):
                raise
            raise ValueError(f"查询视频延长任务失败: {e}")

    def _process_image_data(self, image_data: str, image_name: str = "图片") -> str:
        """处理图片数据，确保符合可灵API要求"""
        if not image_data:
            raise ValueError(f"{image_name}数据不能为空")

        image_data = image_data.strip()
        print(f"🎬 【可灵API】处理{image_name}数据: {len(image_data)}字符")

        # 检查是否是data URL格式
        if image_data.startswith("data:"):
            if "," in image_data:
                # 移除data URL前缀，保留纯base64数据
                image_data = image_data.split(",")[1]
                print(f"🎬 【可灵API】移除data URL前缀")
            else:
                raise ValueError(f"{image_name}的data URL格式无效")

        # 清理空白字符
        image_data = "".join(image_data.split())

        # 验证base64格式
        try:
            decoded_data = base64.b64decode(image_data)
            if len(decoded_data) < 1000:  # 可灵要求较大的图片
                raise ValueError(f"{image_name}数据太小: {len(decoded_data)} bytes")
            print(
                f"🎬 【可灵API】{image_name}验证通过，解码后大小: {len(decoded_data)} bytes"
            )
        except Exception as e:
            raise ValueError(f"{image_name}的base64数据无效: {e}")

        return image_data


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
                desc=f"可灵视频生成: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "kling", "credits": amount},
            ),
        )

        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        print(f"Error deducting Kling credits: {e}")
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
                desc=f"可灵视频生成: {reason}",
                api_params={"task_id": task_id} if task_id else {},
                usage={"service": "kling", "credits": amount},
            ),
        )

        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        print(f"Error adding Kling credits: {e}")
        return 0.0


# ======================== 管理员功能 ========================


def admin_add_credits_to_user(
    admin_id: str, target_user_id: str, amount: int, reason: str = ""
) -> float:
    """管理员给用户充值积分"""
    full_reason = (
        f"Admin {admin_id} added Kling credits: {reason}"
        if reason
        else f"Admin {admin_id} added Kling credits"
    )
    return add_user_credits(target_user_id, amount, full_reason)


def admin_deduct_credits_from_user(
    admin_id: str, target_user_id: str, amount: int, reason: str = ""
) -> float:
    """管理员扣除用户积分"""
    full_reason = (
        f"Admin {admin_id} deducted Kling credits: {reason}"
        if reason
        else f"Admin {admin_id} deducted Kling credits"
    )
    return deduct_user_credits(target_user_id, amount, full_reason)


# ======================== 统计功能 ========================


def get_system_kling_stats() -> dict:
    """获取系统可灵统计"""
    from open_webui.models.kling import KlingTask
    from open_webui.internal.db import get_db
    from sqlalchemy import func

    with get_db() as db:
        # 总任务数
        total_tasks = db.query(KlingTask).count()

        # 成功任务数
        success_tasks = (
            db.query(KlingTask).filter(KlingTask.status == "succeed").count()
        )

        # 今日任务数
        today = datetime.utcnow().date()
        today_tasks = (
            db.query(KlingTask).filter(func.date(KlingTask.created_at) == today).count()
        )

        # 各状态任务数
        status_stats = (
            db.query(KlingTask.status, func.count(KlingTask.id))
            .group_by(KlingTask.status)
            .all()
        )

        # 各动作类型统计
        action_stats = (
            db.query(KlingTask.action, func.count(KlingTask.id))
            .group_by(KlingTask.action)
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


def get_user_kling_stats(user_id: str) -> dict:
    """获取用户可灵统计"""
    from open_webui.models.kling import KlingTask
    from open_webui.internal.db import get_db
    from sqlalchemy import func

    with get_db() as db:
        # 用户任务数
        user_tasks = db.query(KlingTask).filter(KlingTask.user_id == user_id).count()

        # 用户成功任务数
        user_success = (
            db.query(KlingTask)
            .filter(KlingTask.user_id == user_id, KlingTask.status == "succeed")
            .count()
        )

        # 用户今日任务数
        today = datetime.utcnow().date()
        user_today = (
            db.query(KlingTask)
            .filter(
                KlingTask.user_id == user_id, func.date(KlingTask.created_at) == today
            )
            .count()
        )

        # 用户积分余额
        balance = get_user_credit_balance(user_id)

        # 用户总消费积分
        total_spent = (
            db.query(func.sum(KlingTask.credits_cost))
            .filter(KlingTask.user_id == user_id)
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


async def process_kling_generation(
    user_id: str, request: KlingGenerateRequest, action: str = "TEXT_TO_VIDEO"
) -> KlingTask:
    """处理可灵视频生成任务"""
    config = KlingConfig.get_config()
    if not config or not config.enabled:
        raise Exception("可灵服务未配置或已禁用")

    print(f"🎬 【可灵处理】开始处理: {action}, 用户: {user_id}")
    print(
        f"🎬 【可灵处理】配置: base_url={config.base_url}, model={request.model_name}"
    )
    print(
        f"🎬 【可灵处理】请求: prompt={request.prompt[:50]}..., mode={request.mode}, duration={request.duration}"
    )

    if action == "MULTI_IMAGE_TO_VIDEO":
        print(f"🎬 【可灵处理】多图模式: {len(request.image_list)}张图片")

    # 计算积分消耗（统一积分，不因图片数量变化）
    credits_cost = config.get_credits_cost(
        request.mode or "std", request.duration or "5", request.model_name
    )

    # 验证积分
    if not validate_user_credits(user_id, credits_cost):
        raise Exception("积分不足")

    # 扣除积分
    deduct_user_credits(user_id, credits_cost, f"可灵-{action}")

    # 根据动作类型准备任务数据
    task_data = {
        "user_id": user_id,
        "action": action,
        "prompt": request.prompt,
        "model_name": request.model_name,
        "mode": request.mode,
        "duration": request.duration,
        "aspect_ratio": request.aspect_ratio,
        "cfg_scale": request.cfg_scale,
        "negative_prompt": request.negative_prompt,
        "credits_cost": credits_cost,
        "generation_mode": request.generation_mode or "single_image",
        "image_tail": request.image_tail,
        "static_mask": request.static_mask,
        "dynamic_masks": (
            [dm.dict() for dm in request.dynamic_masks]
            if request.dynamic_masks
            else None
        ),
        "camera_control": (
            request.camera_control.dict(exclude_none=True)
            if request.camera_control
            else None
        ),
        "properties": {
            "serviceType": "kling",
            "action": action,
            "model": request.model_name,
            "mode": request.mode,
            "duration": request.duration,
        },
    }

    # 处理图片数据
    if action == "MULTI_IMAGE_TO_VIDEO":
        task_data.update(
            {
                "input_images": request.image_list,
                "image_count": len(request.image_list) if request.image_list else 0,
            }
        )
    else:
        task_data.update(
            {
                "input_image": request.image if action == "IMAGE_TO_VIDEO" else None,
                "image_count": (
                    1 if (action == "IMAGE_TO_VIDEO" and request.image) else 0
                ),
            }
        )

    # 创建任务记录
    task = KlingTask.create_task(**task_data)

    try:
        # 调用API
        client = KlingApiClient(config)

        if action == "TEXT_TO_VIDEO":
            api_response = await client.generate_text_to_video(request)
        elif action == "MULTI_IMAGE_TO_VIDEO":
            api_response = await client.generate_multi_image_to_video(request)
        else:  # IMAGE_TO_VIDEO
            api_response = await client.generate_image_to_video(request)

        # 更新任务状态
        task.update_from_api_response(api_response)

        return task

    except Exception as e:
        print(f"❌ 【可灵处理】生成失败: {e}")
        import traceback

        traceback.print_exc()

        # 发生错误时退还积分
        add_user_credits(user_id, credits_cost, f"可灵-{action}-error-refund", task.id)
        task.update_status("failed")
        task.fail_reason = str(e)
        raise


async def process_kling_video_extend(
    user_id: str,
    video_id: str,
    prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    cfg_scale: Optional[float] = None,
) -> KlingTask:
    """处理可灵视频延长任务"""
    from open_webui.models.kling import KlingVideoExtendRequest

    config = KlingConfig.get_config()
    if not config or not config.enabled:
        raise Exception("可灵服务未配置或已禁用")

    print(f"🎬 【可灵延长】开始处理视频延长: 视频ID={video_id}, 用户={user_id}")

    # 查找原始任务
    original_task = KlingTask.get_task_by_video_id(video_id)
    if not original_task:
        raise Exception("未找到原始视频任务")

    # 检查是否可以延长
    can_extend, reason, credits_cost = original_task.can_extend()
    if not can_extend:
        raise Exception(reason)

    print(f"🎬 【可灵延长】延长检查通过，积分消耗: {credits_cost}")

    # 验证积分
    if not validate_user_credits(user_id, credits_cost):
        raise Exception(f"积分不足，需要{credits_cost}积分")

    # 扣除积分
    deduct_user_credits(user_id, credits_cost, f"可灵视频延长-{video_id}")

    # 获取原始任务或根任务来计算延长次数
    root_task = KlingTask.get_original_task(original_task.id) or original_task
    extend_count = KlingTask.get_task_extend_count(root_task.id) + 1

    # 创建延长任务记录
    extend_task_data = {
        "user_id": user_id,
        "action": "VIDEO_EXTEND",
        "prompt": prompt or original_task.prompt,
        "negative_prompt": negative_prompt or original_task.negative_prompt,
        "model_name": original_task.model_name,
        "mode": original_task.mode,
        "duration": original_task.duration,
        "aspect_ratio": original_task.aspect_ratio,
        "cfg_scale": cfg_scale if cfg_scale is not None else original_task.cfg_scale,
        "credits_cost": credits_cost,
        "parent_task_id": original_task.id,
        "is_extended": True,
        "original_duration": str(original_task.get_total_duration()),
        "extend_count": extend_count,
        "properties": {
            "serviceType": "kling",
            "action": "VIDEO_EXTEND",
            "model": original_task.model_name,
            "mode": original_task.mode,
            "original_video_id": video_id,
            "extend_from_task": original_task.id,
        },
    }

    extend_task = KlingTask.create_task(**extend_task_data)

    try:
        # 调用API
        client = KlingApiClient(config)
        api_response = await client.extend_video(
            video_id=video_id,
            prompt=prompt,
            negative_prompt=negative_prompt,
            cfg_scale=cfg_scale,
        )

        # 更新任务状态
        extend_task.update_from_api_response(api_response)

        print(f"🎬 【可灵延长】任务创建成功: {extend_task.id}")
        return extend_task

    except Exception as e:
        print(f"❌ 【可灵延长】延长失败: {e}")
        import traceback

        traceback.print_exc()

        # 发生错误时退还积分
        add_user_credits(
            user_id, credits_cost, f"可灵视频延长失败退款-{video_id}", extend_task.id
        )
        extend_task.update_status("failed")
        extend_task.fail_reason = str(e)
        raise


# ======================== 任务清理 ========================


def cleanup_old_tasks(days: int = 30):
    """清理旧任务记录"""
    from open_webui.models.kling import KlingTask
    from open_webui.internal.db import get_db
    from datetime import timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    with get_db() as db:
        deleted_count = (
            db.query(KlingTask).filter(KlingTask.created_at < cutoff_date).delete()
        )
        db.commit()
        return deleted_count


# ======================== 错误处理 ========================


class KlingApiError(Exception):
    """可灵API错误"""

    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class KlingInsufficientCreditsError(Exception):
    """积分不足错误"""

    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient credits: required {required}, available {available}"
        )


class KlingConfigError(Exception):
    """配置错误"""

    pass


class KlingVideoError(Exception):
    """视频处理错误"""

    pass
