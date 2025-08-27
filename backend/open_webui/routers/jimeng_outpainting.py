import logging
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from open_webui.internal.db import SessionLocal
from open_webui.models.jimeng_outpainting import (
    JimengOutpaintingConfig,
    JimengOutpaintingTask,
    JimengOutpaintingCredit,
    JimengOutpaintingConfigModel,
    JimengOutpaintingRequest,
    JimengOutpaintingTaskResponse,
    JimengOutpaintingHistoryResponse,
    JimengOutpaintingCreditsResponse,
)
from open_webui.models.users import UserModel
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.jimeng_outpainting import jimeng_outpainting_service
from open_webui.services.file_manager import get_file_manager
from fastapi.responses import StreamingResponse
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# 管理员配置接口


@router.get("/config", dependencies=[Depends(get_admin_user)])
async def get_jimeng_outpainting_config():
    """获取即梦智能扩图配置"""
    db = SessionLocal()
    try:
        config = db.query(JimengOutpaintingConfig).first()
        if not config:
            # 创建默认配置
            config = JimengOutpaintingConfig()
            db.add(config)
            db.commit()
            db.refresh(config)

        return {
            "enabled": config.enabled,
            "base_url": config.base_url,
            "api_key": config.api_key,
            "credits_cost": config.credits_cost,
            "default_steps": config.default_steps,
            "default_strength": config.default_strength,
            "default_scale": config.default_scale,
            "default_quality": config.default_quality,
            "default_max_width": config.default_max_width,
            "default_max_height": config.default_max_height,
        }
    except Exception as e:
        logger.error(f"获取即梦智能扩图配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置失败")
    finally:
        db.close()


@router.put("/config", dependencies=[Depends(get_admin_user)])
async def update_jimeng_outpainting_config(config_data: JimengOutpaintingConfigModel):
    """更新即梦智能扩图配置"""
    db = SessionLocal()
    try:
        config = db.query(JimengOutpaintingConfig).first()
        if not config:
            config = JimengOutpaintingConfig()
            db.add(config)

        # 更新配置
        config.enabled = config_data.enabled
        config.base_url = config_data.base_url
        config.api_key = config_data.api_key
        config.credits_cost = config_data.credits_cost
        config.default_steps = config_data.default_steps
        config.default_strength = config_data.default_strength
        config.default_scale = config_data.default_scale
        config.default_quality = config_data.default_quality
        config.default_max_width = config_data.default_max_width
        config.default_max_height = config_data.default_max_height
        config.updated_at = datetime.now()

        db.commit()
        db.refresh(config)

        # 重新初始化服务
        jimeng_outpainting_service.initialize(config)

        return {"message": "配置更新成功"}
    except Exception as e:
        logger.error(f"更新即梦智能扩图配置失败: {e}")
        raise HTTPException(status_code=500, detail="更新配置失败")
    finally:
        db.close()


@router.get("/config/test", dependencies=[Depends(get_admin_user)])
async def test_jimeng_outpainting_connection():
    """测试即梦智能扩图API连接"""
    try:
        result = await jimeng_outpainting_service.test_connection()
        return result
    except Exception as e:
        logger.error(f"测试即梦智能扩图连接失败: {e}")
        return {"status": "error", "message": f"连接测试失败: {str(e)}"}


# 用户接口


