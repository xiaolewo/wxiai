"""
谷歌生图服务数据模型
支持OpenAI DALL-E兼容格式的图像编辑和生成
包含配置、任务、积分记录等所有相关模型
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import json
import uuid

from open_webui.internal.db import Base, get_db

# ======================== Pydantic API 模型 ========================


class GoogleImagesGenerateRequest(BaseModel):
    """谷歌生图生成请求模型 - 兼容OpenAI DALL-E格式"""

    model: str = "nano-banana"  # 固定模型名
    prompt: str = Field(..., description="图像生成描述")
    images: Optional[List[str]] = Field(None, description="参考图片列表(base64或URL)")
    size: Optional[str] = Field("1024x1024", description="图像尺寸")
    n: Optional[int] = Field(1, description="生成图片数量")
    quality: Optional[str] = Field("standard", description="图片质量: standard, hd")
    style: Optional[str] = Field("natural", description="风格: natural, vivid")

    @validator("images")
    def validate_images(cls, v, values):
        """验证图片输入"""
        if v is None:
            return v

        if len(v) > 10:  # 限制最多10张参考图
            raise ValueError("最多支持10张参考图片")

        return v


class GoogleImagesConfigForm(BaseModel):
    """谷歌生图配置表单模型"""

    enabled: bool = False
    base_url: str = Field("", description="API基础URL")
    api_key: str = Field("", description="API密钥")
    default_model: str = "nano-banana"
    max_images_per_request: int = Field(10, description="单次请求最大图片数")
    timeout: int = Field(60, description="请求超时时间(秒)")

    # 积分配置
    credits_per_generation: int = Field(20, description="每次生成消耗积分")
    credits_per_image: int = Field(5, description="每张参考图额外积分")


class GoogleImagesTaskForm(BaseModel):
    """谷歌生图任务表单模型"""

    id: str
    user_id: str
    status: str
    prompt: str
    model: str = "nano-banana"
    input_images: Optional[List[str]] = None
    cloud_input_images: Optional[List[str]] = None
    result_images: Optional[List[str]] = None
    cloud_result_images: Optional[List[str]] = None
    credits_cost: Optional[int] = None
    fail_reason: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: Optional[str] = None
    finish_time: Optional[str] = None


# ======================== SQLAlchemy 数据库模型 ========================


class GoogleImagesConfig(Base):
    """谷歌生图配置表"""

    __tablename__ = "google_images_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False, nullable=False)
    base_url = Column(String(500), nullable=True)
    api_key = Column(Text, nullable=True)

    # 模型配置
    default_model = Column(String(50), default="nano-banana", nullable=False)
    max_images_per_request = Column(Integer, default=10, nullable=False)
    timeout = Column(Integer, default=60, nullable=False)

    # 积分配置
    credits_per_generation = Column(Integer, default=20, nullable=False)
    credits_per_image = Column(Integer, default=5, nullable=False)

    # 扩展配置
    additional_config = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, nullable=True)

    @classmethod
    def get_config(cls):
        """获取配置"""
        try:
            with get_db() as db:
                return db.query(cls).filter(cls.id == 1).first()
        except Exception as e:
            print(f"获取谷歌生图配置失败: {str(e)}")
            return None

    @classmethod
    def save_config(cls, config_data: dict):
        """保存配置"""
        try:
            with get_db() as db:
                config = db.query(cls).filter(cls.id == 1).first()
                if config:
                    # 更新现有配置
                    for key, value in config_data.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
                    config.updated_at = datetime.now()
                else:
                    # 创建新配置
                    config_data["id"] = 1
                    config = cls(**config_data)
                    db.add(config)

                db.commit()
                db.refresh(config)
                return config
        except Exception as e:
            print(f"保存谷歌生图配置失败: {str(e)}")
            raise e

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "default_model": self.default_model,
            "max_images_per_request": self.max_images_per_request,
            "timeout": self.timeout,
            "credits_per_generation": self.credits_per_generation,
            "credits_per_image": self.credits_per_image,
            "additional_config": self.additional_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class GoogleImagesTask(Base):
    """谷歌生图任务表"""

    __tablename__ = "google_images_tasks"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    status = Column(String(20), default="submitted", nullable=False)

    # 请求参数
    prompt = Column(Text, nullable=False)
    model = Column(String(50), default="nano-banana", nullable=False)
    size = Column(String(20), nullable=True)
    quality = Column(String(20), nullable=True)
    style = Column(String(20), nullable=True)

    # 图片数据
    input_images = Column(JSON, nullable=True)  # 原始输入图片
    cloud_input_images = Column(JSON, nullable=True)  # 云端输入图片URL
    result_images = Column(JSON, nullable=True)  # 原始结果图片
    cloud_result_images = Column(JSON, nullable=True)  # 云端结果图片URL

    # 任务状态
    progress = Column(String(10), default="0%")
    fail_reason = Column(Text, nullable=True)

    # 积分消耗
    credits_cost = Column(Integer, nullable=True)

    # 扩展属性
    properties = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, nullable=True)
    finish_time = Column(DateTime, nullable=True)

    @classmethod
    def create_task(cls, task_data: dict):
        """创建新任务"""
        if "id" not in task_data:
            task_data["id"] = str(uuid.uuid4())

        try:
            with get_db() as db:
                task = cls(**task_data)
                db.add(task)
                db.commit()
                db.refresh(task)
                return task
        except Exception as e:
            print(f"创建谷歌生图任务失败: {str(e)}")
            raise e

    @classmethod
    def get_task_by_id(cls, task_id: str):
        """根据ID获取任务"""
        try:
            with get_db() as db:
                return db.query(cls).filter(cls.id == task_id).first()
        except Exception as e:
            print(f"获取谷歌生图任务失败: {str(e)}")
            return None

    @classmethod
    def get_tasks_by_user(cls, user_id: str, limit: int = 20, offset: int = 0):
        """获取用户的任务列表"""
        try:
            with get_db() as db:
                return (
                    db.query(cls)
                    .filter(cls.user_id == user_id)
                    .order_by(cls.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )
        except Exception as e:
            print(f"获取用户谷歌生图任务列表失败: {str(e)}")
            return []

    @classmethod
    def update_task_status(cls, task_id: str, status_data: dict):
        """更新任务状态"""
        try:
            with get_db() as db:
                task = db.query(cls).filter(cls.id == task_id).first()
                if task:
                    for key, value in status_data.items():
                        if hasattr(task, key):
                            setattr(task, key, value)
                    task.updated_at = datetime.now()
                    db.commit()
                    db.refresh(task)
                    return task
                return None
        except Exception as e:
            print(f"更新谷歌生图任务状态失败: {str(e)}")
            raise e

    @classmethod
    def delete_task(cls, task_id: str) -> bool:
        """删除任务"""
        try:
            with get_db() as db:
                task = db.query(cls).filter(cls.id == task_id).first()
                if task:
                    db.delete(task)
                    db.commit()
                    return True
                return False
        except Exception as e:
            print(f"删除谷歌生图任务失败: {str(e)}")
            return False

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "prompt": self.prompt,
            "model": self.model,
            "size": self.size,
            "quality": self.quality,
            "style": self.style,
            "input_images": self.input_images,
            "cloud_input_images": self.cloud_input_images,
            "result_images": self.result_images,
            "cloud_result_images": self.cloud_result_images,
            "progress": self.progress,
            "fail_reason": self.fail_reason,
            "credits_cost": self.credits_cost,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "finish_time": self.finish_time.isoformat() if self.finish_time else None,
        }


class GoogleImagesCredit(Base):
    """谷歌生图积分记录表"""

    __tablename__ = "google_images_credits"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    task_id = Column(String(50), nullable=False)

    # 积分变化
    credit_amount = Column(Integer, nullable=False)
    credits_before = Column(Integer, nullable=True)
    credits_after = Column(Integer, nullable=True)

    # 操作信息
    operation_type = Column(String(20), default="deduct", nullable=False)
    model_name = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False)

    @classmethod
    def create_credit_log(cls, log_data: dict):
        """创建积分记录"""
        if "id" not in log_data:
            log_data["id"] = str(uuid.uuid4())

        try:
            with get_db() as db:
                credit = cls(**log_data)
                db.add(credit)
                db.commit()
                db.refresh(credit)
                return credit
        except Exception as e:
            print(f"创建谷歌生图积分记录失败: {str(e)}")
            raise e

    @classmethod
    def get_credits_by_user(cls, user_id: str, limit: int = 50):
        """获取用户的积分记录"""
        try:
            with get_db() as db:
                return (
                    db.query(cls)
                    .filter(cls.user_id == user_id)
                    .order_by(cls.created_at.desc())
                    .limit(limit)
                    .all()
                )
        except Exception as e:
            print(f"获取用户谷歌生图积分记录失败: {str(e)}")
            return []


# ======================== 响应模型 ========================


class GoogleImagesTaskResponse(BaseModel):
    """谷歌生图任务响应模型"""

    success: bool
    task_id: Optional[str] = None
    task: Optional[GoogleImagesTaskForm] = None
    error: Optional[str] = None


class GoogleImagesGenerateResponse(BaseModel):
    """谷歌生图生成响应模型"""

    success: bool
    task_id: Optional[str] = None
    credits_cost: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class GoogleImagesUserConfig(BaseModel):
    """谷歌生图用户配置模型"""

    enabled: bool
    supported_models: List[str]
    max_images_per_request: int
    default_model: str
    credits_per_generation: int
    credits_per_image: int
