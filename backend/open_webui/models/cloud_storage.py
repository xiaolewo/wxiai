from sqlalchemy import Column, String, Boolean, BigInteger, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime
from open_webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict
import time
import uuid


####################
# 云存储配置模型
####################


class CloudStorageConfig(Base):
    __tablename__ = "cloud_storage_config"

    id = Column(String(255), primary_key=True)
    provider = Column(String(50), nullable=False)  # 'tencent-cos'
    enabled = Column(Boolean, nullable=False, default=False)

    # 腾讯云COS配置
    secret_id = Column(Text, nullable=True)
    secret_key = Column(Text, nullable=True)
    region = Column(String(50), nullable=True)  # 'ap-beijing'
    bucket = Column(String(255), nullable=True)
    domain = Column(Text, nullable=True)  # 自定义域名

    # 上传配置
    auto_upload = Column(Boolean, nullable=False, default=True)
    allowed_types = Column(JSON, nullable=True)  # ['image/*', 'video/*']
    max_file_size = Column(BigInteger, nullable=False, default=104857600)  # 100MB

    # 路径配置
    base_path = Column(String(255), nullable=False, default="generated/")
    image_path = Column(String(255), nullable=False, default="images/")
    video_path = Column(String(255), nullable=False, default="videos/")

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now())


####################
# 生成文件记录模型
####################


class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)

    # 文件基本信息
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_type = Column(String(20), nullable=False)  # 'image', 'video'
    mime_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger, nullable=True)

    # 存储信息
    storage_provider = Column(String(50), nullable=False, default="local")
    local_path = Column(Text, nullable=True)  # 本地备份路径
    cloud_url = Column(Text, nullable=True)  # COS访问URL
    cloud_path = Column(Text, nullable=True)  # COS存储路径

    # 关联信息
    source_type = Column(
        String(50), nullable=False
    )  # 'midjourney', 'kling', 'jimeng', 'dreamwork'
    source_task_id = Column(String(255), nullable=True)  # 关联任务ID

    # 元数据和状态
    file_metadata = Column(JSON, nullable=True)  # 扩展数据
    status = Column(
        String(20), nullable=False, default="pending"
    )  # 'pending', 'uploaded', 'failed'
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, default=func.now())

    # 复合索引
    __table_args__ = (
        Index("idx_generated_files_source", "source_type", "source_task_id"),
        Index("idx_generated_files_user_status", "user_id", "status"),
    )


####################
# Pydantic 表单模型
####################


class CloudStorageConfigForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str = "tencent-cos"
    enabled: bool = False
    secret_id: Optional[str] = None
    secret_key: Optional[str] = None
    region: str = "ap-beijing"
    bucket: Optional[str] = None
    domain: Optional[str] = None
    auto_upload: bool = True
    allowed_types: List[str] = ["image/*", "video/*"]
    max_file_size: int = 104857600  # 100MB
    base_path: str = "generated/"
    image_path: str = "images/"
    video_path: str = "videos/"


class CloudStorageConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    enabled: bool
    secret_id: Optional[str] = None  # 不返回敏感信息的完整内容
    secret_key: Optional[str] = None  # 不返回敏感信息的完整内容
    region: Optional[str] = None
    bucket: Optional[str] = None
    domain: Optional[str] = None
    auto_upload: bool
    allowed_types: Optional[List[str]] = None
    max_file_size: int
    base_path: str
    image_path: str
    video_path: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GeneratedFileForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    filename: str
    original_filename: Optional[str] = None
    file_type: str  # 'image', 'video'
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    storage_provider: str = "local"
    local_path: Optional[str] = None
    cloud_url: Optional[str] = None
    cloud_path: Optional[str] = None
    source_type: str  # 'midjourney', 'kling', 'jimeng', 'dreamwork'
    source_task_id: Optional[str] = None
    file_metadata: Optional[Dict[str, Any]] = None
    status: str = "pending"
    error_message: Optional[str] = None


class GeneratedFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    filename: str
    original_filename: Optional[str] = None
    file_type: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    storage_provider: str
    local_path: Optional[str] = None
    cloud_url: Optional[str] = None
    cloud_path: Optional[str] = None
    source_type: str
    source_task_id: Optional[str] = None
    file_metadata: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UploadRequest(BaseModel):
    user_id: str
    file_url: Optional[str] = None  # 用于从URL下载上传
    file_data: Optional[bytes] = None  # 用于直接上传
    filename: str
    file_type: str  # 'image', 'video'
    source_type: str  # 'midjourney', 'kling', 'jimeng', 'dreamwork'
    source_task_id: Optional[str] = None
    file_metadata: Optional[Dict[str, Any]] = None


class MigrateUrlRequest(BaseModel):
    external_url: str
    user_id: str
    source_type: str
    source_task_id: Optional[str] = None
    filename: Optional[str] = None