@router.get("/user-config")
async def get_jimeng_outpainting_user_config(
    user: UserModel = Depends(get_verified_user),
):
    """获取用户可见的即梦智能扩图配置"""
    db = SessionLocal()
    try:
        config = db.query(JimengOutpaintingConfig).first()
        if not config:
            raise HTTPException(status_code=404, detail="配置未找到")

        # 确保服务已初始化
        if not jimeng_outpainting_service.is_available():
            jimeng_outpainting_service.initialize(config)

        return {
            "enabled": config.enabled,
            "credits_cost": config.credits_cost,
            "default_steps": config.default_steps,
            "default_strength": config.default_strength,
            "default_scale": config.default_scale,
            "default_quality": config.default_quality,
            "default_max_width": config.default_max_width,
            "default_max_height": config.default_max_height,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置失败")
    finally:
        db.close()


@router.post("/upload-image")
async def upload_image_for_outpainting(
    file: UploadFile = File(...), user: UserModel = Depends(get_verified_user)
):
    """上传图片用于智能扩图"""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只能上传图片文件")

        if file.size > 5 * 1024 * 1024:  # 5MB限制
            raise HTTPException(status_code=400, detail="文件大小不能超过5MB")

        # 读取文件内容
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="文件内容不能为空")

        # 生成唯一文件名
        file_extension = (
            file.filename.split(".")[-1]
            if file.filename and "." in file.filename
            else "jpg"
        )
        unique_filename = f"outpainting_{user.id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}.{file_extension}"

        # 上传到文件管理器
        file_manager = get_file_manager()
        success, message, file_record = await file_manager.save_generated_content(
            user_id=user.id,
            file_data=file_content,
            filename=unique_filename,
            file_type="image",
            source_type="upload",
        )

        if not success:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {message}")

        # 构建文件URL - 优先使用cloud_url，否则使用我们的文件服务路径
        if file_record and file_record.cloud_url:
            file_url = file_record.cloud_url
        else:
            # 使用我们的文件访问路径
            file_url = (
                f"/api/v1/jimeng-outpainting/files/{file_record.id}"
                if file_record
                else f"/api/v1/files/{unique_filename}"
            )

        return {
            "success": True,
            "image_url": file_url,
            "filename": unique_filename,
            "message": "图片上传成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/tasks")
