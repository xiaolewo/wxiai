from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from typing import Optional, List
import uuid
import logging
from datetime import datetime
import base64
import re
import ipaddress

from open_webui.models.kling_lip_sync import (
    KlingLipSyncConfigs,
    KlingLipSyncTasks,
    KlingLipSyncCredits,
    KlingLipSyncConfigForm,
    KlingLipSyncRequestModel,
    KlingLipSyncTaskModel,
    KlingLipSyncTaskResponse,
)
from open_webui.utils.auth import get_current_user, get_admin_user
from open_webui.utils.kling_lip_sync import kling_lip_sync_service
from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
from open_webui.services.file_manager import get_file_manager
from decimal import Decimal

logger = logging.getLogger(__name__)
router = APIRouter()

# ======================== URL验证函数 ========================


def is_ip_based_url(url: str) -> bool:
    """检查URL是否基于IP地址"""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False

        # 尝试解析为IP地址
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            return False
    except Exception:
        return False


def validate_video_url(url: str) -> tuple[bool, str]:
    """验证视频URL是否可被可灵API访问"""
    if not url or not url.strip():
        return False, "视频URL不能为空"

    url = url.strip()

    # 检查URL格式
    if not re.match(r"^https?://", url, re.IGNORECASE):
        return False, "视频URL必须以http://或https://开头"

    # 检查是否为IP地址URL
    if is_ip_based_url(url):
        return False, "可灵API无法访问基于IP地址的URL，请使用域名URL或上传文件"

    # 检查localhost和本地地址
    if re.search(r"localhost|127\.0\.0\.1|0\.0\.0\.0", url, re.IGNORECASE):
        return False, "可灵API无法访问本地地址，请使用公网可访问的URL或上传文件"

    # 检查端口号（通常API服务不支持非标准端口）
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        if parsed.port and parsed.port not in [80, 443]:
            return False, "可灵API可能无法访问使用非标准端口的URL，建议上传文件"
    except Exception:
        pass

    return True, ""


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
                desc=f"可灵对口型: {reason}",
                usage={
                    "service": "kling_lip_sync",
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
                desc=f"可灵对口型退款: {reason}",
                usage={
                    "service": "kling_lip_sync",
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
    default_voice_id: str
    default_voice_language: str
    default_voice_speed: float
    credits_cost: int


class UserCreditsResponse(BaseModel):
    balance: int


class VideoUploadResponse(BaseModel):
    success: bool
    message: str
    video_url: Optional[str] = None
    cloud_path: Optional[str] = None


# ======================== 管理员接口 ========================


@router.get("/config", dependencies=[Depends(get_admin_user)])
async def get_kling_lip_sync_config():
    """获取可灵对口型配置（管理员）"""
    try:
        config = KlingLipSyncConfigs.get_config()
        if config:
            return {
                "enabled": config.enabled,
                "base_url": config.base_url,
                "api_key": config.api_key,
                "default_voice_id": config.default_voice_id,
                "default_voice_language": config.default_voice_language,
                "default_voice_speed": config.default_voice_speed,
                "credits_cost": config.credits_cost,
            }
        else:
            # 返回默认配置
            return {
                "enabled": False,
                "base_url": "https://api.kling.com",
                "api_key": "",
                "default_voice_id": "genshin_vindi2",
                "default_voice_language": "zh",
                "default_voice_speed": 1.0,
                "credits_cost": 50,
            }
    except Exception as e:
        logger.error(f"获取可灵对口型配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.post("/config", dependencies=[Depends(get_admin_user)])
async def save_kling_lip_sync_config(config_form: KlingLipSyncConfigForm):
    """保存可灵对口型配置（管理员）"""
    try:
        logger.info(f"🎬 【可灵对口型管理员】保存配置: {config_form.model_dump()}")

        # 保存配置到数据库
        config = KlingLipSyncConfigs.upsert_config(config_form)

        # 重新初始化服务
        kling_lip_sync_service.initialize(config)

        logger.info("🎬 【可灵对口型管理员】配置保存成功")
        return {"success": True, "message": "配置保存成功"}

    except Exception as e:
        logger.error(f"保存可灵对口型配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/test", dependencies=[Depends(get_admin_user)])
async def test_kling_lip_sync_connection():
    """测试可灵对口型连接"""
    try:
        # 先获取最新配置
        config = KlingLipSyncConfigs.get_config()
        if not config:
            return {"status": "error", "message": "未找到配置，请先保存配置"}

        if not config.enabled:
            return {"status": "error", "message": "可灵对口型服务未启用"}

        if not config.api_key:
            return {"status": "error", "message": "请先配置API密钥"}

        # 重新初始化服务以确保使用最新配置
        kling_lip_sync_service.initialize(config)

        # 测试连接
        result = await kling_lip_sync_service.test_connection()
        logger.info(f"🎬 【可灵对口型管理员】连接测试结果: {result}")
        return result

    except Exception as e:
        logger.error(f"测试可灵对口型连接失败: {str(e)}")
        return {"status": "error", "message": f"连接测试失败: {str(e)}"}


# ======================== 用户接口 ========================


@router.get("/config/user")
async def get_user_kling_lip_sync_config(
    user=Depends(get_current_user),
) -> UserConfigResponse:
    """获取用户可见的可灵对口型配置"""
    try:
        config = KlingLipSyncConfigs.get_config()
        if config:
            return UserConfigResponse(
                enabled=config.enabled,
                default_voice_id=config.default_voice_id,
                default_voice_language=config.default_voice_language,
                default_voice_speed=config.default_voice_speed,
                credits_cost=config.credits_cost,
            )
        else:
            return UserConfigResponse(
                enabled=False,
                default_voice_id="genshin_vindi2",
                default_voice_language="zh",
                default_voice_speed=1.0,
                credits_cost=50,
            )
    except Exception as e:
        logger.error(f"获取用户可灵对口型配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.post("/submit")
async def submit_kling_lip_sync_task(
    request: KlingLipSyncRequestModel, user=Depends(get_current_user)
) -> TaskSubmitResponse:
    """提交对口型任务"""
    try:
        # 检查服务是否启用
        config = KlingLipSyncConfigs.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="可灵对口型服务未启用")

        # 初始化服务
        kling_lip_sync_service.initialize(config)
        if not kling_lip_sync_service.is_available():
            raise HTTPException(status_code=400, detail="可灵对口型服务不可用")

        # 验证视频输入URL（如果是video_url类型）
        if request.input_type == "video_url":
            is_valid, error_msg = validate_video_url(request.video_input)
            if not is_valid:
                raise HTTPException(
                    status_code=400, detail=f"视频URL验证失败: {error_msg}"
                )

        # 验证请求参数
        if request.mode == "text2video":
            if not request.text or not request.voice_id:
                raise HTTPException(
                    status_code=400, detail="文本转视频模式需要提供文本和音色ID"
                )
        elif request.mode == "audio2video":
            # 现在我们统一使用URL方式，检查是否有音频URL
            if not request.audio_url and not request.audio_file:
                raise HTTPException(
                    status_code=400, detail="音频转视频模式需要提供音频URL或音频文件"
                )
        else:
            raise HTTPException(
                status_code=400, detail="不支持的模式，请选择 text2video 或 audio2video"
            )

        # 验证积分
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
            "mode": request.mode,
            "video_input": request.video_input,
            "input_type": request.input_type,
            "text": request.text,
            "voice_id": request.voice_id or config.default_voice_id,
            "voice_language": request.voice_language or config.default_voice_language,
            "voice_speed": request.voice_speed or config.default_voice_speed,
            "audio_file": request.audio_file,
            "audio_type": request.audio_type,
            "credits_cost": credits_cost,
            "status": "submitted",
            "progress": "0%",
        }

        # 保存任务到数据库
        task = KlingLipSyncTasks.create_task(task_data)
        logger.info(f"🎬 【可灵对口型用户】创建任务: {task_id} (用户: {user.id})")

        # 扣除积分
        try:
            deduct_user_credits(
                user.id, credits_cost, f"对口型生成 - {request.mode}", task_id
            )

            # 记录积分消耗
            KlingLipSyncCredits.create_credit_record(
                user.id, task_id, credits_cost, "deduct"
            )
            logger.info(
                f"🎬 【可灵对口型用户】扣除积分: {credits_cost} (任务: {task_id})"
            )

        except Exception as credit_error:
            logger.error(f"扣除积分失败: {str(credit_error)}")
            raise HTTPException(status_code=400, detail="积分扣除失败")

        # 提交到可灵API
        try:
            api_request = request.model_dump()
            api_request.update(
                {
                    "voice_id": task_data["voice_id"],
                    "voice_language": task_data["voice_language"],
                    "voice_speed": task_data["voice_speed"],
                }
            )

            logger.info(f"🎬 【可灵对口型后端】API请求数据: {api_request}")
            logger.info(
                f"🎬 【可灵对口型后端】视频URL: {api_request.get('video_input')}"
            )

            result = await kling_lip_sync_service.submit_task(api_request)

            if result.get("success"):
                # 更新任务状态和外部任务ID
                updates = {
                    "status": "processing",
                    "properties": {"external_task_id": result.get("external_task_id")},
                }
                KlingLipSyncTasks.update_task(task_id, updates)
                logger.info(f"🎬 【可灵对口型用户】任务提交成功: {task_id}")

                return TaskSubmitResponse(
                    success=True, task_id=task_id, message="任务提交成功"
                )
            else:
                # 任务提交失败，退还积分
                refund_user_credits(user.id, credits_cost, "任务提交失败", task_id)
                KlingLipSyncCredits.create_credit_record(
                    user.id, task_id, credits_cost, "refund"
                )

                # 更新任务状态
                KlingLipSyncTasks.update_task(
                    task_id,
                    {
                        "status": "failed",
                        "fail_reason": result.get("message", "任务提交失败"),
                    },
                )

                logger.error(
                    f"🎬 【可灵对口型用户】任务提交失败: {result.get('message')}"
                )
                raise HTTPException(
                    status_code=400, detail=result.get("message", "任务提交失败")
                )

        except HTTPException:
            raise
        except Exception as api_error:
            # API调用异常，退还积分
            refund_user_credits(
                user.id, credits_cost, f"API调用异常: {str(api_error)}", task_id
            )
            KlingLipSyncCredits.create_credit_record(
                user.id, task_id, credits_cost, "refund"
            )

            # 更新任务状态
            KlingLipSyncTasks.update_task(
                task_id,
                {"status": "failed", "fail_reason": f"API调用异常: {str(api_error)}"},
            )

            logger.error(f"🎬 【可灵对口型用户】API调用异常: {str(api_error)}")
            raise HTTPException(status_code=500, detail="提交任务时发生异常")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交可灵对口型任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@router.get("/task/{task_id}")
async def get_kling_lip_sync_task_status(
    task_id: str, user=Depends(get_current_user)
) -> KlingLipSyncTaskModel:
    """获取任务状态"""
    try:
        # 获取任务信息
        task = KlingLipSyncTasks.get_task_by_id(task_id, user.id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 如果任务还在处理中，查询可灵API获取最新状态
        if task.status in ["submitted", "processing"]:
            config = KlingLipSyncConfigs.get_config()
            if config and config.enabled:
                kling_lip_sync_service.initialize(config)

                # 获取外部任务ID
                external_task_id = None
                if task.properties and isinstance(task.properties, dict):
                    external_task_id = task.properties.get("external_task_id")

                if external_task_id:
                    result = await kling_lip_sync_service.get_task_status(
                        external_task_id
                    )
                    if result:
                        # 更新任务状态
                        updates = {
                            "status": result.get("status", task.status),
                            "progress": result.get("progress", task.progress),
                            "video_url": result.get("video_url", task.video_url),
                            "video_duration": result.get(
                                "video_duration", task.video_duration
                            ),
                            "fail_reason": result.get("fail_reason", task.fail_reason),
                        }

                        if updates["status"] == "succeed" and updates["video_url"]:
                            updates["finish_time"] = datetime.now()

                            # 将生成的视频保存到云存储
                            try:
                                logger.info(
                                    f"🎬 【可灵对口型】开始保存视频到云存储: {updates['video_url']}"
                                )
                                file_manager = get_file_manager()
                                success, message, file_record = (
                                    await file_manager.save_generated_content(
                                        user_id=user.id,
                                        file_url=updates["video_url"],
                                        filename=f"kling_lip_sync_result_{task_id}.mp4",
                                        file_type="video",
                                        source_type="kling_lip_sync",
                                        source_task_id=task_id,
                                        metadata={
                                            "original_url": updates["video_url"],
                                            "task_mode": task.mode,
                                            "video_duration": updates.get(
                                                "video_duration"
                                            ),
                                            "generation_source": "kling_api",
                                        },
                                    )
                                )

                                if success and file_record and file_record.cloud_url:
                                    # 使用云存储URL替换原始URL
                                    updates["video_url"] = file_record.cloud_url
                                    updates["cloud_image_url"] = (
                                        file_record.cloud_url
                                    )  # 兼容字段
                                    logger.info(
                                        f"🎬 【可灵对口型】视频已保存到云存储: {file_record.cloud_url}"
                                    )
                                else:
                                    logger.warning(
                                        f"🎬 【可灵对口型】视频保存到云存储失败: {message}"
                                    )
                                    # 仍然使用原始URL，不影响任务完成
                            except Exception as save_error:
                                logger.error(
                                    f"🎬 【可灵对口型】保存视频到云存储时异常: {str(save_error)}"
                                )
                                # 不影响任务状态更新，继续使用原始URL

                        # 无论云存储是否成功，都要更新任务状态
                        updated_task = KlingLipSyncTasks.update_task(task_id, updates)
                        if updated_task:
                            task = updated_task
                            logger.info(
                                f"🎬 【可灵对口型用户】任务状态更新成功: {task_id} -> {task.status} (进度: {task.progress})"
                            )

                            # 如果任务已完成，记录完成状态
                            if task.status in ["succeed", "failed"]:
                                logger.info(
                                    f"🎬 【可灵对口型用户】任务{task_id}已完成，状态: {task.status}, 前端轮询应该停止"
                                )
                        else:
                            logger.error(
                                f"🎬 【可灵对口型用户】任务状态更新失败: {task_id}"
                            )
                    else:
                        logger.warning(
                            f"🎬 【可灵对口型用户】从可灵API获取任务状态失败: {external_task_id}"
                        )
                else:
                    logger.warning(
                        f"🎬 【可灵对口型用户】任务{task_id}缺少external_task_id，无法查询状态"
                    )

        return KlingLipSyncTaskModel.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取可灵对口型任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务状态失败")


@router.get("/history")
async def get_kling_lip_sync_history(
    page: int = 1, limit: int = 20, user=Depends(get_current_user)
) -> KlingLipSyncTaskResponse:
    """获取用户任务历史"""
    try:
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20

        tasks, total = KlingLipSyncTasks.get_user_tasks(user.id, page, limit)

        task_models = [KlingLipSyncTaskModel.model_validate(task) for task in tasks]

        return KlingLipSyncTaskResponse(
            data=task_models, total=total, page=page, limit=limit
        )

    except Exception as e:
        logger.error(f"获取可灵对口型历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取历史记录失败")


@router.delete("/task/{task_id}")
async def delete_kling_lip_sync_task(
    task_id: str, user=Depends(get_current_user)
) -> ApiResponse:
    """删除任务"""
    try:
        success = KlingLipSyncTasks.delete_task(task_id, user.id)
        if success:
            logger.info(f"🎬 【可灵对口型用户】删除任务: {task_id}")
            return ApiResponse(success=True, message="任务删除成功")
        else:
            raise HTTPException(status_code=404, detail="任务不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除可灵对口型任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除任务失败")


@router.get("/credits")
async def get_kling_lip_sync_credits(
    user=Depends(get_current_user),
) -> UserCreditsResponse:
    """获取用户积分余额"""
    try:
        balance = get_user_credit_balance(user.id)
        return UserCreditsResponse(balance=int(balance))

    except Exception as e:
        logger.error(f"获取用户积分失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取积分失败")


@router.post("/upload-video")
async def upload_video_for_lip_sync(
    video: UploadFile = File(...), user=Depends(get_current_user)
) -> VideoUploadResponse:
    """上传视频文件到云存储用于对口型"""
    try:
        # 验证文件类型
        if not video.content_type or not video.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="请上传视频文件")

        # 验证文件大小 (100MB限制)
        if video.size and video.size > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="视频文件大小不能超过100MB")

        # 读取文件内容
        file_content = await video.read()

        # 生成文件名
        original_filename = video.filename or "video"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kling_lip_sync_{timestamp}_{original_filename}"

        # 使用文件管理器上传到云存储
        file_manager = get_file_manager()
        success, message, file_record = await file_manager.save_generated_content(
            user_id=user.id,
            file_data=file_content,
            filename=filename,
            file_type="video",
            source_type="kling_lip_sync",
            metadata={
                "original_filename": original_filename,
                "content_type": video.content_type,
                "file_size": len(file_content),
                "upload_purpose": "lip_sync_input",
            },
        )

        if success and file_record and file_record.cloud_url:
            logger.info(
                f"🎬 【可灵对口型】视频上传成功: {file_record.cloud_url} (用户: {user.id})"
            )

            # 记录上传的URL以便调试
            logger.info(
                f"🎬 【可灵对口型】将传递给可灵API的URL: {file_record.cloud_url}"
            )

            return VideoUploadResponse(
                success=True,
                message="视频上传成功",
                video_url=file_record.cloud_url,
                cloud_path=file_record.cloud_path,
            )
        else:
            logger.error(f"🎬 【可灵对口型】视频上传失败: {message}")
            raise HTTPException(status_code=500, detail=message or "上传失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传视频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传视频失败: {str(e)}")


class AudioUploadResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str] = None
    cloud_path: Optional[str] = None


