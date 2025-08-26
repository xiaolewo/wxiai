from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from typing import Optional, List
import uuid
import logging
from datetime import datetime
import base64

from open_webui.models.jimeng_inpainting import (
    JimengInpaintingConfigs,
    JimengInpaintingTasks,
    JimengInpaintingCredits,
    JimengInpaintingConfigForm,
    JimengInpaintingRequestModel,
    JimengInpaintingTaskModel,
    JimengInpaintingTaskResponse,
)
from open_webui.utils.auth import get_current_user, get_admin_user
from open_webui.utils.jimeng_inpainting import jimeng_inpainting_service
from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
from open_webui.services.file_manager import get_file_manager
from decimal import Decimal

logger = logging.getLogger(__name__)
router = APIRouter()

# ======================== 积分处理函数 ========================


def get_user_credit_balance(user_id: str) -> float:
    """获取用户积分余额"""
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


def deduct_user_credits(user_id: str, amount: int, reason: str, task_id: str) -> float:
    """扣除用户积分"""
    try:
        # 扣除积分（负数）
        form_data = AddCreditForm(
            user_id=user_id,
            amount=Decimal(-amount),
            detail=SetCreditFormDetail(
                desc=f"即梦涂抹消除: {reason}",
                usage={
                    "service": "jimeng_inpainting",
                    "task_id": task_id,
                    "amount": amount,
                    "reason": reason,
                },
            ),
        )
        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        logger.error(f"扣除积分失败: {str(e)}")
        raise HTTPException(status_code=400, detail="积分扣除失败")


def refund_user_credits(user_id: str, amount: int, reason: str, task_id: str) -> float:
    """退还用户积分"""
    try:
        # 退还积分（正数）
        form_data = AddCreditForm(
            user_id=user_id,
            amount=Decimal(amount),
            detail=SetCreditFormDetail(
                desc=f"即梦涂抹消除退款: {reason}",
                usage={
                    "service": "jimeng_inpainting",
                    "task_id": task_id,
                    "amount": amount,
                    "reason": reason,
                },
            ),
        )
        result = Credits.add_credit_by_user_id(form_data)
        return float(result.credit) if result else 0.0
    except Exception as e:
        logger.error(f"退还积分失败: {str(e)}")
        return 0.0


# ======================== 响应模型 ========================


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class TaskSubmitResponse(BaseModel):
    success: bool
    task_id: str
    message: str


class UserConfigResponse(BaseModel):
    enabled: bool
    credits_cost: int
    edit_credits_cost: int
    default_steps: int
    default_strength: float
    default_scale: float
    default_quality: str


class UserCreditsResponse(BaseModel):
    balance: int


class ImageUploadResponse(BaseModel):
    success: bool
    message: str
    image_url: Optional[str] = None
    cloud_path: Optional[str] = None


# ======================== 管理员接口 ========================