class FileListRequest(BaseModel):
    page: int = 1
    limit: int = 20
    file_type: Optional[str] = None  # 'image', 'video'
    source_type: Optional[str] = None  # 'midjourney', 'kling', 'jimeng', 'dreamwork'
    status: Optional[str] = None  # 'pending', 'uploaded', 'failed'


class FileListResponse(BaseModel):
    data: List[GeneratedFileResponse]
    total: int
    page: int
    limit: int


####################
# 工具类
####################


class CloudStorageTable:
    def get_config(self) -> Optional[CloudStorageConfig]:
        """获取云存储配置"""
        try:
            with get_db() as db:
                return db.query(CloudStorageConfig).first()
        except Exception as e:
            print(f"获取配置错误: {e}")
            return None

    def create_or_update_config(
        self, form_data: CloudStorageConfigForm
    ) -> CloudStorageConfig:
        """创建或更新云存储配置"""
        from datetime import datetime

        try:
            with get_db() as db:
                # 查找现有配置
                config = db.query(CloudStorageConfig).first()

                if config:
                    # 更新现有配置
                    for key, value in form_data.model_dump().items():
                        setattr(config, key, value)
                    config.updated_at = datetime.utcnow()
                else:
                    # 创建新配置
                    config_data = form_data.model_dump()
                    config = CloudStorageConfig(
                        id=str(uuid.uuid4()),
                        **config_data,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(config)

                db.commit()
                db.refresh(config)
                return config
        except Exception as e:
            print(f"创建或更新配置错误: {e}")
            import traceback

            traceback.print_exc()
            raise e

    def delete_config(self) -> bool:
        """删除云存储配置"""
        try:
            with get_db() as db:
                config = db.query(CloudStorageConfig).first()
                if config:
                    db.delete(config)
                    db.commit()
                    return True
                return False
        except Exception:
            return False


class GeneratedFileTable:

    def create_file_record(self, form_data: GeneratedFileForm) -> GeneratedFile:
        """创建文件记录"""
        from datetime import datetime

        try:
            with get_db() as db:
                file_data = form_data.model_dump()
                file_record = GeneratedFile(
                    id=str(uuid.uuid4()),
                    **file_data,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(file_record)
                db.commit()
                db.refresh(file_record)
                return file_record
        except Exception as e:
            print(f"创建文件记录错误: {e}")
            import traceback

            traceback.print_exc()
            raise e

    def get_file_by_id(self, file_id: str) -> Optional[GeneratedFile]:
        """根据ID获取文件记录"""
        try:
            with get_db() as db:
                return (
                    db.query(GeneratedFile).filter(GeneratedFile.id == file_id).first()
                )
        except Exception:
            return None

    def get_files_by_user(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        file_type: Optional[str] = None,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[List[GeneratedFile], int]:
        """获取用户的文件列表"""
        try:
            with get_db() as db:
                query = db.query(GeneratedFile).filter(GeneratedFile.user_id == user_id)

                if file_type:
                    query = query.filter(GeneratedFile.file_type == file_type)
                if source_type:
                    query = query.filter(GeneratedFile.source_type == source_type)
                if status:
                    query = query.filter(GeneratedFile.status == status)

                # 总数
                total = query.count()

                # 分页
                files = (
                    query.order_by(GeneratedFile.created_at.desc())
                    .offset((page - 1) * limit)
                    .limit(limit)
                    .all()
                )

                return files, total
        except Exception:
            return [], 0

    def update_file_status(
        self,
        file_id: str,
        status: str,
        cloud_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """更新文件状态"""
        try:
            from datetime import datetime

            with get_db() as db:
                file_record = (
                    db.query(GeneratedFile).filter(GeneratedFile.id == file_id).first()
                )
                if file_record:
                    file_record.status = status
                    if cloud_url:
                        file_record.cloud_url = cloud_url
                    if error_message:
                        file_record.error_message = error_message
                    file_record.updated_at = datetime.utcnow()

                    db.commit()
                    return True
                return False
        except Exception:
            return False

    def delete_file_record(self, file_id: str, user_id: str) -> bool:
        """删除文件记录（验证用户权限）"""
        try:
            with get_db() as db:
                file_record = (
                    db.query(GeneratedFile)
                    .filter(
                        GeneratedFile.id == file_id, GeneratedFile.user_id == user_id
                    )
                    .first()
                )

                if file_record:
                    db.delete(file_record)
                    db.commit()
                    return True
                return False
        except Exception:
            return False

    def get_files_by_source(
        self, source_type: str, source_task_id: str
    ) -> List[GeneratedFile]:
        """根据来源获取文件列表"""
        try:
            with get_db() as db:
                return (
                    db.query(GeneratedFile)
                    .filter(
                        GeneratedFile.source_type == source_type,
                        GeneratedFile.source_task_id == source_task_id,
                    )
                    .all()
                )
        except Exception:
            return []


CloudStorageConfigs = CloudStorageTable
GeneratedFiles = GeneratedFileTable
