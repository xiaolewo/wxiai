"""
可灵对口型功能数据模型
基于可灵对口型API规范的完整数据模型定义
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


class KlingLipSyncConfig(Base):
    __tablename__ = "kling_lip_sync_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False, comment="是否启用对口型功能")
    base_url = Column(
        String(500), default="https://api.klingai.com", comment="API基础URL"
    )
    api_key = Column(Text, comment="API密钥")

    # 积分配置
    credits_per_task = Column(Integer, default=50, comment="每个对口型任务消耗积分")

    # API配置
    max_concurrent_tasks = Column(Integer, default=3, comment="最大并发任务数")
    task_timeout = Column(Integer, default=300000, comment="任务超时时间(毫秒)")

    # 默认参数配置
    default_mode = Column(String(50), default="text2video", comment="默认模式")
    default_voice_id = Column(
        String(100), default="girlfriend_1_speech02", comment="默认音色ID"
    )
    default_voice_language = Column(String(10), default="zh", comment="默认语言")

    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def get_config(cls):
        """获取可灵对口型配置"""
        with get_db() as db:
            return db.query(cls).filter(cls.id == 1).first()

    @classmethod
    def save_config(cls, config_data: dict):
        """保存可灵对口型配置"""
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
            "default_mode": self.default_mode,
            "default_voice_id": self.default_voice_id,
            "default_voice_language": self.default_voice_language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class KlingLipSyncTask(Base):
    __tablename__ = "kling_lip_sync_tasks"

    id = Column(String(50), primary_key=True, comment="任务ID")
    user_id = Column(String(50), nullable=False, index=True, comment="用户ID")
    task_id = Column(String(100), comment="外部任务ID")

    # 任务状态
    status = Column(String(50), default="submitted", comment="任务状态")
    task_status_msg = Column(Text, comment="状态消息")

    # 输入参数
    video_id = Column(String(100), comment="视频ID")
    video_url = Column(Text, comment="视频URL")
    uploaded_video_url = Column(Text, comment="上传的视频云存储URL")
    mode = Column(String(50), default="text2video", comment="模式")
    text = Column(Text, nullable=False, comment="对口型文本")
    voice_id = Column(String(100), comment="音色ID")
    voice_language = Column(String(10), comment="语言")

    # 结果数据
    result_video_url = Column(Text, comment="生成结果视频URL")
    cloud_result_url = Column(Text, comment="云存储结果视频URL")
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
            "video_id": self.video_id,
            "video_url": self.video_url,
            "uploaded_video_url": self.uploaded_video_url,
            "mode": self.mode,
            "text": self.text,
            "voice_id": self.voice_id,
            "voice_language": self.voice_language,
            "result_video_url": self.result_video_url,
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


class KlingLipSyncCredits(Base):
    __tablename__ = "kling_lip_sync_credits"

    id = Column(String(50), primary_key=True, comment="积分记录ID")
    user_id = Column(String(50), nullable=False, index=True, comment="用户ID")
    credits_balance = Column(Integer, default=0, comment="剩余积分")
    total_used = Column(Integer, default=0, comment="总消耗积分")
    total_recharged = Column(Integer, default=0, comment="总充值积分")

    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "credits_balance": self.credits_balance,
            "total_used": self.total_used,
            "total_recharged": self.total_recharged,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ======================== Pydantic 请求响应模型 ========================


class KlingLipSyncConfigForm(BaseModel):
    """可灵对口型配置表单"""

    enabled: bool = Field(default=False, description="是否启用对口型功能")
    base_url: str = Field(default="https://api.klingai.com", description="API基础URL")
    api_key: str = Field(description="API密钥")
    credits_per_task: int = Field(default=50, description="每个对口型任务消耗积分")
    max_concurrent_tasks: int = Field(default=3, description="最大并发任务数")
    task_timeout: int = Field(default=300000, description="任务超时时间(毫秒)")
    default_mode: str = Field(default="text2video", description="默认模式")
    default_voice_id: str = Field(
        default="girlfriend_1_speech02", description="默认音色ID"
    )
    default_voice_language: str = Field(default="zh", description="默认语言")


class KlingLipSyncRequest(BaseModel):
    """可灵对口型请求"""

    video_id: Optional[str] = Field(None, description="视频ID")
    video_url: Optional[str] = Field(None, description="视频URL")
    mode: str = Field(default="text2video", description="模式")
    text: str = Field(description="对口型文本")
    voice_id: str = Field(default="girlfriend_1_speech02", description="音色ID")
    voice_language: str = Field(default="zh", description="语言")


class KlingLipSyncTaskForm(BaseModel):
    """可灵对口型任务表单"""

    request: KlingLipSyncRequest = Field(description="对口型请求")


class KlingLipSyncResponse(BaseModel):
    """可灵对口型响应"""

    code: int
    message: str
    request_id: str
    data: Optional[Dict[str, Any]] = None


# ======================== 数据操作类 ========================


class KlingLipSyncConfigs:
    """可灵对口型配置操作类"""

    @staticmethod
    def get_config():
        """获取配置"""
        return KlingLipSyncConfig.get_config()

    @staticmethod
    def save_config(config_data: dict):
        """保存配置"""
        return KlingLipSyncConfig.save_config(config_data)

    @staticmethod
    def is_enabled():
        """检查是否启用"""
        config = KlingLipSyncConfig.get_config()
        return config and config.enabled


class KlingLipSyncTasks:
    """可灵对口型任务操作类"""

    @staticmethod
    def create_task(user_id: str, task_data: dict) -> KlingLipSyncTask:
        """创建任务"""
        with get_db() as db:
            task_id = str(uuid.uuid4())
            task = KlingLipSyncTask(id=task_id, user_id=user_id, **task_data)
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    @staticmethod
    def get_task_by_id(task_id: str) -> Optional[KlingLipSyncTask]:
        """根据ID获取任务"""
        with get_db() as db:
            return (
                db.query(KlingLipSyncTask)
                .filter(KlingLipSyncTask.id == task_id)
                .first()
            )

    @staticmethod
    def get_user_tasks(
        user_id: str, limit: int = 50, offset: int = 0
    ) -> List[KlingLipSyncTask]:
        """获取用户任务列表"""
        with get_db() as db:
            return (
                db.query(KlingLipSyncTask)
                .filter(KlingLipSyncTask.user_id == user_id)
                .order_by(KlingLipSyncTask.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

    @staticmethod
    def update_task(task_id: str, update_data: dict) -> Optional[KlingLipSyncTask]:
        """更新任务"""
        with get_db() as db:
            task = (
                db.query(KlingLipSyncTask)
                .filter(KlingLipSyncTask.id == task_id)
                .first()
            )
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
            task = (
                db.query(KlingLipSyncTask)
                .filter(KlingLipSyncTask.id == task_id)
                .first()
            )
            if task:
                db.delete(task)
                db.commit()
                return True
            return False


class KlingLipSyncCreditsManager:
    """可灵对口型积分管理类"""

    @staticmethod
    def get_user_credits(user_id: str) -> KlingLipSyncCredits:
        """获取用户积分"""
        with get_db() as db:
            credits = (
                db.query(KlingLipSyncCredits)
                .filter(KlingLipSyncCredits.user_id == user_id)
                .first()
            )
            if not credits:
                credits = KlingLipSyncCredits(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    credits_balance=0,
                    total_used=0,
                    total_recharged=0,
                )
                db.add(credits)
                db.commit()
                db.refresh(credits)
            return credits

    @staticmethod
    def consume_credits(user_id: str, amount: int) -> bool:
        """消费积分"""
        with get_db() as db:
            credits = KlingLipSyncCreditsManager.get_user_credits(user_id)
            if credits.credits_balance >= amount:
                credits.credits_balance -= amount
                credits.total_used += amount
                credits.updated_at = datetime.now()
                db.commit()
                return True
            return False

    @staticmethod
    def add_credits(user_id: str, amount: int) -> bool:
        """增加积分"""
        with get_db() as db:
            credits = KlingLipSyncCreditsManager.get_user_credits(user_id)
            credits.credits_balance += amount
            credits.total_recharged += amount
            credits.updated_at = datetime.now()
            db.commit()
            return True
