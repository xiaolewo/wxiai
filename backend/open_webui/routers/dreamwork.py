"""
DreamWork (即梦) API Router
实现完整的即梦图像生成功能，包括文生图、图生图等
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import json
import asyncio
from datetime import datetime, timedelta
import uuid

from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.config import CACHE_DIR
from open_webui.internal.db import get_db
from open_webui.models.dreamwork import (
    DreamWorkConfig,
    DreamWorkTask,
    DreamWorkConfigForm,
    DreamWorkTaskForm,
    DreamWorkGenerateRequest,
)
from open_webui.utils.dreamwork import (
    DreamWorkApiClient,
    deduct_user_credits,
    add_user_credits,
    get_user_credit_balance,
    validate_user_credits,
    process_dreamwork_generation,
)
from open_webui.services.file_manager import get_file_manager

# 导入修复版函数
from open_webui.utils.dreamwork_fixed import generate_image_to_image_fixed

router = APIRouter(prefix="/dreamwork", tags=["dreamwork"])

# 全局变量存储DreamWork配置
dreamwork_config = None
dreamwork_client = None


def get_dreamwork_client():
    """获取DreamWork API客户端"""
    global dreamwork_client, dreamwork_config
    if not dreamwork_client or not dreamwork_config:
        config = DreamWorkConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(
                status_code=400, detail="DreamWork service not configured or disabled"
            )
        dreamwork_client = DreamWorkApiClient(config)
        dreamwork_config = config
    return dreamwork_client


# ======================== 配置管理 ========================


@router.get("/config")
async def get_dreamwork_config(user=Depends(get_admin_user)):
    """获取DreamWork配置 - 管理员专用"""
    config = DreamWorkConfig.get_config()
    if not config:
        # 返回默认配置
        return {
            "enabled": False,
            "base_url": "",
            "api_key": "",
            "text_to_image_model": "doubao-seedream-3-0-t2i-250415",
            "image_to_image_model": "doubao-seededit-3-0-i2i-250628",
            "default_size": "1024x1024",
            "default_guidance_scale": 2.5,
            "watermark_enabled": True,
            "credits_per_generation": 10,
            "max_concurrent_tasks": 5,
            "task_timeout": 300000,
        }
    return config.to_dict()


@router.get("/config/user")
async def get_dreamwork_user_config(user=Depends(get_verified_user)):
    """获取DreamWork用户配置 - 只返回用户需要的配置信息（不包含敏感信息）"""
    config = DreamWorkConfig.get_config()
    if not config:
        # 返回默认用户配置
        return {
            "enabled": False,
            "text_to_image_model": "doubao-seedream-3-0-t2i-250415",
            "image_to_image_model": "doubao-seededit-3-0-i2i-250628",
            "default_size": "1024x1024",
            "default_guidance_scale": 2.5,
            "watermark_enabled": True,
            "credits_per_generation": 10,
        }

    # 只返回用户需要的配置，不包含敏感信息
    return {
        "enabled": config.enabled,
        "text_to_image_model": config.text_to_image_model,
        "image_to_image_model": config.image_to_image_model,
        "default_size": config.default_size,
        "default_guidance_scale": config.default_guidance_scale,
        "watermark_enabled": config.watermark_enabled,
        "credits_per_generation": config.credits_per_generation,
    }


@router.post("/config")
async def save_dreamwork_config(config_data: dict, user=Depends(get_admin_user)):
    """保存DreamWork配置 - 管理员专用"""
    global dreamwork_client, dreamwork_config

    try:
        # 验证必需字段
        enabled = config_data.get("enabled", False)
        if enabled and (
            not config_data.get("base_url") or not config_data.get("api_key")
        ):
            raise HTTPException(
                status_code=400, detail="Base URL and API Key are required when enabled"
            )

        # 设置默认值
        config_data.setdefault("text_to_image_model", "doubao-seedream-3-0-t2i-250415")
        config_data.setdefault("image_to_image_model", "doubao-seededit-3-0-i2i-250628")
        config_data.setdefault("default_size", "1024x1024")
        config_data.setdefault("default_guidance_scale", 2.5)
        config_data.setdefault("watermark_enabled", True)
        config_data.setdefault("credits_per_generation", 10)
        config_data.setdefault("max_concurrent_tasks", 5)
        config_data.setdefault("task_timeout", 300000)

        # 保存配置
        config = DreamWorkConfig.save_config(config_data)

        # 重置客户端
        dreamwork_client = None
        dreamwork_config = None

        return {
            "message": "Configuration saved successfully",
            "config": config.to_dict(),
        }
    except Exception as e:
        import traceback

        print(f"Error saving DreamWork config: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to save configuration: {str(e)}"
        )


@router.get("/test/simple")
async def test_dreamwork_simple(user=Depends(get_admin_user)):
    """简单测试DreamWork配置 - 不需要真实API"""
    try:
        config = DreamWorkConfig.get_config()
        if not config:
            return {"status": "error", "message": "DreamWork service not configured"}

        return {
            "status": "success",
            "message": "DreamWork configuration found",
            "config": {
                "enabled": config.enabled,
                "base_url": config.base_url,
                "has_api_key": bool(config.api_key),
                "text_to_image_model": config.text_to_image_model,
                "image_to_image_model": config.image_to_image_model,
            },
        }
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}


@router.get("/test")
async def test_dreamwork_connection(user=Depends(get_admin_user)):
    """测试DreamWork连接 - 管理员专用"""
    try:
        # 检查配置是否存在
        config = DreamWorkConfig.get_config()
        if not config:
            raise HTTPException(
                status_code=400, detail="DreamWork service not configured"
            )

        print(
            f"🎨 【DreamWork测试】配置检查: enabled={config.enabled}, base_url={config.base_url}, api_key={'***' if config.api_key else 'None'}"
        )

        if not config.enabled:
            raise HTTPException(status_code=400, detail="DreamWork service is disabled")

        if not config.base_url or not config.api_key:
            raise HTTPException(
                status_code=400, detail="Base URL and API Key are required"
            )

        # 构建测试URL
        test_url = f"{config.base_url.rstrip('/')}/v1/images/generations"
        print(f"🎨 【DreamWork测试】测试URL: {test_url}")

        # 简单测试 - 分步骤检查连接
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            try:
                # 第一步：简单的健康检查（如果有的话）
                try:
                    base_response = await http_client.get(
                        config.base_url.rstrip("/"), timeout=10.0
                    )
                    print(
                        f"🎨 【DreamWork测试】基础连接测试: {base_response.status_code}"
                    )
                except Exception as e:
                    print(f"🎨 【DreamWork测试】基础连接失败: {e}")

                # 第二步：测试API端点
                test_payload = {
                    "model": config.text_to_image_model,
                    "prompt": "test connection",
                    "size": "1024x1024",
                    "response_format": "url",
                }

                print(f"🎨 【DreamWork测试】请求数据: {test_payload}")

                response = await http_client.post(
                    test_url,
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=test_payload,
                    timeout=15.0,
                )

                print(f"🎨 【DreamWork测试】响应状态: {response.status_code}")
                print(f"🎨 【DreamWork测试】响应内容: {response.text[:200]}...")

                # 如果API返回任何响应（即使是错误），说明连接成功
                if response.status_code in [200, 400, 401, 403, 422]:
                    return {
                        "message": "Connection test successful",
                        "status_code": response.status_code,
                        "response_preview": (
                            response.text[:100] if response.text else "No content"
                        ),
                        "note": (
                            "API endpoint is reachable"
                            if response.status_code == 200
                            else "API endpoint reachable but returned error (check credentials/parameters)"
                        ),
                    }
                else:
                    return {
                        "message": "Connection test completed with unexpected status",
                        "status_code": response.status_code,
                        "response_preview": (
                            response.text[:100] if response.text else "No content"
                        ),
                    }

            except httpx.ConnectError as e:
                print(f"❌ 【DreamWork测试】连接错误: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot connect to DreamWork API server: {str(e)}",
                )
            except httpx.TimeoutException as e:
                print(f"❌ 【DreamWork测试】超时错误: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Connection to DreamWork API timed out: {str(e)}",
                )
            except Exception as e:
                print(f"❌ 【DreamWork测试】其他错误: {e}")
                raise HTTPException(status_code=400, detail=f"Request failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【DreamWork测试】系统错误: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


# ======================== 任务提交 ========================


@router.post("/submit/text-to-image")
async def submit_text_to_image_task(
    request: DreamWorkGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """提交文生图任务"""
    try:
        print(f"🎨 【DreamWork后端】收到文生图请求: 用户={user.id}")
        print(
            f"🎨 【DreamWork后端】请求参数: model={request.model}, prompt={request.prompt[:50]}..., size={request.size}"
        )
        print(
            f"🎨 【DreamWork后端】其他参数: guidance_scale={request.guidance_scale}, seed={request.seed}, watermark={request.watermark}"
        )

        # 使用工具函数处理任务
        print(f"🎨 【DreamWork后端】开始处理文生图任务...")
        task = await process_dreamwork_generation(
            user_id=user.id, request=request, action="TEXT_TO_IMAGE"
        )

        print(f"🎨 【DreamWork后端】任务创建成功: {task.id}")
        return {
            "success": True,
            "task_id": task.id,
            "message": "Text-to-image task submitted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【DreamWork后端】文生图任务提交失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to submit text-to-image task: {str(e)}"
        )


@router.post("/submit/image-to-image")
async def submit_image_to_image_task(
    request: DreamWorkGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """提交图生图任务"""
    try:
        print(f"🎨 【DreamWork后端】收到图生图请求: 用户={user.id}")
        print(
            f"🎨 【DreamWork后端】请求参数: model={request.model}, prompt={request.prompt[:50]}..., size={request.size}"
        )
        print(
            f"🎨 【DreamWork后端】输入图片: {len(request.image) if request.image else 0}字符"
        )
        print(
            f"🎨 【DreamWork后端】其他参数: guidance_scale={request.guidance_scale}, seed={request.seed}, watermark={request.watermark}"
        )

        # 验证输入图片
        if not request.image:
            print("❌ 【DreamWork后端】缺少输入图片")
            raise HTTPException(
                status_code=400,
                detail="Input image is required for image-to-image generation",
            )

        # 验证图片数据基本格式
        image_data = request.image.strip()
        if len(image_data) < 100:
            print(f"❌ 【DreamWork后端】图片数据太短: {len(image_data)}字符")
            raise HTTPException(
                status_code=400,
                detail=f"Image data too short: {len(image_data)} characters",
            )

        # 记录图片数据前缀用于调试
        prefix = image_data[:50] if len(image_data) > 50 else image_data
        print(f"🎨 【DreamWork后端】图片数据前缀: {prefix}...")

        # 使用修复版API进行图生图处理
        print(f"🎨 【DreamWork后端】开始处理图生图任务（使用修复版API）...")

        # 检查配置
        config = DreamWorkConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(
                status_code=400, detail="DreamWork service not configured or disabled"
            )

        # 验证积分
        if not validate_user_credits(user.id, config.credits_per_generation):
            raise HTTPException(status_code=400, detail="Insufficient credits")

        # 扣除积分
        deduct_user_credits(
            user.id, config.credits_per_generation, "DreamWork-IMAGE_TO_IMAGE"
        )

        # 创建任务记录
        task = DreamWorkTask.create_task(
            user_id=user.id,
            action="IMAGE_TO_IMAGE",
            prompt=request.prompt,
            model=request.model or config.image_to_image_model,
            size=request.size or config.default_size,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            watermark=request.watermark,
            credits_cost=config.credits_per_generation,
            input_image=request.image,
            properties={
                "serviceType": "dreamwork",
                "model": request.model or config.image_to_image_model,
                "size": request.size or config.default_size,
            },
        )

        try:
            # 使用修复版API调用
            api_response = await generate_image_to_image_fixed(config, request)

            # 更新任务状态
            task.update_from_api_response(api_response)

            # 🔥 如果任务成功且有图片URL，自动上传到云存储
            if task.status == "SUCCESS" and task.image_url:
                try:
                    with get_db() as db:
                        file_manager = get_file_manager()
                        success, message, file_record = (
                            await file_manager.save_generated_content(
                                user_id=user.id,
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
                                    "action": "IMAGE_TO_IMAGE",
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
                                update_db.commit()
                            print(
                                f"☁️ 【云存储】DreamWork图生图上传成功，已更新URL: {task.id}"
                            )
                        else:
                            print(
                                f"☁️ 【云存储】DreamWork图生图上传失败: {task.id} - {message}"
                            )
                except Exception as upload_error:
                    print(
                        f"☁️ 【云存储】DreamWork图生图自动上传异常: {task.id} - {upload_error}"
                    )

        except Exception as e:
            print(f"❌ 【DreamWork后端】修复版API调用失败: {e}")
            # 发生错误时退还积分
            add_user_credits(
                user.id,
                config.credits_per_generation,
                "DreamWork-IMAGE_TO_IMAGE-error-refund",
                task.id,
            )
            task.update_status("FAILURE")
            task.fail_reason = str(e)
            raise HTTPException(status_code=500, detail=str(e))

        print(f"🎨 【DreamWork后端】任务创建成功: {task.id}")
        return {
            "success": True,
            "task_id": task.id,
            "message": "Image-to-image task submitted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【DreamWork后端】图生图任务提交失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to submit image-to-image task: {str(e)}"
        )


# ======================== 任务查询 ========================


@router.get("/task/{task_id}")
async def get_dreamwork_task_status(task_id: str, user=Depends(get_verified_user)):
    """获取任务状态"""
    try:
        print(f"🎨 【DreamWork API】获取任务状态: {task_id}, 用户: {user.id}")

        # 先查本地数据库
        task = DreamWorkTask.get_task_by_id(task_id)
        print(
            f"🎨 【DreamWork API】本地任务: {task.id if task else 'None'}, 状态: {task.status if task else 'None'}"
        )

        # 验证任务所有权
        if not task or task.user_id != user.id:
            raise HTTPException(
                status_code=404, detail="Task not found or access denied"
            )

        # 如果任务已完成，直接返回
        if task.status in ["SUCCESS", "FAILURE"]:
            print(f"🎨 【DreamWork API】任务已完成: {task.id}")

            # 🔥 检查是否需要补充上传到云存储
            if task.status == "SUCCESS" and task.image_url:
                try:
                    with get_db() as db:
                        file_manager = get_file_manager()
                        # 检查是否已经上传过
                        existing_files = file_manager.file_table.get_files_by_source(
                            "dreamwork", task.id
                        )
                        if not any(f.status == "uploaded" for f in existing_files):
                            success, message, file_record = (
                                await file_manager.save_generated_content(
                                    user_id=user.id,
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
                                        "action": task.action,
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
                                        update_task.cloud_image_url = (
                                            file_record.cloud_url
                                        )
                                        update_db.commit()
                                print(
                                    f"☁️ 【云存储】DreamWork补充上传成功，已更新URL: {task.id}"
                                )
                            else:
                                print(
                                    f"☁️ 【云存储】DreamWork补充上传失败: {task.id} - {message}"
                                )
                        else:
                            print(
                                f"☁️ 【云存储】DreamWork图片已存在，跳过上传: {task.id}"
                            )
                except Exception as upload_error:
                    print(
                        f"☁️ 【云存储】DreamWork补充上传异常: {task.id} - {upload_error}"
                    )

            return task.to_dict()

        # 如果任务还在进行中，可以选择查询远程状态（DreamWork API是同步的，所以通常不需要）
        return task.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【DreamWork API】获取任务状态失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


# ======================== 用户功能 ========================


@router.get("/history")
async def get_user_dreamwork_history(
    page: int = 1, limit: int = 20, user=Depends(get_verified_user)
):
    """获取用户任务历史"""
    try:
        tasks = DreamWorkTask.get_user_tasks(user.id, page, limit)
        total = DreamWorkTask.get_user_task_count(user.id)

        return {
            "data": [task.to_dict() for task in tasks],
            "total": total,
            "page": page,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task history: {str(e)}"
        )


@router.get("/credits")
async def get_user_dreamwork_credits(user=Depends(get_verified_user)):
    """获取用户积分余额"""
    try:
        balance = get_user_credit_balance(user.id)
        return {"balance": balance}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get credits: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_dreamwork_task(task_id: str, user=Depends(get_verified_user)):
    """删除用户任务"""
    try:
        # 验证任务所有权
        task = DreamWorkTask.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 删除任务记录
        with get_db() as db:
            db.delete(task)
            db.commit()

        return {"message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


# ======================== 统计功能 ========================


@router.get("/stats/system")
async def get_dreamwork_system_stats(user=Depends(get_admin_user)):
    """获取系统DreamWork统计 - 管理员专用"""
    try:
        from open_webui.utils.dreamwork import get_system_dreamwork_stats

        stats = get_system_dreamwork_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get system stats: {str(e)}"
        )


@router.get("/stats/user")
async def get_dreamwork_user_stats(user=Depends(get_verified_user)):
    """获取用户DreamWork统计"""
    try:
        from open_webui.utils.dreamwork import get_user_dreamwork_stats

        stats = get_user_dreamwork_stats(user.id)
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user stats: {str(e)}"
        )


# ======================== 管理员功能 ========================


@router.post("/admin/credits/add")
async def admin_add_dreamwork_credits(
    target_user_id: str, amount: int, reason: str = "", user=Depends(get_admin_user)
):
    """管理员给用户充值积分"""
    try:
        from open_webui.utils.dreamwork import admin_add_credits_to_user

        new_balance = admin_add_credits_to_user(user.id, target_user_id, amount, reason)
        return {
            "message": f"Added {amount} credits to user {target_user_id}",
            "new_balance": new_balance,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add credits: {str(e)}")


@router.post("/admin/credits/deduct")
async def admin_deduct_dreamwork_credits(
    target_user_id: str, amount: int, reason: str = "", user=Depends(get_admin_user)
):
    """管理员扣除用户积分"""
    try:
        from open_webui.utils.dreamwork import admin_deduct_credits_from_user

        new_balance = admin_deduct_credits_from_user(
            user.id, target_user_id, amount, reason
        )
        return {
            "message": f"Deducted {amount} credits from user {target_user_id}",
            "new_balance": new_balance,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to deduct credits: {str(e)}"
        )


@router.post("/admin/cleanup")
async def admin_cleanup_old_tasks(days: int = 30, user=Depends(get_admin_user)):
    """管理员清理旧任务记录"""
    try:
        from open_webui.utils.dreamwork import cleanup_old_tasks

        deleted_count = cleanup_old_tasks(days)
        return {
            "message": f"Cleaned up {deleted_count} old tasks (older than {days} days)"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup tasks: {str(e)}"
        )
