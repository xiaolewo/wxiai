import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.models.cloud_storage import (
    CloudStorageConfigForm,
    CloudStorageConfigResponse,
    CloudStorageConfigs,
    GeneratedFiles,
)
from open_webui.utils.cloud_storage.tencent_cos import TencentCOSService
from open_webui.services.file_manager import get_file_manager


logger = logging.getLogger(__name__)

router = APIRouter()


####################
# 存储配置管理 API
####################


@router.get("/config")
async def get_storage_config(user=Depends(get_admin_user)):
    """获取云存储配置（管理员专用）"""
    try:
        storage_configs = CloudStorageConfigs()
        config = storage_configs.get_config()

        if not config:
            # 返回默认配置
            return {
                "provider": "tencent-cos",
                "enabled": False,
                "region": "ap-beijing",
                "auto_upload": True,
                "allowed_types": ["image/*", "video/*"],
                "max_file_size": 104857600,
                "base_path": "generated/",
                "image_path": "images/",
                "video_path": "videos/",
            }

        # 不返回敏感信息的完整内容
        response_data = {
            "id": config.id,
            "provider": config.provider,
            "enabled": config.enabled,
            "secret_id": config.secret_id[:8] + "****" if config.secret_id else None,
            "secret_key": "****" if config.secret_key else None,
            "region": config.region,
            "bucket": config.bucket,
            "domain": config.domain,
            "auto_upload": config.auto_upload,
            "allowed_types": config.allowed_types,
            "max_file_size": config.max_file_size,
            "base_path": config.base_path,
            "image_path": config.image_path,
            "video_path": config.video_path,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }

        return response_data

    except Exception as e:
        logger.error(f"获取存储配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}",
        )


@router.post("/config")
async def update_storage_config(
    config_form: CloudStorageConfigForm, user=Depends(get_admin_user)
):
    """更新云存储配置（管理员专用）"""
    try:
        storage_configs = CloudStorageConfigs()

        # 更新配置
        config = storage_configs.create_or_update_config(config_form)

        logger.info(f"云存储配置更新成功，启用状态: {config.enabled}")

        return {
            "success": True,
            "message": "配置保存成功",
            "config": {
                "id": config.id,
                "provider": config.provider,
                "enabled": config.enabled,
                "region": config.region,
                "bucket": config.bucket,
                "auto_upload": config.auto_upload,
            },
        }

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logger.error(f"更新存储配置失败: {str(e)}")
        logger.error(f"详细错误信息: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置失败: {str(e)}",
        )


@router.post("/test")
async def test_storage_connection(user=Depends(get_admin_user)):
    """测试云存储连接（管理员专用）"""
    try:
        storage_configs = CloudStorageConfigs()
        config = storage_configs.get_config()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请先配置云存储"
            )

        if not config.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="云存储未启用"
            )

        # 创建COS服务并测试连接
        cos_service = TencentCOSService(config)
        test_result = await cos_service.test_connection()

        if test_result.get("success"):
            logger.info("云存储连接测试成功")
            return {
                "success": True,
                "message": "连接测试成功",
                "details": test_result.get("bucket_info", {}),
            }
        else:
            logger.error(f"云存储连接测试失败: {test_result.get('message')}")
            return {
                "success": False,
                "message": test_result.get("message", "连接测试失败"),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试存储连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接测试失败: {str(e)}",
        )


####################
# 文件管理 API
####################


@router.get("/files/generated")
async def get_generated_files(
    page: int = 1,
    limit: int = 20,
    file_type: Optional[str] = None,
    source_type: Optional[str] = None,
    status: Optional[str] = None,
    user=Depends(get_verified_user),
):
    """获取用户生成的文件列表"""
    try:
        # 参数验证
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20

        file_manager = get_file_manager()
        files, total = file_manager.get_user_files(
            user_id=user.id,
            page=page,
            limit=limit,
            file_type=file_type,
            source_type=source_type,
            status=status,
        )

        # 转换为响应格式
        file_list = []
        for file_record in files:
            file_data = {
                "id": file_record.id,
                "filename": file_record.filename,
                "file_type": file_record.file_type,
                "file_size": file_record.file_size,
                "mime_type": file_record.mime_type,
                "cloud_url": file_record.cloud_url,
                "source_type": file_record.source_type,
                "source_task_id": file_record.source_task_id,
                "status": file_record.status,
                "metadata": file_record.file_metadata,
                "created_at": (
                    file_record.created_at.isoformat()
                    if file_record.created_at
                    else None
                ),
                "error_message": file_record.error_message,
            }
            file_list.append(file_data)

        return {
            "data": file_list,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"获取生成文件列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件列表失败: {str(e)}",
        )


