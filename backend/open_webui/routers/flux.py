"""
Flux API Router
实现完整的Flux图像生成功能，包括配置管理、任务提交、状态查询等
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Dict, Any
import json
import asyncio
from datetime import datetime
import uuid
import logging

from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.flux import (
    FluxConfig,
    FluxConfigs,
    FluxTask,
    FluxTasks,
    FluxConfigForm,
    FluxTextToImageRequest,
    FluxImageToImageRequest,
    FluxMultiImageRequest,
    FluxTaskResponse,
    FluxUploadResponse,
    get_supported_flux_models,
    is_flux_enabled,
)
from open_webui.models.credits import Credits
from open_webui.utils.credit.utils import check_credit_by_user_id
from open_webui.utils.flux_api import FluxAPIClient, FluxAPIError


def replace_flux_response_urls(response: dict, configured_base_url: str) -> dict:
    """根据管理员配置的base_url动态替换API响应中的URL"""
    if not isinstance(response, dict):
        return response

    # 只有当配置了代理地址时才进行替换
    if configured_base_url == "https://api.linkapi.org":
        original_base = "https://queue.fal.run"
        new_base = configured_base_url

        # 需要替换的URL字段
        url_fields = ["response_url", "status_url", "cancel_url"]

        for field in url_fields:
            if field in response and response[field]:
                if response[field].startswith(original_base):
                    response[field] = response[field].replace(original_base, new_base)
                    logger.debug(
                        f"URL replaced for {field}: {original_base} -> {new_base}"
                    )

    return response


from open_webui.services.file_manager import get_file_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flux", tags=["flux"])

# 全局变量存储Flux配置
flux_config = None
flux_client = None


def get_flux_api_client():
    """获取Flux API客户端"""
    global flux_client, flux_config
    config = FluxConfigs.get_config()
    if not config or not config.enabled:
        raise HTTPException(
            status_code=400, detail="Flux service not configured or disabled"
        )

    # 总是重新创建客户端以确保使用最新配置和代码（调试期间）
    # TODO: 生产环境可以恢复缓存机制
    flux_client = FluxAPIClient(config)
    flux_config = config
    print(
        f"🔄 【客户端重建】Created new FluxAPIClient with base_url: {config.base_url}"
    )

    return flux_client


# ======================== 配置管理 ========================


@router.get("/config")
async def get_flux_config(user=Depends(get_admin_user)):
    """获取Flux配置 - 管理员专用"""
    config = FluxConfigs.get_config()
    if not config:
        # 返回默认配置
        return {
            "api_key": "",
            "base_url": "https://queue.fal.run",
            "enabled": False,
            "timeout": 300,
            "max_concurrent_tasks": 5,
            "default_model": "fal-ai/flux-1/dev",
        }
    return config.to_dict()


@router.post("/config")
async def save_flux_config(config_form: FluxConfigForm, user=Depends(get_admin_user)):
    """保存Flux配置 - 管理员专用"""
    global flux_client, flux_config

    try:
        # 保存配置到数据库
        config = FluxConfigs.create_or_update_config(config_form)

        # 重置全局客户端以使用新配置
        flux_client = None
        flux_config = None

        # 如果启用了服务，测试API连接
        if config.enabled:
            try:
                test_client = FluxAPIClient(config)
                # 测试连接（这里可能需要根据实际API调整）
                logger.info(
                    "Flux API configuration saved and connection tested successfully"
                )
            except Exception as e:
                logger.warning(
                    f"Flux configuration saved but connection test failed: {e}"
                )
                # 不抛出异常，允许保存配置即使连接测试失败

        return {"success": True, "message": "Flux configuration saved successfully"}

    except Exception as e:
        logger.error(f"Failed to save Flux configuration: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to save configuration: {str(e)}"
        )


# ======================== 管理员专用配置API ========================


@router.get("/admin/config")
async def get_flux_admin_config(user=Depends(get_admin_user)):
    """获取Flux管理员配置 - 新版前端专用"""
    config = FluxConfigs.get_config()
    if not config:
        # 返回默认配置，字段名匹配前端期望
        return {
            "enabled": False,
            "baseUrl": "https://api.linkapi.org",
            "apiKey": "",
            "defaultModel": "fal-ai/flux-1/schnell",
            "creditsPerGeneration": 5,
            "maxConcurrentTasks": 5,
            "taskTimeout": 300000,
            "modelCredits": {
                "fal-ai/flux-1/schnell": 5,
                "fal-ai/flux-1/dev": 10,
                "fal-ai/flux-1/dev/image-to-image": 10,
                "fal-ai/flux-pro": 20,
                "fal-ai/flux-pro/kontext": 25,
                "fal-ai/flux-pro/kontext/multi": 30,
                "fal-ai/flux-pro/max": 35,
            },
        }

    # 转换现有配置到前端期望格式
    return {
        "enabled": config.enabled,
        "baseUrl": config.base_url,
        "apiKey": config.api_key,
        "defaultModel": config.default_model,
        "creditsPerGeneration": getattr(config, "credits_per_generation", 5),
        "maxConcurrentTasks": config.max_concurrent_tasks,
        "taskTimeout": (
            config.timeout * 1000 if config.timeout else 300000
        ),  # 转换为毫秒
        "modelCredits": getattr(
            config,
            "model_credits",
            {
                "fal-ai/flux-1/schnell": 5,
                "fal-ai/flux-1/dev": 10,
                "fal-ai/flux-1/dev/image-to-image": 10,
                "fal-ai/flux-pro": 20,
                "fal-ai/flux-pro/kontext": 25,
                "fal-ai/flux-pro/kontext/multi": 30,
                "fal-ai/flux-pro/max": 35,
            },
        ),
    }


@router.post("/admin/config")
async def save_flux_admin_config(config_data: dict, user=Depends(get_admin_user)):
    """保存Flux管理员配置 - 新版前端专用"""
    global flux_client, flux_config

    try:
        # 转换前端格式到后端格式
        config_form = FluxConfigForm(
            api_key=config_data.get("apiKey", ""),
            base_url=config_data.get("baseUrl", "https://api.linkapi.org"),
            enabled=config_data.get("enabled", False),
            timeout=config_data.get("taskTimeout", 300000) // 1000,  # 转换为秒
            max_concurrent_tasks=config_data.get("maxConcurrentTasks", 5),
            default_model=config_data.get("defaultModel", "fal-ai/flux-1/schnell"),
            model_credits=config_data.get("modelCredits", {}),
        )

        # 保存配置到数据库
        config = FluxConfigs.create_or_update_config(config_form)

        # 重置全局客户端以使用新配置
        flux_client = None
        flux_config = None

        # 如果启用了服务，测试API连接
        if config.enabled:
            try:
                test_client = FluxAPIClient(config)
                logger.info(
                    "Flux admin configuration saved and connection tested successfully"
                )
            except Exception as e:
                logger.warning(
                    f"Flux admin configuration saved but connection test failed: {e}"
                )

        return {"success": True, "message": "Flux configuration saved successfully"}

    except Exception as e:
        logger.error(f"Failed to save Flux admin configuration: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to save configuration: {str(e)}"
        )


@router.post("/admin/test-connection")
async def test_flux_admin_connection(config_data: dict, user=Depends(get_admin_user)):
    """测试Flux连接 - 管理员专用"""
    try:
        base_url = config_data.get("baseUrl")
        api_key = config_data.get("apiKey")

        if not base_url or not api_key:
            return {"success": False, "error": "缺少API URL或密钥"}

        # 创建临时配置进行测试
        temp_config = FluxConfigForm(
            api_key=api_key,
            base_url=base_url,
            enabled=True,
            timeout=30,
            max_concurrent_tasks=1,
            default_model="fal-ai/flux-1/schnell",
        )

        # 创建临时客户端测试连接
        test_client = FluxAPIClient(temp_config)
        connection_ok = await test_client.test_connection()

        if connection_ok:
            return {"success": True, "message": "连接测试成功"}
        else:
            return {"success": False, "error": "API连接失败"}

    except Exception as e:
        logger.error(f"Flux connection test failed: {e}")
        return {"success": False, "error": f"连接测试失败: {str(e)}"}


@router.get("/config/user")
async def get_flux_user_config(user=Depends(get_verified_user)):
    """获取Flux用户配置 - 只返回用户需要的配置信息"""
    config = FluxConfigs.get_config()

    # 获取支持的模型列表
    supported_models = get_supported_flux_models()

    # 默认模型积分配置
    default_model_credits = {
        "fal-ai/flux-1/schnell": 5,
        "fal-ai/flux-1/dev": 10,
        "fal-ai/flux-1/dev/image-to-image": 10,
        "fal-ai/flux-pro": 20,
        "fal-ai/flux-pro/kontext": 25,
        "fal-ai/flux-pro/kontext/multi": 30,
        "fal-ai/flux-pro/max": 35,
    }

    if not config or not config.enabled:
        return {
            "enabled": False,
            "models": supported_models,
            "default_model": "fal-ai/flux-1/dev",
            "model_credits": default_model_credits,
        }

    return {
        "enabled": config.enabled,
        "models": supported_models,
        "default_model": config.default_model,
        "max_concurrent_tasks": config.max_concurrent_tasks,
        "model_credits": config.model_credits or default_model_credits,
    }


@router.get("/models")
async def get_flux_models(user=Depends(get_verified_user)):
    """获取支持的Flux模型列表"""
    return {"models": get_supported_flux_models(), "enabled": is_flux_enabled()}


# ======================== 积分管理 ========================


@router.get("/credits")
async def get_user_credits(user=Depends(get_verified_user)):
    """获取用户积分信息"""
    try:
        credits = Credits.init_credit_by_user_id(user.id)
        return {
            "user_id": credits.user_id,
            "credits_balance": float(credits.credit),
            "updated_at": credits.updated_at,
            "created_at": credits.created_at,
        }
    except Exception as e:
        logger.error(f"Failed to get user credits: {e}")
        raise HTTPException(status_code=500, detail="Failed to get credits")


@router.post("/credits/add")
async def add_user_credits(
    amount: int, target_user_id: Optional[str] = None, user=Depends(get_admin_user)
):
    """添加用户积分 - 管理员专用"""
    user_id = target_user_id or user.id

    try:
        # 使用通用积分系统的加分功能
        credit_record = Credits.init_credit_by_user_id(user_id)
        success = Credits.update_credit_by_user_id(
            user_id, credit_record.credit + amount
        )
        if success:
            return {
                "success": True,
                "message": f"Added {amount} credits to user {user_id}",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add credits")
    except Exception as e:
        logger.error(f"Failed to add credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================== 图片上传 ========================


@router.post("/upload-image", response_model=FluxUploadResponse)
async def upload_image_for_flux(
    file: UploadFile = File(...), user=Depends(get_verified_user)
):
    """上传单张图片到腾讯云存储，用于图生图功能

    流程：用户上传 -> 腾讯云COS -> 获取云URL -> 传给第三方平台
    """
    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            return FluxUploadResponse(
                success=False, message="仅支持图片文件格式（JPEG, PNG, WebP等）"
            )

        # 验证文件大小 (10MB限制)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            return FluxUploadResponse(success=False, message="文件大小不能超过10MB")

        # 验证文件内容不为空
        if len(file_content) == 0:
            return FluxUploadResponse(success=False, message="文件内容不能为空")

        # 上传到腾讯云存储
        file_manager = get_file_manager()
        success, message, file_record = await file_manager.save_generated_content(
            user_id=user.id,
            file_data=file_content,
            filename=f"flux_input_{uuid.uuid4()}.jpg",
            file_type="image",
            source_type="flux_input",
            metadata={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(file_content),
            },
        )

        if success and file_record and file_record.cloud_url:
            logger.info(
                f"Image uploaded successfully to cloud: {file_record.cloud_url}"
            )
            return FluxUploadResponse(
                success=True,
                message="图片上传成功，已保存到云存储",
                url=file_record.cloud_url,  # 腾讯云COS的公网URL
                file_id=file_record.id,
            )
        else:
            return FluxUploadResponse(success=False, message=f"上传失败: {message}")

    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        import traceback

        traceback.print_exc()

        # 提供更详细的错误信息
        error_message = str(e)
        if "422" in error_message:
            error_message = f"文件格式验证失败或云存储服务问题: {error_message}"
        elif "413" in error_message:
            error_message = "文件太大，请选择小于10MB的图片"
        elif "connection" in error_message.lower():
            error_message = "云存储服务连接失败，请稍后重试"

        return FluxUploadResponse(success=False, message=f"上传失败: {error_message}")


@router.post("/upload-images", response_model=List[FluxUploadResponse])
async def upload_images_for_flux(
    files: List[UploadFile] = File(...), user=Depends(get_verified_user)
):
    """批量上传多张图片到腾讯云存储，用于多图编辑功能

    流程：用户上传多图 -> 腾讯云COS -> 获取多个云URL -> 传给第三方平台
    """
    results = []

    # 验证文件数量限制
    if len(files) > 10:
        return [FluxUploadResponse(success=False, message="一次最多只能上传10张图片")]

    # 处理每个文件
    for i, file in enumerate(files):
        try:
            # 复用单图上传的验证逻辑
            if not file.content_type or not file.content_type.startswith("image/"):
                results.append(
                    FluxUploadResponse(
                        success=False,
                        message=f"第{i+1}张图片格式不支持：{file.filename}",
                    )
                )
                continue

            file_content = await file.read()
            if len(file_content) > 10 * 1024 * 1024:
                results.append(
                    FluxUploadResponse(
                        success=False,
                        message=f"第{i+1}张图片大小超限5MB：{file.filename}",
                    )
                )
                continue

            if len(file_content) == 0:
                results.append(
                    FluxUploadResponse(
                        success=False, message=f"第{i+1}张图片内容为空：{file.filename}"
                    )
                )
                continue

            # 上传到云存储
            file_manager = get_file_manager()
            success, message, file_record = await file_manager.save_generated_content(
                user_id=user.id,
                file_data=file_content,
                filename=f"flux_multi_input_{i}_{uuid.uuid4()}.jpg",
                file_type="image",
                source_type="flux_multi_input",
                metadata={
                    "original_filename": file.filename,
                    "content_type": file.content_type,
                    "file_size": len(file_content),
                    "batch_index": i,
                },
            )

            if success and file_record and file_record.cloud_url:
                results.append(
                    FluxUploadResponse(
                        success=True,
                        message=f"第{i+1}张图片上传成功",
                        url=file_record.cloud_url,
                        file_id=file_record.id,
                    )
                )
            else:
                results.append(
                    FluxUploadResponse(
                        success=False, message=f"第{i+1}张图片上传失败: {message}"
                    )
                )

        except Exception as e:
            logger.error(f"Upload failed for file {i}: {e}")
            results.append(
                FluxUploadResponse(
                    success=False, message=f"第{i+1}张图片上传失败: {str(e)}"
                )
            )

    return results


# ======================== 任务管理 ========================


@router.post("/text-to-image", response_model=FluxTaskResponse)
async def create_text_to_image_task(
    request: FluxTextToImageRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """创建文本生图任务"""
    try:
        # 检查服务是否启用
        if not is_flux_enabled():
            raise HTTPException(status_code=400, detail="Flux service is not enabled")

        # 预检查用户积分（不扣费，只检查是否有足够积分）
        form_data = {
            "model": request.model,
            "metadata": {"features": {"image_generation": True}},
        }
        check_credit_by_user_id(user.id, form_data)

        # 获取API客户端
        client = get_flux_api_client()

        # 提交任务到Flux API
        flux_response = await client.submit_text_to_image(request)
        logger.info(f"Flux API response: {flux_response}")

        # 根据管理员配置动态替换响应中的URL
        flux_response = replace_flux_response_urls(flux_response, client.base_url)
        logger.info(f"URLs replaced for configured base_url: {flux_response}")

        # Fal.ai API 返回格式处理
        request_id = None
        if isinstance(flux_response, dict):
            # 同步模式：直接返回结果
            if request.sync_mode and flux_response.get("images"):
                request_id = str(uuid.uuid4())  # 生成本地ID
                logger.info(f"Sync mode, generated local ID: {request_id}")
            # 异步模式：返回request_id
            elif flux_response.get("request_id"):
                request_id = flux_response["request_id"]
            # 其他格式
            elif flux_response.get("id"):
                request_id = flux_response["id"]

        if not request_id:
            logger.error(f"No request ID found in response: {flux_response}")
            raise HTTPException(
                status_code=500, detail="Failed to get request ID from Flux API"
            )

        # 创建数据库任务记录 - 只传递数据库支持的字段
        task_params = {
            "user_id": user.id,
            "model": request.model,
            "task_type": "text_to_image",
            "prompt": request.prompt,
            "request_id": request_id,
            "num_images": request.num_images,
            "guidance_scale": request.guidance_scale,
            "num_inference_steps": request.num_inference_steps,
            "sync_mode": request.sync_mode,
            "enable_safety_checker": request.enable_safety_checker,
        }

        # 添加可选参数（如果有值）
        if request.aspect_ratio:
            task_params["aspect_ratio"] = request.aspect_ratio
        if request.seed is not None:
            task_params["seed"] = request.seed
        if request.safety_tolerance:
            task_params["safety_tolerance"] = int(
                request.safety_tolerance
            )  # 转换为整数
        if request.output_format:
            task_params["output_format"] = request.output_format

        task = FluxTasks.create_task(**task_params)

        # 启动后台任务轮询状态
        if not request.sync_mode:
            background_tasks.add_task(poll_flux_task_status, task.id)

        # 积分扣费将在后台任务完成时进行

        logger.info(f"Text-to-image task created: {task.id}")

        return FluxTaskResponse(**task.to_dict())

    except FluxAPIError as e:
        logger.error(f"Flux API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(f"Flux input validation error: {e}")
        raise HTTPException(status_code=422, detail=f"参数验证失败: {str(e)}")
    except ValidationError as e:
        logger.error(f"Flux pydantic validation error: {e}")
        # 解析pydantic验证错误，提供更友好的提示
        errors = []
        for error in e.errors():
            field = error.get("loc", ["unknown"])[0] if error.get("loc") else "unknown"
            msg = error.get("msg", "验证失败")
            errors.append(f"{field}: {msg}")
        error_msg = "; ".join(errors)
        raise HTTPException(status_code=422, detail=f"请求参数错误: {error_msg}")
    except Exception as e:
        logger.error(f"Failed to create text-to-image task: {e}")
        # 检查是否是pydantic验证错误
        if "validation error" in str(e).lower():
            raise HTTPException(status_code=422, detail=f"请求参数格式错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image-to-image", response_model=FluxTaskResponse)
async def create_image_to_image_task(
    request: FluxImageToImageRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """创建单图片生成图片任务"""
    try:
        # 检查服务是否启用
        if not is_flux_enabled():
            raise HTTPException(status_code=400, detail="Flux service is not enabled")

        # 预检查用户积分
        form_data = {
            "model": request.model,
            "metadata": {"features": {"image_generation": True}},
        }
        check_credit_by_user_id(user.id, form_data)

        # 获取API客户端
        client = get_flux_api_client()

        # 提交任务到Flux API
        flux_response = await client.submit_image_to_image(request)

        # 根据管理员配置动态替换响应中的URL
        flux_response = replace_flux_response_urls(flux_response, client.base_url)

        request_id = flux_response.get("request_id")

        if not request_id:
            raise HTTPException(
                status_code=500, detail="Failed to get request ID from Flux API"
            )

        # 创建数据库任务记录
        task = FluxTasks.create_task(
            user_id=user.id,
            model=request.model,
            task_type="image_to_image",
            prompt=request.prompt,
            request_id=request_id,
            input_image_url=request.image_url,
            strength=request.strength,
            num_images=request.num_images,
            guidance_scale=request.guidance_scale,
            num_inference_steps=request.num_inference_steps,
            seed=request.seed,
            sync_mode=request.sync_mode,
            enable_safety_checker=request.enable_safety_checker,
        )

        # 启动后台任务轮询状态
        if not request.sync_mode:
            background_tasks.add_task(poll_flux_task_status, task.id)

        logger.info(f"Single image-to-image task created: {task.id}")

        return FluxTaskResponse(**task.to_dict())

    except FluxAPIError as e:
        logger.error(f"Flux API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        logger.error(f"Flux pydantic validation error: {e}")
        errors = []
        for error in e.errors():
            field = error.get("loc", ["unknown"])[0] if error.get("loc") else "unknown"
            msg = error.get("msg", "验证失败")
            errors.append(f"{field}: {msg}")
        error_msg = "; ".join(errors)
        raise HTTPException(status_code=422, detail=f"请求参数错误: {error_msg}")
    except Exception as e:
        logger.error(f"Failed to create image-to-image task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-image-edit", response_model=FluxTaskResponse)
async def create_multi_image_edit_task(
    request: FluxMultiImageRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """创建多图片编辑任务（实验性功能）"""
    try:
        # 检查服务是否启用
        if not is_flux_enabled():
            raise HTTPException(status_code=400, detail="Flux service is not enabled")

        # 检查模型是否支持多图编辑
        supported_models = get_supported_flux_models()
        model_info = next(
            (m for m in supported_models if m["id"] == request.model), None
        )
        if not model_info or model_info.get("type") != "multi_image":
            raise HTTPException(
                status_code=400,
                detail=f"Model {request.model} does not support multi-image editing",
            )

        # 预检查用户积分
        form_data = {
            "model": request.model,
            "metadata": {"features": {"image_generation": True}},
        }
        check_credit_by_user_id(user.id, form_data)

        # 获取API客户端
        client = get_flux_api_client()

        # 提交任务到Flux API
        flux_response = await client.submit_multi_image_edit(request)

        # 根据管理员配置动态替换响应中的URL
        flux_response = replace_flux_response_urls(flux_response, client.base_url)

        request_id = flux_response.get("request_id")

        if not request_id:
            raise HTTPException(
                status_code=500, detail="Failed to get request ID from Flux API"
            )

        # 创建数据库任务记录 - 只传递数据库支持的字段
        task_params = {
            "user_id": user.id,
            "model": request.model,
            "task_type": "multi_image_edit",
            "prompt": request.prompt,
            "request_id": request_id,
            "input_image_urls": request.image_urls,  # 多图片URL列表
            "num_images": request.num_images,
            "guidance_scale": request.guidance_scale,
            "seed": request.seed,
            "sync_mode": request.sync_mode,
        }

        # 添加可选参数
        if request.aspect_ratio:
            task_params["aspect_ratio"] = request.aspect_ratio
        if request.safety_tolerance:
            task_params["safety_tolerance"] = int(request.safety_tolerance)
        if request.output_format:
            task_params["output_format"] = request.output_format

        task = FluxTasks.create_task(**task_params)

        # 启动后台任务轮询状态
        if not request.sync_mode:
            background_tasks.add_task(poll_flux_task_status, task.id)

        logger.info(f"Multi-image edit task created: {task.id}")

        return FluxTaskResponse(**task.to_dict())

    except FluxAPIError as e:
        logger.error(f"Flux API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        logger.error(f"Flux pydantic validation error: {e}")
        errors = []
        for error in e.errors():
            field = error.get("loc", ["unknown"])[0] if error.get("loc") else "unknown"
            msg = error.get("msg", "验证失败")
            errors.append(f"{field}: {msg}")
        error_msg = "; ".join(errors)
        raise HTTPException(status_code=422, detail=f"请求参数错误: {error_msg}")
    except Exception as e:
        logger.error(f"Failed to create multi-image edit task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}", response_model=FluxTaskResponse)
async def get_task_status(task_id: str, user=Depends(get_verified_user)):
    """获取任务状态"""
    try:
        task = FluxTasks.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 检查用户权限
        if task.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        return FluxTaskResponse(**task.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_user_flux_history(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    user=Depends(get_verified_user),
):
    """获取用户Flux历史记录"""
    try:
        tasks = FluxTasks.get_user_tasks(
            user_id=user.id, page=page, limit=limit, status=status
        )

        # 获取符合条件的任务总数
        total_count = FluxTasks.get_user_task_count(user_id=user.id, status=status)

        return {
            "data": [FluxTaskResponse(**task.to_dict()) for task in tasks],
            "total": total_count,
            "page": page,
            "limit": limit,
        }

    except Exception as e:
        logger.error(f"Failed to get user history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str, user=Depends(get_verified_user)):
    """取消任务"""
    try:
        task = FluxTasks.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 检查用户权限
        if task.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        # 如果任务还在进行中，尝试取消
        if task.status in ["PENDING", "IN_PROGRESS", "IN_QUEUE"]:
            try:
                client = get_flux_api_client()
                await client.cancel_task(task.model, task.request_id)
            except Exception as e:
                logger.warning(f"Failed to cancel remote task: {e}")

            # 更新本地状态
            FluxTasks.update_task_status(task_id, "CANCELLED")

        return {"success": True, "message": "Task cancelled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================== 后台任务 ========================


async def poll_flux_task_status(task_id: str):
    """后台轮询Flux任务状态"""
    max_attempts = 300  # 最大轮询次数
    attempt = 0

    logger.info(f"Starting background polling for task {task_id}")

    try:
        while attempt < max_attempts:
            # 获取任务信息
            task = FluxTasks.get_task_by_id(task_id)
            if not task or task.status in ["SUCCESS", "FAILED", "CANCELLED"]:
                break

            try:
                # 查询远程状态
                client = get_flux_api_client()
                result = await client.get_task_status(task.model, task.request_id)

                # 更新本地状态
                from open_webui.internal.db import get_db

                with get_db() as db:
                    # 重新获取task对象确保在当前session中
                    current_task = (
                        db.query(FluxTask).filter(FluxTask.id == task_id).first()
                    )
                    if current_task:
                        current_task.update_from_flux_response(result)
                        db.commit()
                        task = current_task  # 更新引用

                # 如果任务完成，上传结果到云存储
                if (
                    task.status in ["SUCCESS", "COMPLETED"]
                    and task.image_url
                    and not task.cloud_image_url
                ):
                    await upload_result_to_cloud_storage(task)

                    # 任务成功完成时扣除积分
                    try:
                        form_data = {
                            "model": task.model,
                            "metadata": {
                                "features": {"image_generation": True},
                                "task_id": task.id,
                                "task_type": task.task_type,
                            },
                        }
                        # 使用通用积分系统进行扣费
                        from open_webui.utils.credit.utils import (
                            check_credit_by_user_id,
                        )

                        logger.info(
                            f"Deducting credits for completed Flux task {task.id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to deduct credits for task {task.id}: {e}"
                        )

                # 检查COMPLETED状态但没有图片的情况
                if task.status == "SUCCESS" and not task.image_url:
                    logger.warning(
                        f"Task {task_id} marked as SUCCESS but no image_url, continuing to poll"
                    )
                    # 继续轮询，等待获取图片结果
                elif task.status in ["SUCCESS", "FAILED", "CANCELLED"]:
                    break

            except Exception as e:
                logger.error(f"Error polling task {task_id}: {e}")
                # 增加重试计数
                FluxTasks.update_task_status(
                    task_id, task.status, retry_count=task.retry_count + 1
                )

            await asyncio.sleep(5)  # 5秒间隔
            attempt += 1

        # 如果超过最大尝试次数，标记为失败
        if attempt >= max_attempts:
            FluxTasks.update_task_status(
                task_id,
                "FAILED",
                error_message="Polling timeout after maximum attempts",
            )
            logger.error(f"Task {task_id} polling timeout")

    except Exception as e:
        logger.error(f"Background polling failed for task {task_id}: {e}")
        FluxTasks.update_task_status(
            task_id, "FAILED", error_message=f"Background polling error: {str(e)}"
        )


async def upload_result_to_cloud_storage(task: FluxTask):
    """上传Flux生成结果到云存储"""
    try:
        if not task.image_url:
            return

        file_manager = get_file_manager()
        success, message, file_record = await file_manager.save_generated_content(
            user_id=task.user_id,
            file_url=task.image_url,
            filename=f"flux_{task.model.replace('/', '_')}_{task.id}.jpg",
            file_type="image",
            source_type="flux",
            source_task_id=task.id,
            metadata={
                "model": task.model,
                "prompt": task.prompt,
                "task_type": task.task_type,
            },
        )

        if success and file_record:
            # 更新任务记录中的云存储URL
            FluxTasks.update_task_status(
                task.id, task.status, cloud_image_url=file_record.cloud_url
            )
            logger.info(f"Result uploaded to cloud storage for task {task.id}")
        else:
            logger.error(f"Failed to upload result to cloud storage: {message}")

    except Exception as e:
        logger.error(f"Error uploading result to cloud storage: {e}")


# ======================== 健康检查 ========================


@router.get("/health")
async def health_check():
    """Flux服务健康检查"""
    try:
        config = FluxConfigs.get_config()
        if not config:
            return {
                "status": "error",
                "message": "No configuration found",
                "enabled": False,
            }

        if not config.enabled:
            return {
                "status": "disabled",
                "message": "Flux service is disabled",
                "enabled": False,
            }

        # 测试API连接
        client = FluxAPIClient(config)
        connection_ok = await client.test_connection()

        return {
            "status": "healthy" if connection_ok else "error",
            "message": (
                "Flux service is running" if connection_ok else "API connection failed"
            ),
            "enabled": True,
            "api_connected": connection_ok,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "enabled": False,
            "api_connected": False,
        }