@router.post("/upload-audio")
async def upload_audio_for_lip_sync(
    audio: UploadFile = File(...), user=Depends(get_current_user)
) -> AudioUploadResponse:
    """上传音频文件到云存储用于对口型"""
    try:
        # 验证文件类型
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="请上传音频文件")

        # 验证文件大小 (5MB限制)
        if audio.size and audio.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="音频文件大小不能超过5MB")

        # 读取文件内容
        file_content = await audio.read()

        # 生成文件名
        original_filename = audio.filename or "audio"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kling_lip_sync_audio_{timestamp}_{original_filename}"

        # 使用文件管理器上传到云存储
        file_manager = get_file_manager()
        success, message, file_record = await file_manager.save_generated_content(
            user_id=user.id,
            file_data=file_content,
            filename=filename,
            file_type="audio",
            source_type="kling_lip_sync",
            metadata={
                "original_filename": original_filename,
                "content_type": audio.content_type,
                "file_size": len(file_content),
                "upload_purpose": "lip_sync_audio_input",
            },
        )

        if success and file_record and file_record.cloud_url:
            logger.info(
                f"🎬 【可灵对口型】音频上传成功: {file_record.cloud_url} (用户: {user.id})"
            )

            return AudioUploadResponse(
                success=True,
                message="音频上传成功",
                audio_url=file_record.cloud_url,
                cloud_path=file_record.cloud_path,
            )
        else:
            logger.error(f"🎬 【可灵对口型】音频上传失败: {message}")
            raise HTTPException(status_code=500, detail=message or "上传失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传音频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传音频失败: {str(e)}")
