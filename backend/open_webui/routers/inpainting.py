"""
即梦涂抹消除功能路由器
提供配置管理、任务提交、历史记录等API接口
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from open_webui.models.inpainting import (
    InpaintingConfigs,
    InpaintingTasks,
    InpaintingConfigForm,
    InpaintingRequest,
    InpaintingTaskForm,
)
from open_webui.models.credits import Credits
from open_webui.utils.inpainting_api import (
    get_inpainting_client,
    get_inpainting_processor,
    InpaintingAPIError,
)
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_access, has_permission

logger = logging.getLogger(__name__)

router = APIRouter()

# ======================== 管理员配置接口 ========================


@router.get("/config")
async def get_inpainting_config(user=Depends(get_admin_user)):
    """获取涂抹消除配置（管理员）"""
    try:
        config = InpaintingConfigs.get_config()
        if config:
            config_dict = config.to_dict()
            # 隐藏敏感信息
            if config_dict.get("api_key"):
                config_dict["api_key"] = "***" + config_dict["api_key"][-4:]
            return config_dict
        else:
            return {
                "enabled": False,
                "base_url": "https://api.linkapi.org",
                "api_key": "",
                "credits_per_task": 50,
                "max_concurrent_tasks": 3,
                "task_timeout": 300000,
                "default_steps": 30,
                "default_strength": 0.8,
                "default_scale": 7.0,
                "default_quality": "M",
                "default_dilate_size": 15,
            }
    except Exception as e:
        logger.error(f"获取涂抹消除配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/config")
async def save_inpainting_config(
    config_form: InpaintingConfigForm, user=Depends(get_admin_user)
):
    """保存涂抹消除配置（管理员）"""
    try:
        config_data = config_form.dict()
        config = InpaintingConfigs.save_config(config_data)

        return {
            "success": True,
            "message": "配置保存成功",
            "config": config.to_dict(),
        }
    except Exception as e:
        logger.error(f"保存涂抹消除配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/config/user")
async def get_user_inpainting_config(user=Depends(get_verified_user)):
    """获取用户可见的涂抹消除配置"""
    try:
        config = InpaintingConfigs.get_config()
        if config and config.enabled:
            return {
                "enabled": True,
                "default_steps": config.default_steps,
                "default_strength": config.default_strength,
                "default_scale": config.default_scale,
                "default_quality": config.default_quality,
                "default_dilate_size": config.default_dilate_size,
                "credits_per_task": config.credits_per_task,
                "max_concurrent_tasks": config.max_concurrent_tasks,
            }
        else:
            return {"enabled": False}
    except Exception as e:
        logger.error(f"获取用户配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/test-connection")
async def test_inpainting_connection(user=Depends(get_admin_user)):
    """测试涂抹消除API连接（管理员）"""
    try:
        client = get_inpainting_client()
        result = await client.test_connection()
        return result
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        return {
            "success": False,
            "message": f"测试连接失败: {str(e)}",
            "error": str(e),
        }


# ======================== 任务管理接口 ========================


@router.post("/inpaint")
async def create_inpainting_task(
    task_form: InpaintingTaskForm, user=Depends(get_verified_user)
):
    """创建涂抹消除任务"""
    try:
        # 检查功能是否启用
        if not InpaintingConfigs.is_enabled():
            raise HTTPException(status_code=400, detail="涂抹消除功能未启用")

        # 验证输入参数
        request = task_form.request

        # 添加调试信息
        logger.info(f"🎨 【涂抹消除路由】收到任务请求，用户: {user.id}")
        logger.info(
            f"🎨 输入图片Base64长度: {len(request.input_image_base64) if request.input_image_base64 else 0}"
        )
        logger.info(
            f"🎨 Mask图片Base64长度: {len(request.mask_image_base64) if request.mask_image_base64 else 0}"
        )
        logger.info(
            f"🎨 参数: steps={request.steps}, strength={request.strength}, quality={request.quality}"
        )

        if not request.input_image_base64 or not request.input_image_base64.strip():
            raise HTTPException(status_code=400, detail="输入图片不能为空")

        if not request.mask_image_base64 or not request.mask_image_base64.strip():
            raise HTTPException(status_code=400, detail="Mask图片不能为空")

        # 检查系统积分是否足够（任务处理器会负责实际扣除）
        config = InpaintingConfigs.get_config()
        credits_required = config.credits_per_task if config else 50

        user_credits = Credits.get_credit_by_user_id(user.id)
        if not user_credits or float(user_credits.credit) < credits_required:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"积分不足，需要 {credits_required} 积分",
                    "required_credits": credits_required,
                    "current_credits": (
                        float(user_credits.credit) if user_credits else 0
                    ),
                },
            )

        # 提交任务
        processor = get_inpainting_processor()
        task_data = {
            "task_id": f"inpainting_{user.id}_{int(time.time() * 1000)}",
            "input_image_base64": request.input_image_base64,
            "mask_image_base64": request.mask_image_base64,
            "steps": request.steps,
            "strength": request.strength,
            "scale": request.scale,
            "quality": request.quality,
            "dilate_size": request.dilate_size,
            "seed": request.seed,
        }

        result = await processor.submit_inpainting_task(user.id, task_data)

        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result["message"],
                    "task_id": result["task_id"],
                    "result_image_url": result.get("result_image_url"),
                    "credits_consumed": result.get(
                        "credits_consumed", credits_required
                    ),
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result["message"],
                    "error": result.get("error"),
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建涂抹消除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/task/{task_id}")
async def get_inpainting_task(task_id: str, user=Depends(get_verified_user)):
    """获取涂抹消除任务详情"""
    try:
        task = InpaintingTasks.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 权限检查：只能查看自己的任务
        if task.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="无权访问此任务")

        return task.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")


@router.get("/tasks")
async def get_user_inpainting_tasks(
    limit: int = 50, offset: int = 0, user=Depends(get_verified_user)
):
    """获取用户涂抹消除任务列表"""
    try:
        tasks = InpaintingTasks.get_user_tasks(user.id, limit, offset)

        return {
            "tasks": [task.to_dict() for task in tasks],
            "total": len(tasks),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/history")
async def get_user_inpainting_history(
    page: int = 1, limit: int = 20, user=Depends(get_verified_user)
):
    """获取用户涂抹消除任务历史记录"""
    try:
        offset = (page - 1) * limit
        tasks = InpaintingTasks.get_user_tasks(user.id, limit, offset)

        return {
            "success": True,
            "data": [task.to_dict() for task in tasks],
            "total": len(tasks),
            "page": page,
            "limit": limit,
            "has_more": len(tasks) == limit,
        }

    except Exception as e:
        logger.error(f"获取任务历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务历史失败: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_inpainting_task(task_id: str, user=Depends(get_verified_user)):
    """删除涂抹消除任务"""
    try:
        task = InpaintingTasks.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 权限检查
        if task.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="无权删除此任务")

        # 只能删除已完成或失败的任务
        if task.status in ["submitted", "processing"]:
            raise HTTPException(status_code=400, detail="无法删除进行中的任务")

        success = InpaintingTasks.delete_task(task_id)
        if success:
            return {"success": True, "message": "任务删除成功"}
        else:
            raise HTTPException(status_code=500, detail="任务删除失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


# ======================== 图片上传接口 ========================


@router.post("/upload-image")
async def upload_image_for_inpainting(
    file: UploadFile = File(...), user=Depends(get_verified_user)
):
    """上传图片用于涂抹消除"""
    try:
        # 检查文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="请上传图片文件")

        # 检查文件大小 (限制5MB，根据即梦API文档)
        max_size = 5 * 1024 * 1024  # 5MB
        file_size = 0
        content = bytearray()

        while True:
            chunk = await file.read(8192)  # 8KB chunks
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > max_size:
                raise HTTPException(status_code=413, detail="图片文件不能超过5MB")
            content.extend(chunk)

        # 上传到云存储
        try:
            from open_webui.services.file_manager import get_file_manager

            file_manager = get_file_manager()

            # 生成文件名
            file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
            cloud_filename = f"inpainting_input/{user.id}/{uuid.uuid4().hex}.{file_ext}"

            # 上传文件
            upload_result = await file_manager.upload_file_content(
                content=bytes(content),
                filename=cloud_filename,
                content_type=file.content_type,
                metadata={
                    "user_id": user.id,
                    "original_filename": file.filename,
                    "file_size": file_size,
                    "upload_type": "inpainting_input",
                    "created_at": datetime.now().isoformat(),
                },
            )

            if upload_result["success"]:
                return {
                    "success": True,
                    "message": "图片上传成功",
                    "image_url": upload_result["url"],
                    "filename": cloud_filename,
                    "file_size": file_size,
                    "content_type": file.content_type,
                }
            else:
                raise HTTPException(
                    status_code=500, detail=f"上传失败: {upload_result['message']}"
                )

        except ImportError:
            raise HTTPException(status_code=500, detail="云存储服务不可用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")


# ======================== 积分管理接口 ========================


@router.get("/credits")
async def get_user_inpainting_credits(user=Depends(get_verified_user)):
    """获取用户系统积分"""
    try:
        credits = Credits.get_credit_by_user_id(user.id)
        return {
            "success": True,
            "balance": float(credits.credit) if credits else 0.0,
            "user_id": user.id,
        }

    except Exception as e:
        logger.error(f"获取用户积分失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取积分失败: {str(e)}")


# ======================== 健康检查 ========================


@router.get("/health")
async def inpainting_health_check():
    """健康检查"""
    try:
        config = InpaintingConfigs.get_config()
        return {
            "status": "healthy",
            "enabled": config.enabled if config else False,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