@router.delete("/files/generated/{file_id}")
async def delete_generated_file(file_id: str, user=Depends(get_verified_user)):
    """删除生成的文件"""
    try:
        file_manager = get_file_manager()
        success, message = await file_manager.delete_generated_file(file_id, user.id)

        if success:
            logger.info(f"用户 {user.id} 删除文件 {file_id} 成功")
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除生成文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {str(e)}",
        )


@router.post("/files/migrate")
async def migrate_external_files(
    source_type: Optional[str] = None,
    batch_size: int = 100,
    user=Depends(get_admin_user),
):
    """批量迁移外部URL到云存储（管理员专用）"""
    try:
        # 参数验证
        if batch_size < 1 or batch_size > 1000:
            batch_size = 100

        file_manager = get_file_manager()
        result = await file_manager.batch_migrate_external_urls(
            source_type=source_type, batch_size=batch_size
        )

        logger.info(f"批量迁移完成: {result}")
        return result

    except Exception as e:
        logger.error(f"批量迁移失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量迁移失败: {str(e)}",
        )


####################
# 统计信息 API
####################


@router.get("/stats")
async def get_storage_stats(user=Depends(get_admin_user)):
    """获取存储使用统计（管理员专用）"""
    try:
        file_manager = get_file_manager()
        stats = await file_manager.get_storage_stats()

        return {"success": True, "stats": stats}

    except Exception as e:
        logger.error(f"获取存储统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}",
        )


####################
# 内部服务 API（供其他模块调用）
####################


@router.post("/internal/upload")
async def internal_upload_file(request_data: dict):
    """内部文件上传接口（供其他模块调用）

    Args:
        request_data: {
            "user_id": str,
            "file_url": str (可选),
            "file_data": bytes (可选),
            "filename": str,
            "file_type": str,
            "source_type": str,
            "source_task_id": str (可选),
            "metadata": dict (可选)
        }
    """
    try:
        file_manager = get_file_manager()

        success, message, file_record = await file_manager.save_generated_content(
            user_id=request_data.get("user_id"),
            file_url=request_data.get("file_url"),
            file_data=request_data.get("file_data"),
            filename=request_data.get("filename", ""),
            file_type=request_data.get("file_type", "image"),
            source_type=request_data.get("source_type", ""),
            source_task_id=request_data.get("source_task_id"),
            metadata=request_data.get("metadata"),
        )

        result = {"success": success, "message": message}

        if file_record:
            result.update(
                {
                    "file_id": file_record.id,
                    "cloud_url": file_record.cloud_url,
                    "cloud_path": file_record.cloud_path,
                    "status": file_record.status,
                }
            )

        return result

    except Exception as e:
        logger.error(f"内部文件上传失败: {str(e)}")
        return {"success": False, "message": f"上传失败: {str(e)}"}


@router.post("/internal/migrate-url")
async def internal_migrate_url(request_data: dict):
    """内部URL迁移接口（供其他模块调用）

    Args:
        request_data: {
            "external_url": str,
            "user_id": str,
            "source_type": str,
            "source_task_id": str (可选),
            "filename": str (可选)
        }
    """
    try:
        file_manager = get_file_manager()

        success, message, cloud_url = await file_manager.migrate_external_url(
            external_url=request_data.get("external_url"),
            user_id=request_data.get("user_id"),
            source_type=request_data.get("source_type"),
            source_task_id=request_data.get("source_task_id"),
            filename=request_data.get("filename"),
        )

        return {
            "success": success,
            "message": message,
            "original_url": request_data.get("external_url"),
            "cloud_url": cloud_url,
        }

    except Exception as e:
        logger.error(f"内部URL迁移失败: {str(e)}")
        return {
            "success": False,
            "message": f"迁移失败: {str(e)}",
            "original_url": request_data.get("external_url"),
            "cloud_url": None,
        }
