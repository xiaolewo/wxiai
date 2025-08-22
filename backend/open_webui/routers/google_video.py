"""
谷歌视频生成 API 路由
实现完整的谷歌视频生成功能，包括文生视频、图生视频等
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import uuid
from datetime import datetime

from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.google_video import (
    GoogleVideoConfig,
    GoogleVideoTask,
    GoogleVideoCredit,
    GoogleVideoConfigForm,
    GoogleVideoTextToVideoRequest,
    GoogleVideoImageToVideoRequest,
    validate_image_to_video_request,
)
from open_webui.utils.google_video import (
    GoogleVideoApiClient,
    get_user_google_video_credits,
    deduct_user_google_video_credits,
    validate_user_google_video_credits,
    process_google_video_task_polling,
)
from open_webui.internal.db import get_db

router = APIRouter(prefix="/google-video", tags=["google_video"])

# 全局变量存储客户端
google_video_config = None
google_video_client = None


def get_google_video_client():
    """获取谷歌视频API客户端"""
    global google_video_client, google_video_config
    if not google_video_client or not google_video_config:
        config = GoogleVideoConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="谷歌视频服务未配置或已禁用")
        google_video_client = GoogleVideoApiClient(config)
        google_video_config = config
    return google_video_client


# ======================== 配置管理 ========================


@router.get("/config")
async def get_google_video_config(user=Depends(get_admin_user)):
    """获取谷歌视频配置 - 管理员专用"""
    config = GoogleVideoConfig.get_config()
    if not config:
        # 返回默认配置
        default_config = GoogleVideoConfig()
        return {
            "enabled": False,
            "base_url": "",
            "api_key": "",
            "default_text_model": "veo3",
            "default_image_model": "veo3-pro-frames",
            "default_enhance_prompt": False,
            "model_credits_config": default_config.get_default_model_credits(),
            "max_concurrent_tasks": 3,
            "task_timeout": 600000,
        }
    return config.to_dict()


@router.post("/config")
async def save_google_video_config(
    config_form: GoogleVideoConfigForm, user=Depends(get_admin_user)
):
    """保存谷歌视频配置 - 管理员专用"""
    try:
        # 清除全局客户端缓存
        global google_video_client, google_video_config
        google_video_client = None
        google_video_config = None

        # 保存配置
        config = GoogleVideoConfig.save_config(config_form.dict())
        return {"success": True, "message": "配置保存成功", "config": config.to_dict()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/config/user")
async def get_google_video_user_config(user=Depends(get_verified_user)):
    """获取谷歌视频用户配置 - 只返回用户需要的配置信息"""
    config = GoogleVideoConfig.get_config()
    if not config:
        return {
            "enabled": False,
            "default_text_model": "veo3",
            "default_image_model": "veo3-pro-frames",
            "default_enhance_prompt": False,
        }

    return {
        "enabled": config.enabled,
        "default_text_model": config.default_text_model,
        "default_image_model": config.default_image_model,
        "default_enhance_prompt": config.default_enhance_prompt,
        "model_credits_config": config.model_credits_config
        or config.get_default_model_credits(),
    }


@router.post("/test-connection")
async def test_google_video_connection(user=Depends(get_admin_user)):
    """测试谷歌视频API连接"""
    try:
        client = get_google_video_client()
        success = await client.test_connection()

        if success:
            return {"success": True, "message": "连接测试成功"}
        else:
            return {"success": False, "message": "连接测试失败"}

    except Exception as e:
        return {"success": False, "message": f"连接测试失败: {str(e)}"}


# ======================== 模型管理 ========================


@router.get("/models")
async def get_google_video_models(user=Depends(get_verified_user)):
    """获取支持的谷歌视频模型列表"""
    return {
        "text_to_video_models": [
            {"id": "veo3", "name": "Veo 3.0", "description": "最新版本，高质量输出"},
            {"id": "veo3-fast", "name": "Veo 3.0 Fast", "description": "快速生成版本"},
            {
                "id": "veo3-pro",
                "name": "Veo 3.0 Pro",
                "description": "专业版本，最高质量",
            },
            {
                "id": "veo3-pro-frames",
                "name": "Veo 3.0 Pro Frames",
                "description": "支持图生视频的专业版本",
            },
            {"id": "veo2", "name": "Veo 2.0", "description": "经典版本"},
            {"id": "veo2-fast", "name": "Veo 2.0 Fast", "description": "快速版本"},
            {"id": "veo2-pro", "name": "Veo 2.0 Pro", "description": "专业版本"},
            {
                "id": "veo3-fast-frames",
                "name": "Veo 3.0 Fast Frames",
                "description": "快速帧处理版本",
            },
            {
                "id": "veo2-fast-frames",
                "name": "Veo 2.0 Fast Frames",
                "description": "经典快速帧处理版本",
            },
            {
                "id": "veo2-fast-components",
                "name": "Veo 2.0 Fast Components",
                "description": "组件化快速生成",
            },
        ],
        "image_to_video_models": [
            {
                "id": "veo3-pro-frames",
                "name": "Veo 3.0 Pro Frames",
                "description": "支持图生视频的专业版本",
                "maxImages": 1,
                "imageType": "首帧",
            },
            {
                "id": "veo3-fast-frames",
                "name": "Veo 3.0 Fast Frames",
                "description": "快速图生视频",
                "maxImages": 1,
                "imageType": "首帧",
            },
            {
                "id": "veo2-fast-frames",
                "name": "Veo 2.0 Fast Frames",
                "description": "经典快速图生视频",
                "maxImages": 2,
                "imageType": "首尾帧",
            },
            {
                "id": "veo2-fast-components",
                "name": "Veo 2.0 Fast Components",
                "description": "组件化快速生成",
                "maxImages": 3,
                "imageType": "视频元素",
            },
        ],
    }


# ======================== 任务管理 ========================


@router.post("/text-to-video")
async def create_text_to_video_task(
    request: GoogleVideoTextToVideoRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """创建文生视频任务"""
    try:
        # 获取配置和客户端
        config = GoogleVideoConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="谷歌视频服务未启用")

        client = get_google_video_client()

        # 计算积分消耗
        credits_cost = config.get_credits_cost(request.model)

        # 验证用户积分
        if not validate_user_google_video_credits(user.id, credits_cost):
            current_credits = get_user_google_video_credits(user.id)
            raise HTTPException(
                status_code=400,
                detail=f"积分不足。当前积分: {current_credits}，需要积分: {credits_cost}",
            )

        # 扣除积分
        if not deduct_user_google_video_credits(
            user.id, credits_cost, "", "谷歌视频文生视频任务"
        ):
            raise HTTPException(status_code=400, detail="积分扣除失败")

        # 创建数据库任务记录
        task = GoogleVideoTask.create_task(
            user_id=user.id,
            task_type="text_to_video",
            prompt=request.prompt,
            model=request.model,
            enhance_prompt=request.enhance_prompt,
            credits_cost=credits_cost,
        )

        # 提交任务到API
        try:
            api_response = await client.submit_text_to_video(request)

            # 确保api_response是字典类型
            if not isinstance(api_response, dict):
                raise Exception(f"API返回格式错误: {str(api_response)}")

            # 检查API调用结果
            if api_response.get("code") == "success":
                # 更新任务信息
                task.update_from_api_response(api_response)

                # 启动后台轮询任务
                background_tasks.add_task(
                    process_google_video_task_polling, task, client
                )

                return {"success": True, "task_id": task.id, "task": task.to_dict()}
            else:
                # API返回错误
                error_msg = api_response.get("message", "未知API错误")
                raise Exception(f"API调用失败: {error_msg}")

        except Exception as e:
            # API调用失败，标记任务失败并回滚积分
            task.status = "FAILURE"
            task.fail_reason = str(e)
            with get_db() as db:
                db.merge(task)
                db.commit()

            # 回滚积分（如果积分系统可用）
            try:
                from open_webui.utils.kling import add_user_credits

                add_user_credits(
                    user.id, credits_cost, task.id, f"任务失败回滚积分: {task.id}"
                )
                print(
                    f"🎬 【谷歌视频】任务失败，已回滚积分 {credits_cost} 给用户 {user.id}"
                )
            except ImportError:
                print("⚠️ 【谷歌视频】积分系统不可用，无法回滚积分")
            except Exception as credit_error:
                print(f"⚠️ 【谷歌视频】积分回滚失败: {credit_error}")

            raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/image-to-video")
async def create_image_to_video_task(
    request: GoogleVideoImageToVideoRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """创建图生视频任务"""
    try:
        # 验证图片数量限制
        is_valid, error_msg = validate_image_to_video_request(
            request.model, request.images
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # 获取配置和客户端
        config = GoogleVideoConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="谷歌视频服务未启用")

        client = get_google_video_client()

        # 计算积分消耗
        credits_cost = config.get_credits_cost(request.model)

        # 验证用户积分
        if not validate_user_google_video_credits(user.id, credits_cost):
            current_credits = get_user_google_video_credits(user.id)
            raise HTTPException(
                status_code=400,
                detail=f"积分不足。当前积分: {current_credits}，需要积分: {credits_cost}",
            )

        # 扣除积分
        if not deduct_user_google_video_credits(
            user.id, credits_cost, "", "谷歌视频图生视频任务"
        ):
            raise HTTPException(status_code=400, detail="积分扣除失败")

        # 创建数据库任务记录
        task = GoogleVideoTask.create_task(
            user_id=user.id,
            task_type="image_to_video",
            prompt=request.prompt,
            model=request.model,
            enhance_prompt=request.enhance_prompt,
            credits_cost=credits_cost,
            input_images=request.images,
        )

        # 提交任务到API
        try:
            api_response = await client.submit_image_to_video(request)

            # 确保api_response是字典类型
            if not isinstance(api_response, dict):
                raise Exception(f"API返回格式错误: {str(api_response)}")

            # 检查API调用结果
            if api_response.get("code") == "success":
                # 更新任务信息
                task.update_from_api_response(api_response)

                # 启动后台轮询任务
                background_tasks.add_task(
                    process_google_video_task_polling, task, client
                )

                return {"success": True, "task_id": task.id, "task": task.to_dict()}
            else:
                # API返回错误
                error_msg = api_response.get("message", "未知API错误")
                raise Exception(f"API调用失败: {error_msg}")

        except Exception as e:
            # API调用失败，标记任务失败并回滚积分
            task.status = "FAILURE"
            task.fail_reason = str(e)
            with get_db() as db:
                db.merge(task)
                db.commit()

            # 回滚积分（如果积分系统可用）
            try:
                from open_webui.utils.kling import add_user_credits

                add_user_credits(
                    user.id, credits_cost, task.id, f"任务失败回滚积分: {task.id}"
                )
                print(
                    f"🎬 【谷歌视频】任务失败，已回滚积分 {credits_cost} 给用户 {user.id}"
                )
            except ImportError:
                print("⚠️ 【谷歌视频】积分系统不可用，无法回滚积分")
            except Exception as credit_error:
                print(f"⚠️ 【谷歌视频】积分回滚失败: {credit_error}")

            raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/task/{task_id}")
async def get_task_status(task_id: str, user=Depends(get_verified_user)):
    """获取任务状态"""
    try:
        task = GoogleVideoTask.get_task_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问此任务")

        return {"success": True, "task": task.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_task(task_id: str, user=Depends(get_verified_user)):
    """删除任务"""
    try:
        task = GoogleVideoTask.get_task_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问此任务")

        # 删除任务记录
        with get_db() as db:
            db.delete(task)
            db.commit()

        return {"success": True, "message": "任务已删除"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


@router.get("/history")
async def get_user_task_history(
    page: int = 1,
    limit: int = 20,
    user=Depends(get_verified_user),
):
    """获取用户任务历史记录"""
    try:
        tasks = GoogleVideoTask.get_user_tasks(user.id, page, limit)
        task_list = [task.to_dict() for task in tasks]

        return {
            "success": True,
            "tasks": task_list,
            "page": page,
            "limit": limit,
            "total": len(task_list),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


# ======================== 文件管理 ========================


@router.post("/upload-image")
async def upload_image_for_video(
    file: UploadFile = File(...),
    user=Depends(get_verified_user),
):
    """上传图片用于图生视频"""
    try:
        # 验证文件类型
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只支持图片文件")

        # 验证文件大小 (最大10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

        # 上传到云存储
        try:
            from open_webui.services.file_manager import get_file_manager

            file_manager = get_file_manager()

            cloud_url = await file_manager.upload_file_content(
                file_content=file_content,
                filename=file.filename,
                user_id=user.id,
                source_type="google_video_input",
                file_type="image",
            )

            if cloud_url:
                return {"success": True, "url": cloud_url}
            else:
                raise HTTPException(status_code=500, detail="图片上传失败")
        except ImportError:
            # 如果文件管理器不存在，返回base64
            import base64

            base64_content = base64.b64encode(file_content).decode()
            return {
                "success": True,
                "url": f"data:{file.content_type};base64,{base64_content}",
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传图片失败: {str(e)}")


# ======================== 积分管理 ========================


@router.get("/credits")
async def get_user_credits(user=Depends(get_verified_user)):
    """获取用户谷歌视频积分余额"""
    try:
        credits = get_user_google_video_credits(user.id)
        return {"success": True, "balance": credits}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取积分失败: {str(e)}")


# ======================== 服务监控 ========================


@router.get("/health")
async def health_check():
    """服务健康检查"""
    try:
        config = GoogleVideoConfig.get_config()

        return {
            "success": True,
            "service": "google_video",
            "status": "healthy",
            "enabled": config.enabled if config else False,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "service": "google_video",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
