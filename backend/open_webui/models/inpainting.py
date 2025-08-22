"""
即梦涂抹消除功能数据模型
基于即梦涂抹消除API规范的完整数据模型定义
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON, Float
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import uuid

from open_webui.internal.db import Base, get_db

# ======================== SQLAlchemy 数据库模型 ========================


class InpaintingConfig(Base):
    __tablename__ = "inpainting_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False, comment="是否启用涂抹消除功能")
    base_url = Column(
        String(500), default="https://api.linkapi.org", comment="API基础URL"
    )
    api_key = Column(Text, comment="API密钥")

    # 积分配置
    credits_per_task = Column(Integer, default=50, comment="每个涂抹消除任务消耗积分")

    # API配置
    max_concurrent_tasks = Column(Integer, default=3, comment="最大并发任务数")
    task_timeout = Column(Integer, default=300000, comment="任务超时时间(毫秒)")

    # 默认参数配置（优化为更快速的设置）
    default_steps = Column(Integer, default=20, comment="默认采样步数")
    default_strength = Column(Float, default=0.8, comment="默认强度")
    default_scale = Column(Float, default=7.0, comment="默认文本描述程度")
    default_quality = Column(String(10), default="L", comment="默认质量(H/M/L)")
    default_dilate_size = Column(Integer, default=15, comment="默认mask膨胀半径")

    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def get_config(cls):
        """获取涂抹消除配置"""
        with get_db() as db:
            return db.query(cls).filter(cls.id == 1).first()

    @classmethod
    def save_config(cls, config_data: dict):
        """保存涂抹消除配置"""
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

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "credits_per_task": self.credits_per_task,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
            "default_steps": self.default_steps,
            "default_strength": self.default_strength,
            "default_scale": self.default_scale,
            "default_quality": self.default_quality,
            "default_dilate_size": self.default_dilate_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InpaintingTask(Base):
    __tablename__ = "inpainting_tasks"

    id = Column(String(50), primary_key=True, comment="任务ID")
    user_id = Column(String(50), nullable=False, index=True, comment="用户ID")
    task_id = Column(String(100), comment="外部任务ID")

    # 任务状态
    status = Column(String(50), default="submitted", comment="任务状态")
    task_status_msg = Column(Text, comment="状态消息")

    # 输入数据
    input_image_url = Column(Text, comment="输入图片URL")
    mask_image_url = Column(Text, comment="Mask图片URL")
    uploaded_input_url = Column(Text, comment="上传的输入图片云存储URL")
    uploaded_mask_url = Column(Text, comment="上传的Mask图片云存储URL")

    # 参数设置
    steps = Column(Integer, default=30, comment="采样步数")
    strength = Column(Float, default=0.8, comment="强度")
    scale = Column(Float, default=7.0, comment="文本描述程度")
    quality = Column(String(10), default="M", comment="质量(H/M/L)")
    dilate_size = Column(Integer, default=15, comment="mask膨胀半径")
    seed = Column(Integer, default=0, comment="随机种子")

    # 结果数据
    result_image_url = Column(Text, comment="生成结果图片URL")
    cloud_result_url = Column(Text, comment="云存储结果图片URL")
    fail_reason = Column(Text, comment="失败原因")

    # 积分和时间
    credits_cost = Column(Integer, default=0, comment="消耗积分")
    submit_time = Column(DateTime, comment="提交时间")
    start_time = Column(DateTime, comment="开始处理时间")
    finish_time = Column(DateTime, comment="完成时间")

    # 请求响应数据
    request_data = Column(Text, comment="请求数据JSON")
    response_data = Column(Text, comment="响应数据JSON")

    # 元数据
    properties = Column(JSON, comment="扩展属性")
    progress = Column(String(20), default="0%", comment="进度")

    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "status": self.status,
            "task_status_msg": self.task_status_msg,
            "input_image_url": self.input_image_url,
            "mask_image_url": self.mask_image_url,
            "uploaded_input_url": self.uploaded_input_url,
            "uploaded_mask_url": self.uploaded_mask_url,
            "steps": self.steps,
            "strength": self.strength,
            "scale": self.scale,
            "quality": self.quality,
            "dilate_size": self.dilate_size,
            "seed": self.seed,
            "result_image_url": self.result_image_url,
            "cloud_result_url": self.cloud_result_url,
            "fail_reason": self.fail_reason,
            "credits_cost": self.credits_cost,
            "submit_time": self.submit_time.isoformat() if self.submit_time else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "finish_time": self.finish_time.isoformat() if self.finish_time else None,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "properties": self.properties,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ======================== Pydantic 请求响应模型 ========================


class InpaintingConfigForm(BaseModel):
    """涂抹消除配置表单"""

    enabled: bool = Field(default=False, description="是否启用涂抹消除功能")
    base_url: str = Field(default="https://api.linkapi.org", description="API基础URL")
    api_key: str = Field(description="API密钥")
    credits_per_task: int = Field(default=50, description="每个涂抹消除任务消耗积分")
    max_concurrent_tasks: int = Field(default=3, description="最大并发任务数")
    task_timeout: int = Field(default=300000, description="任务超时时间(毫秒)")
    default_steps: int = Field(default=30, description="默认采样步数")
    default_strength: float = Field(default=0.8, description="默认强度")
    default_scale: float = Field(default=7.0, description="默认文本描述程度")
    default_quality: str = Field(default="M", description="默认质量(H/M/L)")
    default_dilate_size: int = Field(default=15, description="默认mask膨胀半径")


class InpaintingRequest(BaseModel):
    """涂抹消除请求"""

    input_image_base64: str = Field(description="输入图片Base64")
    mask_image_base64: str = Field(description="Mask图片Base64")
    steps: Optional[int] = Field(default=30, description="采样步数")
    strength: Optional[float] = Field(default=0.8, description="强度")
    scale: Optional[float] = Field(default=7.0, description="文本描述程度")
    quality: Optional[str] = Field(default="M", description="质量(H/M/L)")
    dilate_size: Optional[int] = Field(default=15, description="mask膨胀半径")
    seed: Optional[int] = Field(default=0, description="随机种子")


class InpaintingTaskForm(BaseModel):
    """涂抹消除任务表单"""

    request: InpaintingRequest = Field(description="涂抹消除请求")


class InpaintingResponse(BaseModel):
    """涂抹消除响应"""

    code: int
    message: str
    request_id: str
    data: Optional[Dict[str, Any]] = None


# ======================== 数据操作类 ========================


class InpaintingConfigs:
    """涂抹消除配置操作类"""

    @staticmethod
    def get_config():
        """获取配置"""
        return InpaintingConfig.get_config()

    @staticmethod
    def save_config(config_data: dict):
        """保存配置"""
        return InpaintingConfig.save_config(config_data)

    @staticmethod
    def is_enabled():
        """检查是否启用"""
        config = InpaintingConfig.get_config()
        return config and config.enabled


class InpaintingTasks:
    """涂抹消除任务操作类"""

    @staticmethod
    def create_task(user_id: str, task_data: dict) -> InpaintingTask:
        """创建任务"""
        with get_db() as db:
            task_id = str(uuid.uuid4())
            task = InpaintingTask(id=task_id, user_id=user_id, **task_data)
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    @staticmethod
    def get_task_by_id(task_id: str) -> Optional[InpaintingTask]:
        """根据ID获取任务"""
        with get_db() as db:
            return db.query(InpaintingTask).filter(InpaintingTask.id == task_id).first()

    @staticmethod
    def get_user_tasks(
        user_id: str, limit: int = 50, offset: int = 0
    ) -> List[InpaintingTask]:
        """获取用户任务列表"""
        with get_db() as db:
            return (
                db.query(InpaintingTask)
                .filter(InpaintingTask.user_id == user_id)
                .order_by(InpaintingTask.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

    @staticmethod
    def update_task(task_id: str, update_data: dict) -> Optional[InpaintingTask]:
        """更新任务"""
        with get_db() as db:
            task = db.query(InpaintingTask).filter(InpaintingTask.id == task_id).first()
            if task:
                for key, value in update_data.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = datetime.now()
                db.commit()
                db.refresh(task)
            return task

    @staticmethod
    def delete_task(task_id: str) -> bool:
        """删除任务"""
        with get_db() as db:
            task = db.query(InpaintingTask).filter(InpaintingTask.id == task_id).first()
            if task:
                db.delete(task)
                db.commit()
                return True
            return False