async def submit_jimeng_outpainting_task(
    request: JimengOutpaintingRequest, user: UserModel = Depends(get_verified_user)
):
    """提交即梦智能扩图任务"""
    db = SessionLocal()
    try:
        # 获取配置并初始化服务
        config = db.query(JimengOutpaintingConfig).first()
        if not config:
            # 创建默认配置
            config = JimengOutpaintingConfig()
            db.add(config)
            db.commit()
            db.refresh(config)

        # 初始化服务
        if not jimeng_outpainting_service.is_available():
            jimeng_outpainting_service.initialize(config)

        # 检查服务是否可用
        if not jimeng_outpainting_service.is_available():
            if not config.enabled:
                raise HTTPException(
                    status_code=503, detail="即梦智能扩图服务未启用，请联系管理员配置"
                )
            elif not config.api_key:
                raise HTTPException(
                    status_code=503,
                    detail="即梦智能扩图API密钥未配置，请联系管理员配置",
                )
            else:
                raise HTTPException(status_code=503, detail="即梦智能扩图服务不可用")

        # 检查积分余额
        from open_webui.models.credits import Credits

        credit_record = Credits.get_credit_by_user_id(user.id)
        user_credits = int(credit_record.credit) if credit_record else 0
        required_credits = jimeng_outpainting_service.get_credits_cost()

        if user_credits < required_credits:
            raise HTTPException(
                status_code=402, detail=f"积分不足，需要 {required_credits} 积分"
            )

        # 生成任务ID
        task_id = (
            f"outpainting_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        )

        # 创建任务记录
        task = JimengOutpaintingTask(
            id=task_id,
            user_id=user.id,
            original_image_url=request.original_image_url,
            mask_image_url=request.mask_image_url,
            expansion_mode=request.expansion_mode,
            custom_prompt=request.custom_prompt,
            top=request.top,
            bottom=request.bottom,
            left=request.left,
            right=request.right,
            steps=request.steps,
            strength=request.strength,
            scale=request.scale,
            seed=request.seed,
            quality=request.quality,
            max_width=request.max_width,
            max_height=request.max_height,
            credits_cost=required_credits,
            status="submitted",
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        # 提交到即梦API
        try:
            logger.info(
                f"🎨 【即梦智能扩图】开始提交任务，模式: {request.expansion_mode}"
            )
            api_result = await jimeng_outpainting_service.submit_task(request.dict())
            logger.info(f"🎨 【即梦智能扩图】API调用完成，结果: {api_result}")

            if api_result.get("success"):
                # 更新任务状态
                task.status = "succeed"
                task.result_image_url = api_result.get("result_image_url")
                task.cloud_image_url = api_result.get(
                    "result_image_url"
                )  # 即梦直接返回云端URL
                task.request_id = api_result.get("request_id")
                task.progress = "100%"

                # 扣除积分
                from open_webui.models.credits import AddCreditForm, SetCreditFormDetail
                from decimal import Decimal

                Credits.add_credit_by_user_id(
                    AddCreditForm(
                        user_id=user.id,
                        amount=Decimal(-required_credits),  # 负数表示扣除
                        detail=SetCreditFormDetail(
                            api_path="/api/v1/jimeng-outpainting/tasks",
                            api_params={"task_id": task_id},
                            desc=f"即梦智能扩图任务: {task_id}",
                        ),
                    )
                )

                # 记录积分消费
                credit_record = JimengOutpaintingCredit(
                    user_id=user.id,
                    task_id=task_id,
                    credits_used=required_credits,
                    credits_before=user_credits,
                    credits_after=user_credits - required_credits,
                    operation_type="outpainting",
                    description=f"智能扩图 - {request.expansion_mode}模式",
                )
                db.add(credit_record)

            else:
                # API调用失败
                task.status = "failed"
                task.fail_reason = api_result.get("message", "未知错误")
                logger.info(f"🎨 【即梦智能扩图】任务失败，原因: {task.fail_reason}")

            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)

            return {
                "success": api_result.get("success", False),
                "task_id": task_id,
                "message": api_result.get("message", "任务处理完成"),
            }

        except Exception as api_error:
            # API调用异常，更新任务状态
            task.status = "failed"
            task.fail_reason = f"API调用异常: {str(api_error)}"
            task.updated_at = datetime.now()
            db.commit()

            logger.error(f"即梦智能扩图API调用失败: {str(api_error)}")
            raise HTTPException(
                status_code=500, detail=f"任务提交失败: {str(api_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交即梦智能扩图任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")
    finally:
        db.close()


@router.get("/tasks/{task_id}")
async def get_jimeng_outpainting_task_status(
    task_id: str, user: UserModel = Depends(get_verified_user)
):
    """获取即梦智能扩图任务状态"""
    db = SessionLocal()
    try:
        task = (
            db.query(JimengOutpaintingTask)
            .filter(
                JimengOutpaintingTask.id == task_id,
                JimengOutpaintingTask.user_id == user.id,
            )
            .first()
        )

        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")

        return JimengOutpaintingTaskResponse(
            id=task.id,
            user_id=task.user_id,
            original_image_url=task.original_image_url,
            mask_image_url=task.mask_image_url,
            expansion_mode=task.expansion_mode,
            custom_prompt=task.custom_prompt,
            top=task.top,
            bottom=task.bottom,
            left=task.left,
            right=task.right,
            steps=task.steps,
            strength=task.strength,
            scale=task.scale,
            seed=task.seed,
            quality=task.quality,
            max_width=task.max_width,
            max_height=task.max_height,
            status=task.status,
            progress=task.progress,
            fail_reason=task.fail_reason,
            result_image_url=task.result_image_url,
            cloud_image_url=task.cloud_image_url,
            request_id=task.request_id,
            credits_cost=task.credits_cost,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取任务状态失败")
    finally:
        db.close()


@router.get("/history")
async def get_jimeng_outpainting_history(
    page: int = 1, limit: int = 20, user: UserModel = Depends(get_verified_user)
):
    """获取即梦智能扩图历史记录"""
    db = SessionLocal()
    try:
        offset = (page - 1) * limit

        # 查询任务列表
        query = (
            db.query(JimengOutpaintingTask)
            .filter(JimengOutpaintingTask.user_id == user.id)
            .order_by(JimengOutpaintingTask.created_at.desc())
        )

        total = query.count()
        tasks = query.offset(offset).limit(limit).all()

        # 转换为响应格式
        task_responses = [
            JimengOutpaintingTaskResponse(
                id=task.id,
                user_id=task.user_id,
                original_image_url=task.original_image_url,
                mask_image_url=task.mask_image_url,
                expansion_mode=task.expansion_mode,
                custom_prompt=task.custom_prompt,
                top=task.top,
                bottom=task.bottom,
                left=task.left,
                right=task.right,
                steps=task.steps,
                strength=task.strength,
                scale=task.scale,
                seed=task.seed,
                quality=task.quality,
                max_width=task.max_width,
                max_height=task.max_height,
                status=task.status,
                progress=task.progress,
                fail_reason=task.fail_reason,
                result_image_url=task.result_image_url,
                cloud_image_url=task.cloud_image_url,
                request_id=task.request_id,
                credits_cost=task.credits_cost,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            for task in tasks
        ]

        return JimengOutpaintingHistoryResponse(
            data=task_responses, total=total, page=page, limit=limit
        )
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail="获取历史记录失败")
    finally:
        db.close()


@router.delete("/tasks/{task_id}")
async def delete_jimeng_outpainting_task(
    task_id: str, user: UserModel = Depends(get_verified_user)
):
    """删除即梦智能扩图任务"""
    db = SessionLocal()
    try:
        task = (
            db.query(JimengOutpaintingTask)
            .filter(
                JimengOutpaintingTask.id == task_id,
                JimengOutpaintingTask.user_id == user.id,
            )
            .first()
        )

        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")

        # 删除相关积分记录
        db.query(JimengOutpaintingCredit).filter(
            JimengOutpaintingCredit.task_id == task_id
        ).delete()

        # 删除任务
        db.delete(task)
        db.commit()

        return {"success": True, "message": "任务删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail="删除任务失败")
    finally:
        db.close()


@router.get("/credits")
async def get_jimeng_outpainting_credits(user: UserModel = Depends(get_verified_user)):
    """获取用户积分信息"""
    db = SessionLocal()
    try:
        from open_webui.models.credits import Credits

        # 获取当前积分余额
        credit_record = Credits.get_credit_by_user_id(user.id)
        balance = int(credit_record.credit) if credit_record else 0

        # 获取配置以获取积分消耗
        config = db.query(JimengOutpaintingConfig).first()
        credits_cost = config.credits_cost if config else 25

        # 获取今日使用积分
        today = datetime.now().date()
        today_used_count = (
            db.query(JimengOutpaintingCredit)
            .filter(
                JimengOutpaintingCredit.user_id == user.id,
                JimengOutpaintingCredit.created_at >= today,
            )
            .count()
        )
        today_used = today_used_count * credits_cost

        return JimengOutpaintingCreditsResponse(balance=balance, used_today=today_used)
    except Exception as e:
        logger.error(f"获取积分信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取积分信息失败")
    finally:
        db.close()


@router.get("/files/{file_id}")
async def get_outpainting_file(
    file_id: str, user: UserModel = Depends(get_verified_user)
):
    """获取即梦智能扩图上传的文件"""
    try:
        file_manager = get_file_manager()
        file_record = file_manager.file_table.get_file_by_id(file_id)

        if not file_record:
            raise HTTPException(status_code=404, detail="文件未找到")

        # 检查权限（用户只能访问自己的文件）
        if file_record.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权限访问该文件")

        # 如果有云端URL，直接重定向
        if file_record.cloud_url:
            from fastapi.responses import RedirectResponse

            return RedirectResponse(url=file_record.cloud_url)

        # 如果有本地路径，提供文件流
        if file_record.local_path and os.path.exists(file_record.local_path):

            def iterfile(file_path):
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk

            mime_type = file_record.mime_type or "application/octet-stream"
            return StreamingResponse(
                iterfile(file_record.local_path),
                media_type=mime_type,
                headers={
                    "Content-Disposition": f"inline; filename={file_record.filename}"
                },
            )

        raise HTTPException(status_code=404, detail="文件数据不可用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件失败: {e}")
        raise HTTPException(status_code=500, detail="获取文件失败")