@router.get("/config", dependencies=[Depends(get_admin_user)])
async def get_jimeng_inpainting_config():
    """获取即梦涂抹消除配置（管理员）"""
    try:
        config = JimengInpaintingConfigs.get_config()
        if config:
            return {
                "enabled": config.enabled,
                "base_url": config.base_url,
                "api_key": config.api_key,
                "credits_cost": config.credits_cost,
                "edit_credits_cost": config.edit_credits_cost,
                "default_steps": config.default_steps,
                "default_strength": config.default_strength,
                "default_scale": config.default_scale,
                "default_quality": config.default_quality,
            }
        else:
            # 返回默认配置
            return {
                "enabled": False,
                "base_url": "https://visual.volcengineapi.com",
                "api_key": "",
                "credits_cost": 30,
                "edit_credits_cost": 40,
                "default_steps": 30,
                "default_strength": 0.8,
                "default_scale": 7.0,
                "default_quality": "M",
            }
    except Exception as e:
        logger.error(f"获取即梦涂抹消除配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.post("/config", dependencies=[Depends(get_admin_user)])
async def save_jimeng_inpainting_config(config_form: JimengInpaintingConfigForm):
    """保存即梦涂抹消除配置（管理员）"""
    try:
        logger.info(f"🎨 【即梦涂抹消除管理员】保存配置: {config_form.model_dump()}")

        # 保存配置到数据库
        config = JimengInpaintingConfigs.upsert_config(config_form)

        # 重新初始化服务
        jimeng_inpainting_service.initialize(config)

        logger.info("🎨 【即梦涂抹消除管理员】配置保存成功")
        return {"success": True, "message": "配置保存成功"}

    except Exception as e:
        logger.error(f"保存即梦涂抹消除配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/test", dependencies=[Depends(get_admin_user)])
async def test_jimeng_inpainting_connection():
    """测试即梦涂抹消除连接"""
    try:
        # 先获取最新配置
        config = JimengInpaintingConfigs.get_config()
        if not config:
            return {"status": "error", "message": "未找到配置，请先保存配置"}

        if not config.enabled:
            return {"status": "error", "message": "即梦涂抹消除服务未启用"}

        if not config.api_key:
            return {"status": "error", "message": "请先配置API密钥"}

        # 重新初始化服务以确保使用最新配置
        jimeng_inpainting_service.initialize(config)

        # 测试连接
        result = await jimeng_inpainting_service.test_connection()
        logger.info(f"🎨 【即梦涂抹消除管理员】连接测试结果: {result}")
        return result

    except Exception as e:
        logger.error(f"测试即梦涂抹消除连接失败: {str(e)}")
        return {"status": "error", "message": f"连接测试失败: {str(e)}"}


# ======================== 用户接口 ========================


@router.get("/config/user")
async def get_user_jimeng_inpainting_config(
    user=Depends(get_current_user),
) -> UserConfigResponse:
    """获取用户可见的即梦涂抹消除配置"""
    try:
        config = JimengInpaintingConfigs.get_config()
        if config:
            return UserConfigResponse(
                enabled=config.enabled,
                credits_cost=config.credits_cost,
                edit_credits_cost=config.edit_credits_cost,
                default_steps=config.default_steps,
                default_strength=config.default_strength,
                default_scale=config.default_scale,
                default_quality=config.default_quality,
            )
        else:
            return UserConfigResponse(
                enabled=False,
                credits_cost=30,
                edit_credits_cost=40,
                default_steps=30,
                default_strength=0.8,
                default_scale=7.0,
                default_quality="M",
            )
    except Exception as e:
        logger.error(f"获取用户即梦涂抹消除配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.post("/submit")
async def submit_jimeng_inpainting_task(
    request: JimengInpaintingRequestModel, user=Depends(get_current_user)
) -> TaskSubmitResponse:
    """提交涂抹消除/编辑任务"""
    try:
        # 检查服务是否启用
        config = JimengInpaintingConfigs.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="即梦图像编辑服务未启用")

        # 初始化服务
        jimeng_inpainting_service.initialize(config)
        if not jimeng_inpainting_service.is_available():
            raise HTTPException(status_code=400, detail="即梦图像编辑服务不可用")

        # 验证请求参数
        if not request.original_image_url or not request.original_image_url.strip():
            raise HTTPException(status_code=400, detail="请上传原始图片")

        if not request.mask_image_url or not request.mask_image_url.strip():
            raise HTTPException(status_code=400, detail="请上传遮罩图片")

        # 验证编辑模式的提示词
        if request.mode == "edit" and (
            not request.custom_prompt or not request.custom_prompt.strip()
        ):
            raise HTTPException(status_code=400, detail="编辑模式需要输入提示词")

        # 根据模式计算积分消耗
        if request.mode == "edit":
            credits_cost = config.edit_credits_cost
        else:
            credits_cost = config.credits_cost
        if not validate_user_credits(user.id, credits_cost):
            raise HTTPException(
                status_code=400, detail=f"积分不足，需要 {credits_cost} 积分"
            )

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 创建任务记录
        task_data = {
            "id": task_id,
            "user_id": user.id,
            "status": "processing",  # 即梦API直接处理，设为processing
            "progress": "50%",
            "mode": request.mode or "remove",
            "custom_prompt": (
                request.custom_prompt.strip() if request.custom_prompt else None
            ),
            "original_image_url": request.original_image_url.strip(),
            "mask_image_url": request.mask_image_url.strip(),
            "steps": request.steps or config.default_steps,
            "strength": request.strength or config.default_strength,
            "scale": request.scale or config.default_scale,
            "seed": request.seed or 0,
            "dilate_size": request.dilate_size or 15,
            "quality": request.quality or config.default_quality,
            "credits_cost": credits_cost,
        }

        # 保存任务到数据库
        task = JimengInpaintingTasks.create_task(task_data)
        mode_text = "涂抹编辑" if request.mode == "edit" else "涂抹消除"
        logger.info(f"🎨 【即梦{mode_text}用户】创建任务: {task_id} (用户: {user.id})")

        # 扣除积分
        try:
            deduct_user_credits(user.id, credits_cost, f"{mode_text}处理", task_id)

            # 记录积分消耗
            JimengInpaintingCredits.create_credit_record(
                user.id, task_id, credits_cost, "deduct"
            )
            logger.info(
                f"🎨 【即梦{mode_text}用户】扣除积分: {credits_cost} (任务: {task_id})"
            )

        except Exception as credit_error:
            logger.error(f"扣除积分失败: {str(credit_error)}")
            raise HTTPException(status_code=400, detail="积分扣除失败")

        # 提交到即梦API
        try:
            api_request = request.model_dump()
            api_request.update(
                {
                    "steps": task_data["steps"],
                    "strength": task_data["strength"],
                    "scale": task_data["scale"],
                    "seed": task_data["seed"],
                    "dilate_size": task_data["dilate_size"],
                    "quality": task_data["quality"],
                }
            )

            logger.info(f"🎨 【即梦{mode_text}后端】API请求数据: {api_request}")

            result = await jimeng_inpainting_service.submit_task(api_request)

            if result.get("success"):
                # 即梦API直接返回结果
                result_image_url = result.get("result_image_url")

                # 将生成的图片保存到云存储
                cloud_image_url = result_image_url
                try:
                    logger.info(
                        f"🎨 【即梦涂抹消除】开始保存结果图片到云存储: {result_image_url}"
                    )
                    file_manager = get_file_manager()
                    success, message, file_record = (
                        await file_manager.save_generated_content(
                            user_id=user.id,
                            file_url=result_image_url,
                            filename=f"jimeng_inpainting_result_{task_id}.jpg",
                            file_type="image",
                            source_type="jimeng_inpainting",
                            source_task_id=task_id,
                            metadata={
                                "original_url": result_image_url,
                                "generation_source": "jimeng_api",
                                "task_parameters": {
                                    "steps": task_data["steps"],
                                    "strength": task_data["strength"],
                                    "scale": task_data["scale"],
                                    "quality": task_data["quality"],
                                },
                            },
                        )
                    )

                    if success and file_record and file_record.cloud_url:
                        # 使用云存储URL替换原始URL
                        cloud_image_url = file_record.cloud_url
                        logger.info(
                            f"🎨 【即梦涂抹消除】图片已保存到云存储: {file_record.cloud_url}"
                        )
                    else:
                        logger.warning(
                            f"🎨 【即梦涂抹消除】图片保存到云存储失败: {message}"
                        )
                        # 仍然使用原始URL，不影响任务完成
                except Exception as save_error:
                    logger.error(
                        f"🎨 【即梦涂抹消除】保存图片到云存储时异常: {str(save_error)}"
                    )
                    # 不影响任务状态更新，继续使用原始URL

                # 更新任务状态为成功
                updates = {
                    "status": "succeed",
                    "progress": "100%",
                    "result_image_url": result_image_url,
                    "cloud_image_url": cloud_image_url,
                    "finish_time": datetime.now(),
                }
                JimengInpaintingTasks.update_task(task_id, updates)
                logger.info(f"🎨 【即梦{mode_text}用户】任务完成: {task_id}")

                return TaskSubmitResponse(
                    success=True, task_id=task_id, message=f"{mode_text}处理完成"
                )
            else:
                # 任务处理失败，退还积分
                refund_user_credits(user.id, credits_cost, "任务处理失败", task_id)
                JimengInpaintingCredits.create_credit_record(
                    user.id, task_id, credits_cost, "refund"
                )

                # 更新任务状态
                JimengInpaintingTasks.update_task(
                    task_id,
                    {
                        "status": "failed",
                        "progress": "0%",
                        "fail_reason": result.get("message", "任务处理失败"),
                    },
                )

                logger.error(
                    f"🎨 【即梦{mode_text}用户】任务处理失败: {result.get('message')}"
                )
                raise HTTPException(
                    status_code=400, detail=result.get("message", "任务处理失败")
                )

        except HTTPException:
            raise
        except Exception as api_error:
            # API调用异常，退还积分
            refund_user_credits(
                user.id, credits_cost, f"API调用异常: {str(api_error)}", task_id
            )
            JimengInpaintingCredits.create_credit_record(
                user.id, task_id, credits_cost, "refund"
            )

            # 更新任务状态
            JimengInpaintingTasks.update_task(
                task_id,
                {
                    "status": "failed",
                    "progress": "0%",
                    "fail_reason": f"API调用异常: {str(api_error)}",
                },
            )

            logger.error(f"🎨 【即梦{mode_text}用户】API调用异常: {str(api_error)}")
            raise HTTPException(status_code=500, detail="处理任务时发生异常")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交即梦图像编辑任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@router.get("/task/{task_id}")
async def get_jimeng_inpainting_task_status(
    task_id: str, user=Depends(get_current_user)
) -> JimengInpaintingTaskModel:
    """获取任务状态"""
    try:
        # 获取任务信息
        task = JimengInpaintingTasks.get_task_by_id(task_id, user.id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        return JimengInpaintingTaskModel.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取即梦涂抹消除任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务状态失败")


@router.get("/history")
async def get_jimeng_inpainting_history(
    page: int = 1, limit: int = 20, user=Depends(get_current_user)
) -> JimengInpaintingTaskResponse:
    """获取用户任务历史"""
    try:
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20

        tasks, total = JimengInpaintingTasks.get_user_tasks(user.id, page, limit)

        task_models = [JimengInpaintingTaskModel.model_validate(task) for task in tasks]

        return JimengInpaintingTaskResponse(
            data=task_models, total=total, page=page, limit=limit
        )

    except Exception as e:
        logger.error(f"获取即梦涂抹消除历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取历史记录失败")


@router.delete("/task/{task_id}")
async def delete_jimeng_inpainting_task(
    task_id: str, user=Depends(get_current_user)
) -> ApiResponse:
    """删除任务"""
    try:
        success = JimengInpaintingTasks.delete_task(task_id, user.id)
        if success:
            logger.info(f"🎨 【即梦涂抹消除用户】删除任务: {task_id}")
            return ApiResponse(success=True, message="任务删除成功")
        else:
            raise HTTPException(status_code=404, detail="任务不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除即梦涂抹消除任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除任务失败")


@router.get("/credits")
async def get_jimeng_inpainting_credits(
    user=Depends(get_current_user),
) -> UserCreditsResponse:
    """获取用户积分余额"""
    try:
        balance = get_user_credit_balance(user.id)
        return UserCreditsResponse(balance=int(balance))

    except Exception as e:
        logger.error(f"获取用户积分失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取积分失败")


@router.post("/upload-image")
async def upload_image_for_inpainting(
    image: UploadFile = File(...), user=Depends(get_current_user)
) -> ImageUploadResponse:
    """上传图片文件到云存储用于涂抹消除"""
    try:
        # 验证文件类型
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="请上传图片文件")

        # 验证文件大小 (5MB限制)
        if image.size and image.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="图片文件大小不能超过5MB")

        # 读取文件内容
        file_content = await image.read()

        # 生成文件名
        original_filename = image.filename or "image"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jimeng_inpainting_{timestamp}_{original_filename}"

        # 使用文件管理器上传到云存储
        file_manager = get_file_manager()
        success, message, file_record = await file_manager.save_generated_content(
            user_id=user.id,
            file_data=file_content,
            filename=filename,
            file_type="image",
            source_type="jimeng_inpainting",
            metadata={
                "original_filename": original_filename,
                "content_type": image.content_type,
                "file_size": len(file_content),
                "upload_purpose": "inpainting_input",
            },
        )

        if success and file_record and file_record.cloud_url:
            logger.info(
                f"🎨 【即梦涂抹消除】图片上传成功: {file_record.cloud_url} (用户: {user.id})"
            )

            return ImageUploadResponse(
                success=True,
                message="图片上传成功",
                image_url=file_record.cloud_url,
                cloud_path=file_record.cloud_path,
            )
        else:
            logger.error(f"🎨 【即梦涂抹消除】图片上传失败: {message}")
            raise HTTPException(status_code=500, detail=message or "上传失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传图片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传图片失败: {str(e)}")
