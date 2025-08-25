import os
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple

from open_webui.internal.db import get_db
from open_webui.models.cloud_storage import (
    CloudStorageConfig,
    GeneratedFile,
    CloudStorageConfigs,
    GeneratedFiles,
    GeneratedFileForm,
    UploadRequest,
    MigrateUrlRequest,
)
from open_webui.utils.cloud_storage.tencent_cos import TencentCOSService


logger = logging.getLogger(__name__)


class GeneratedFileManager:
    """生成文件管理器 - 统一处理AI生成内容的存储和管理"""

    def __init__(self):
        """初始化文件管理器"""
        self.storage_config_table = CloudStorageConfigs()
        self.file_table = GeneratedFiles()
        self._cos_service = None

    def _get_cos_service(self) -> Optional[TencentCOSService]:
        """获取腾讯云COS服务实例

        Returns:
            TencentCOSService: COS服务实例，如果未配置返回None
        """
        # 每次都重新检查配置，避免配置更新后服务不可用的问题
        config = self.storage_config_table.get_config()
        if not config or not config.enabled:
            logger.warning("云存储配置未启用或不存在")
            self._cos_service = None
            return None

        # 如果配置存在且启用，检查是否需要重新创建服务
        if self._cos_service is None:
            logger.info("创建新的COS服务实例")
            self._cos_service = TencentCOSService(config)
        else:
            # 检查配置是否发生变化，如果变化则重新创建
            current_config = self._cos_service.config
            if (
                current_config.secret_id != config.secret_id
                or current_config.secret_key != config.secret_key
                or current_config.region != config.region
                or current_config.bucket != config.bucket
            ):
                logger.info("COS配置发生变化，重新创建服务实例")
                self._cos_service = TencentCOSService(config)

        return self._cos_service

    async def save_generated_content(
        self,
        user_id: str,
        file_url: Optional[str] = None,
        file_data: Optional[bytes] = None,
        filename: str = "",
        file_type: str = "image",  # 'image' or 'video'
        source_type: str = "",  # 'midjourney', 'kling', 'jimeng', 'dreamwork'
        source_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Optional[GeneratedFile]]:
        """保存生成的内容到云存储

        Args:
            user_id: 用户ID
            file_url: 文件URL（从URL下载上传）
            file_data: 文件字节数据（直接上传）
            filename: 文件名
            file_type: 文件类型 ('image', 'video')
            source_type: 来源类型 ('midjourney', 'kling', 'jimeng', 'dreamwork')
            source_task_id: 来源任务ID
            metadata: 元数据

        Returns:
            Tuple[bool, str, Optional[GeneratedFile]]: (成功状态, 消息, 文件记录)
        """
        try:
            # 参数验证
            if not user_id or not source_type:
                return False, "用户ID和来源类型不能为空", None

            if not file_url and not file_data:
                return False, "必须提供file_url或file_data其中之一", None

            # 获取COS服务
            cos_service = self._get_cos_service()
            if not cos_service or not cos_service.is_available():
                logger.warning("云存储服务不可用，跳过上传")
                return False, "云存储服务不可用", None

            # 创建文件记录（状态为pending）
            file_form = GeneratedFileForm(
                user_id=user_id,
                filename=filename,
                file_type=file_type,
                source_type=source_type,
                source_task_id=source_task_id,
                file_metadata=metadata,
                status="pending",
            )

            file_record = self.file_table.create_file_record(file_form)
            logger.info(f"创建文件记录: {file_record.id}")

            # 上传文件到COS
            upload_result = None
            if file_url:
                # 从URL上传
                logger.info(f"从URL上传文件: {file_url}")
                upload_result = await cos_service.upload_file_from_url(
                    file_url=file_url,
                    filename=filename,
                    file_type=file_type,
                    user_id=user_id,
                )
            elif file_data:
                # 从字节数据上传
                logger.info(f"从字节数据上传文件: {filename}")
                upload_result = await cos_service.upload_file_from_bytes(
                    file_data=file_data,
                    filename=filename,
                    file_type=file_type,
                    user_id=user_id,
                )

            if upload_result and upload_result.get("success"):
                # 上传成功，更新文件记录
                success = self.file_table.update_file_status(
                    file_id=file_record.id,
                    status="uploaded",
                    cloud_url=upload_result.get("cloud_url"),
                )

                if success:
                    # 重新获取更新后的记录
                    updated_record = self.file_table.get_file_by_id(file_record.id)
                    logger.info(f"文件上传成功: {upload_result.get('cloud_url')}")
                    return True, "文件上传成功", updated_record
                else:
                    logger.error("更新文件状态失败")
                    return False, "更新文件状态失败", file_record
            else:
                # 上传失败，更新错误信息
                error_message = (
                    upload_result.get("message", "上传失败")
                    if upload_result
                    else "上传失败"
                )
                self.file_table.update_file_status(
                    file_id=file_record.id, status="failed", error_message=error_message
                )
                logger.error(f"文件上传失败: {error_message}")
                return False, error_message, file_record

        except Exception as e:
            logger.error(f"保存生成内容失败: {str(e)}")
            return False, f"保存失败: {str(e)}", None

    async def migrate_external_url(
        self,
        external_url: str,
        user_id: str,
        source_type: str,
        source_task_id: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """将外部URL的文件迁移到云存储

        Args:
            external_url: 外部文件URL
            user_id: 用户ID
            source_type: 来源类型
            source_task_id: 来源任务ID
            filename: 文件名（可选）

        Returns:
            Tuple[bool, str, Optional[str]]: (成功状态, 消息, 云存储URL)
        """
        try:
            # 检查是否已经存在相同的文件记录
            existing_files = self.file_table.get_files_by_source(
                source_type, source_task_id
            )
            for file_record in existing_files:
                if file_record.status == "uploaded" and file_record.cloud_url:
                    logger.info(f"文件已存在，跳过迁移: {file_record.cloud_url}")
                    return True, "文件已存在", file_record.cloud_url

            # 推断文件类型
            file_type = (
                "video"
                if any(
                    ext in external_url.lower()
                    for ext in [".mp4", ".avi", ".mov", ".mkv"]
                )
                else "image"
            )

            # 生成文件名
            if not filename:
                filename = f"{source_type}_{source_task_id}_{file_type}"

            # 执行上传
            success, message, file_record = await self.save_generated_content(
                user_id=user_id,
                file_url=external_url,
                filename=filename,
                file_type=file_type,
                source_type=source_type,
                source_task_id=source_task_id,
                metadata={"original_url": external_url},
            )

            if success and file_record:
                return True, message, file_record.cloud_url
            else:
                return False, message, None

        except Exception as e:
            logger.error(f"迁移外部URL失败: {str(e)}")
            return False, f"迁移失败: {str(e)}", None

    async def delete_generated_file(
        self, file_id: str, user_id: str
    ) -> Tuple[bool, str]:
        """删除生成的文件（包括云存储和数据库记录）

        Args:
            file_id: 文件ID
            user_id: 用户ID（用于权限验证）

        Returns:
            Tuple[bool, str]: (成功状态, 消息)
        """
        try:
            # 获取文件记录
            file_record = self.file_table.get_file_by_id(file_id)
            if not file_record:
                return False, "文件记录不存在"

            # 权限检查
            if file_record.user_id != user_id:
                return False, "无权限删除该文件"

            # 删除云存储文件
            if file_record.cloud_path and file_record.status == "uploaded":
                cos_service = self._get_cos_service()
                if cos_service and cos_service.is_available():
                    delete_result = await cos_service.delete_file(
                        file_record.cloud_path
                    )
                    if not delete_result.get("success"):
                        logger.warning(
                            f"删除云存储文件失败: {delete_result.get('message')}"
                        )
                        # 不阻止删除数据库记录

            # 删除数据库记录
            success = self.file_table.delete_file_record(file_id, user_id)
            if success:
                logger.info(f"文件删除成功: {file_id}")
                return True, "文件删除成功"
            else:
                return False, "删除数据库记录失败"

        except Exception as e:
            logger.error(f"删除生成文件失败: {str(e)}")
            return False, f"删除失败: {str(e)}"

    def get_user_files(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        file_type: Optional[str] = None,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[GeneratedFile], int]:
        """获取用户的生成文件列表

        Args:
            user_id: 用户ID
            page: 页码
            limit: 每页数量
            file_type: 文件类型筛选
            source_type: 来源类型筛选
            status: 状态筛选

        Returns:
            Tuple[List[GeneratedFile], int]: (文件列表, 总数)
        """
        try:
            return self.file_table.get_files_by_user(
                user_id=user_id,
                page=page,
                limit=limit,
                file_type=file_type,
                source_type=source_type,
                status=status,
            )
        except Exception as e:
            logger.error(f"获取用户文件列表失败: {str(e)}")
            return [], 0

    async def batch_migrate_external_urls(
        self, source_type: Optional[str] = None, batch_size: int = 10
    ) -> Dict[str, Any]:
        """批量迁移外部URL到云存储（管理员功能）

        Args:
            source_type: 指定来源类型，None表示所有类型
            batch_size: 批处理大小

        Returns:
            Dict: 迁移结果统计
        """
        try:
            # 这里需要根据具体的业务逻辑来实现
            # 比如从midjourney_tasks, kling_tasks等表中查找需要迁移的URL

            # 示例实现（需要根据实际表结构调整）
            migrated_count = 0
            failed_count = 0

            # TODO: 实现具体的批量迁移逻辑
            # 1. 查询各个任务表中的外部URL
            # 2. 检查是否已经迁移
            # 3. 执行迁移
            # 4. 更新任务表中的URL字段

            logger.info("批量迁移功能需要根据具体业务逻辑实现")

            return {
                "success": True,
                "migrated_count": migrated_count,
                "failed_count": failed_count,
                "message": f"迁移完成：成功 {migrated_count} 个，失败 {failed_count} 个",
            }

        except Exception as e:
            logger.error(f"批量迁移失败: {str(e)}")
            return {
                "success": False,
                "migrated_count": 0,
                "failed_count": 0,
                "message": f"批量迁移失败: {str(e)}",
            }

    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储使用统计

        Returns:
            Dict: 存储统计信息
        """
        try:
            # 获取基本统计
            with get_db() as db:
                from sqlalchemy import func, desc
                from datetime import datetime, timedelta

                total_files = db.query(GeneratedFile).count()
                uploaded_files = (
                    db.query(GeneratedFile)
                    .filter(GeneratedFile.status == "uploaded")
                    .count()
                )
                failed_files = (
                    db.query(GeneratedFile)
                    .filter(GeneratedFile.status == "failed")
                    .count()
                )
                pending_files = (
                    db.query(GeneratedFile)
                    .filter(GeneratedFile.status == "pending")
                    .count()
                )

                # 计算总存储大小（字节）
                total_size = (
                    db.query(func.sum(GeneratedFile.file_size))
                    .filter(GeneratedFile.status == "uploaded")
                    .scalar()
                    or 0
                )

                # 按类型统计（包含大小）
                type_stats = (
                    db.query(
                        GeneratedFile.file_type,
                        func.count(GeneratedFile.id).label("count"),
                        func.sum(GeneratedFile.file_size).label("total_size"),
                    )
                    .filter(GeneratedFile.status == "uploaded")
                    .group_by(GeneratedFile.file_type)
                    .all()
                )

                # 按来源统计（包含大小）
                source_stats = (
                    db.query(
                        GeneratedFile.source_type,
                        func.count(GeneratedFile.id).label("count"),
                        func.sum(GeneratedFile.file_size).label("total_size"),
                    )
                    .filter(GeneratedFile.status == "uploaded")
                    .group_by(GeneratedFile.source_type)
                    .all()
                )

                # 按用户统计（前10个用户）
                user_stats = (
                    db.query(
                        GeneratedFile.user_id,
                        func.count(GeneratedFile.id).label("count"),
                        func.sum(GeneratedFile.file_size).label("total_size"),
                    )
                    .filter(GeneratedFile.status == "uploaded")
                    .group_by(GeneratedFile.user_id)
                    .order_by(desc("total_size"))
                    .limit(10)
                    .all()
                )

                # 最近7天的上传趋势
                seven_days_ago = datetime.now() - timedelta(days=7)
                daily_stats = (
                    db.query(
                        func.date(GeneratedFile.created_at).label("date"),
                        func.count(GeneratedFile.id).label("count"),
                        func.sum(GeneratedFile.file_size).label("total_size"),
                    )
                    .filter(
                        GeneratedFile.created_at >= seven_days_ago,
                        GeneratedFile.status == "uploaded",
                    )
                    .group_by(func.date(GeneratedFile.created_at))
                    .order_by("date")
                    .all()
                )

                # 最近失败的文件（前5个）
                recent_failures = (
                    db.query(GeneratedFile)
                    .filter(GeneratedFile.status == "failed")
                    .order_by(GeneratedFile.created_at.desc())
                    .limit(5)
                    .all()
                )

                # 格式化大小为人类可读格式
                def format_size(size_bytes):
                    if size_bytes == 0:
                        return "0B"
                    size_names = ("B", "KB", "MB", "GB", "TB")
                    i = int(math.floor(math.log(size_bytes, 1024)))
                    p = math.pow(1024, i)
                    s = round(size_bytes / p, 2)
                    return f"{s} {size_names[i]}"

                import math

                return {
                    "summary": {
                        "total_files": total_files,
                        "uploaded_files": uploaded_files,
                        "failed_files": failed_files,
                        "pending_files": pending_files,
                        "total_size": total_size,
                        "total_size_formatted": format_size(total_size),
                        "success_rate": round(
                            (
                                (uploaded_files / total_files * 100)
                                if total_files > 0
                                else 0
                            ),
                            2,
                        ),
                    },
                    "type_distribution": {
                        stat[0]: {
                            "count": stat[1],
                            "size": stat[2] or 0,
                            "size_formatted": format_size(stat[2] or 0),
                        }
                        for stat in type_stats
                    },
                    "source_distribution": {
                        stat[0]: {
                            "count": stat[1],
                            "size": stat[2] or 0,
                            "size_formatted": format_size(stat[2] or 0),
                        }
                        for stat in source_stats
                    },
                    "top_users": [
                        {
                            "user_id": stat[0],
                            "count": stat[1],
                            "size": stat[2] or 0,
                            "size_formatted": format_size(stat[2] or 0),
                        }
                        for stat in user_stats
                    ],
                    "daily_trend": [
                        {
                            "date": (
                                stat[0].strftime("%Y-%m-%d")
                                if stat[0] and hasattr(stat[0], "strftime")
                                else str(stat[0]) if stat[0] else ""
                            ),
                            "count": stat[1],
                            "size": stat[2] or 0,
                            "size_formatted": format_size(stat[2] or 0),
                        }
                        for stat in daily_stats
                    ],
                    "recent_failures": [
                        {
                            "id": f.id,
                            "filename": f.filename,
                            "source_type": f.source_type,
                            "error": f.error_message,
                            "created_at": (
                                f.created_at.strftime("%Y-%m-%d %H:%M:%S")
                                if f.created_at
                                else ""
                            ),
                        }
                        for f in recent_failures
                    ],
                }

        except Exception as e:
            logger.error(f"获取存储统计失败: {str(e)}")
            return {
                "summary": {
                    "total_files": 0,
                    "uploaded_files": 0,
                    "failed_files": 0,
                    "pending_files": 0,
                    "total_size": 0,
                    "total_size_formatted": "0B",
                    "success_rate": 0,
                },
                "type_distribution": {},
                "source_distribution": {},
                "top_users": [],
                "daily_trend": [],
                "recent_failures": [],
            }


# 全局实例
_file_manager_instance = None


def get_file_manager() -> GeneratedFileManager:
    """获取文件管理器实例

    Returns:
        GeneratedFileManager: 文件管理器实例
    """
    global _file_manager_instance
    if _file_manager_instance is None:
        _file_manager_instance = GeneratedFileManager()
    return _file_manager_instance
