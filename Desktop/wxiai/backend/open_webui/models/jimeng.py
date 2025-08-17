"""
即梦视频生成数据模型
包含配置管理和任务管理
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid
import json

from open_webui.internal.db import Base, SessionLocal, get_db


# ======================== Pydantic 数据模型 ========================


class JimengConfigForm(BaseModel):
    """即梦配置表单模型"""

    enabled: bool = False
    base_url: Optional[str] = "https://ark.cn-beijing.volces.com"
    api_key: Optional[str] = None
    default_duration: str = "5"
    default_aspect_ratio: str = "16:9"
    default_cfg_scale: float = 0.5
    credits_per_5s: int = 30
    credits_per_10s: int = 60
    max_concurrent_tasks: int = 5
    task_timeout: int = 600000
    query_interval: int = 10000
    detected_api_path: Optional[str] = None


class JimengGenerateRequest(BaseModel):
    """即梦视频生成请求模型"""

    prompt: str = Field(..., description="视频描述")
    image_url: Optional[str] = Field(None, description="图生视频输入图片URL")
    image: Optional[str] = Field(None, description="图生视频输入图片base64数据")
    duration: str = Field("5", description="视频时长: 5, 10")
    aspect_ratio: str = Field(
        "16:9", description="画面比例: 1:1, 21:9, 16:9, 9:16, 4:3, 3:4"
    )
    cfg_scale: float = Field(0.5, description="CFG Scale")

    # 内部使用字段
    external_task_id: Optional[str] = None
    callback_url: Optional[str] = None


class JimengTaskForm(BaseModel):
    """即梦任务表单模型"""

    id: str
    user_id: str
    action: str
    status: str
    prompt: str
    duration: str
    aspect_ratio: str
    cfg_scale: float
    image_url: Optional[str] = None
    input_image: Optional[str] = None
    external_task_id: Optional[str] = None
    video_url: Optional[str] = None
    progress: str = "0%"
    fail_reason: Optional[str] = None
    credits_cost: int
    properties: Optional[Dict[str, Any]] = None


# ======================== SQLAlchemy ORM 模型 ========================


class JimengConfig(Base):
    """即梦配置表"""

    __tablename__ = "jimeng_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False, nullable=False, comment="是否启用即梦服务")
    base_url = Column(Text, nullable=True, comment="即梦API基础URL")
    api_key = Column(Text, nullable=True, comment="即梦API密钥")

    # 默认参数配置
    default_duration = Column(
        String(10), default="5", nullable=False, comment="默认视频时长"
    )
    default_aspect_ratio = Column(
        String(10), default="16:9", nullable=False, comment="默认画面比例"
    )
    default_cfg_scale = Column(
        Float, default=0.5, nullable=False, comment="默认CFG Scale"
    )

    # 积分配置
    credits_per_5s = Column(
        Integer, default=30, nullable=False, comment="5秒视频积分消耗"
    )
    credits_per_10s = Column(
        Integer, default=60, nullable=False, comment="10秒视频积分消耗"
    )

    # 系统配置
    max_concurrent_tasks = Column(
        Integer, default=5, nullable=False, comment="最大并发任务数"
    )
    task_timeout = Column(
        Integer, default=600000, nullable=False, comment="任务超时时间(毫秒)"
    )
    query_interval = Column(
        Integer, default=10000, nullable=False, comment="轮询间隔(毫秒)"
    )

    # API路径配置
    detected_api_path = Column(Text, nullable=True, comment="检测到的API路径")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    @classmethod
    def get_config(cls) -> Optional["JimengConfig"]:
        """获取即梦配置"""
        with get_db() as db:
            return db.query(cls).first()

    @classmethod
    def save_config(cls, config_data: dict) -> "JimengConfig":
        """保存即梦配置"""
        with get_db() as db:
            config = db.query(cls).first()

            if config:
                # 更新现有配置
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                config.updated_at = func.now()
            else:
                # 创建新配置
                config = cls(**config_data)
                db.add(config)

            db.commit()
            db.refresh(config)
            return config

    def get_credits_cost(self, duration: str) -> int:
        """获取指定时长的积分消耗"""
        if duration == "5":
            return self.credits_per_5s
        elif duration == "10":
            return self.credits_per_10s
        else:
            return self.credits_per_5s  # 默认值

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "default_duration": self.default_duration,
            "default_aspect_ratio": self.default_aspect_ratio,
            "default_cfg_scale": self.default_cfg_scale,
            "credits_per_5s": self.credits_per_5s,
            "credits_per_10s": self.credits_per_10s,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
            "query_interval": self.query_interval,
            "detected_api_path": self.detected_api_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class JimengTask(Base):
    """即梦任务表"""

    __tablename__ = "jimeng_tasks"

    id = Column(String(255), primary_key=True, comment="任务ID")
    user_id = Column(String(255), nullable=False, comment="用户ID")
    action = Column(
        String(50), nullable=False, comment="任务类型: TEXT_TO_VIDEO, IMAGE_TO_VIDEO"
    )
    status = Column(String(50), default="submitted", nullable=False, comment="任务状态")

    # 生成参数
    prompt = Column(Text, nullable=False, comment="视频描述")
    duration = Column(String(10), nullable=False, comment="视频时长")
    aspect_ratio = Column(String(10), nullable=False, comment="画面比例")
    cfg_scale = Column(Float, nullable=False, comment="CFG Scale")

    # 图生视频参数
    image_url = Column(Text, nullable=True, comment="输入图片URL(图生视频)")
    input_image = Column(Text, nullable=True, comment="输入图片base64数据")

    # 任务结果
    external_task_id = Column(String(255), nullable=True, comment="即梦返回的任务ID")
    video_url = Column(Text, nullable=True, comment="生成的视频URL")
    progress = Column(String(50), default="0%", comment="任务进度")
    fail_reason = Column(Text, nullable=True, comment="失败原因")

    # 积分相关
    credits_cost = Column(Integer, nullable=False, comment="积分消耗")

    # 扩展属性
    properties = Column(JSON, nullable=True, comment="扩展属性JSON")

    # 时间戳
    submit_time = Column(
        DateTime, default=func.now(), nullable=False, comment="提交时间"
    )
    start_time = Column(DateTime, nullable=True, comment="开始处理时间")
    complete_time = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # 创建索引
    __table_args__ = (
        Index("idx_jimeng_tasks_user_id", "user_id"),
        Index("idx_jimeng_tasks_status", "status"),
        Index("idx_jimeng_tasks_created_at", "created_at"),
        Index("idx_jimeng_tasks_user_status", "user_id", "status"),
    )

    @classmethod
    def create_task(
        cls,
        user_id: str,
        action: str,
        prompt: str,
        duration: str,
        aspect_ratio: str,
        cfg_scale: float,
        credits_cost: int,
        image_url: Optional[str] = None,
        input_image: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "JimengTask":
        """创建即梦任务"""
        task_id = str(uuid.uuid4())

        task = cls(
            id=task_id,
            user_id=user_id,
            action=action,
            status="submitted",
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            cfg_scale=cfg_scale,
            image_url=image_url,
            input_image=input_image,
            credits_cost=credits_cost,
            properties=properties or {},
        )

        with get_db() as db:
            db.add(task)
            db.commit()
            db.refresh(task)

        return task

    @classmethod
    def get_task_by_id(cls, task_id: str) -> Optional["JimengTask"]:
        """根据ID获取任务"""
        with get_db() as db:
            return db.query(cls).filter(cls.id == task_id).first()

    @classmethod
    def get_user_tasks(
        cls, user_id: str, page: int = 1, limit: int = 20
    ) -> List["JimengTask"]:
        """获取用户任务列表"""
        with get_db() as db:
            offset = (page - 1) * limit
            return (
                db.query(cls)
                .filter(cls.user_id == user_id)
                .order_by(cls.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

    @classmethod
    def get_user_task_count(cls, user_id: str) -> int:
        """获取用户任务总数"""
        with get_db() as db:
            return db.query(cls).filter(cls.user_id == user_id).count()

    def update_status(self, status: str, progress: str = None):
        """更新任务状态"""
        with get_db() as db:
            task = db.query(JimengTask).filter(JimengTask.id == self.id).first()
            if task:
                task.status = status
                if progress:
                    task.progress = progress

                if status == "processing" and not task.start_time:
                    task.start_time = func.now()
                elif status in ["succeed", "failed"] and not task.complete_time:
                    task.complete_time = func.now()

                task.updated_at = func.now()
                db.commit()

                # 更新当前实例
                self.status = status
                if progress:
                    self.progress = progress

    def update_from_api_response(self, response: dict):
        """从API响应更新任务信息"""
        print(f"🎬 【即梦任务】更新任务 {self.id} 从API响应: {response}")

        with get_db() as db:
            task = db.query(JimengTask).filter(JimengTask.id == self.id).first()
            if not task:
                print(f"❌ 【即梦任务】任务 {self.id} 不存在")
                return

            # 解析即梦API响应
            if response.get("code") == "success":
                # 提交成功，保存外部任务ID
                external_task_id = response.get("data")
                if external_task_id:
                    task.external_task_id = str(external_task_id)
                    task.status = "processing"
                    task.start_time = func.now()
                    print(f"🎬 【即梦任务】任务提交成功，外部ID: {external_task_id}")
            else:
                # 提交失败
                error_message = response.get("message", "提交失败")
                task.status = "failed"
                task.fail_reason = error_message
                task.complete_time = func.now()
                print(f"❌ 【即梦任务】任务提交失败: {error_message}")

            task.updated_at = func.now()
            db.commit()

            # 更新当前实例属性
            self.external_task_id = task.external_task_id
            self.status = task.status
            self.fail_reason = task.fail_reason

    def update_result(self, video_url: str, status: str = "succeed"):
        """更新任务结果"""
        with get_db() as db:
            task = db.query(JimengTask).filter(JimengTask.id == self.id).first()
            if task:
                task.video_url = video_url
                task.status = status
                task.progress = "100%"
                task.complete_time = func.now()
                task.updated_at = func.now()
                db.commit()

                # 更新当前实例
                self.video_url = video_url
                self.status = status
                self.progress = "100%"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "status": self.status,
            "prompt": self.prompt,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "cfg_scale": self.cfg_scale,
            "image_url": self.image_url,
            "input_image": self.input_image,
            "external_task_id": self.external_task_id,
            "video_url": self.video_url,
            "progress": self.progress,
            "fail_reason": self.fail_reason,
            "credits_cost": self.credits_cost,
            "properties": self.properties,
            "submit_time": self.submit_time.isoformat() if self.submit_time else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "complete_time": (
                self.complete_time.isoformat() if self.complete_time else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
