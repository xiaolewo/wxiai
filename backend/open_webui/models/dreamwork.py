"""
DreamWork (即梦) 数据库模型
包含配置、任务、积分记录等所有相关模型
"""

from pydantic import BaseModel, Field
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
from open_webui.models.users import Users

# ======================== Pydantic 模型 ========================


class DreamWorkGenerateRequest(BaseModel):
    """即梦生成请求模型"""

    model: str  # doubao-seedream-3-0-t2i-250415 或 doubao-seededit-3-0-i2i-250628
    prompt: str
    response_format: str = "url"  # url 或 b64_json
    size: str = "1024x1024"  # 图片尺寸或 adaptive
    seed: Optional[int] = None
    guidance_scale: Optional[float] = None
    watermark: bool = True
    image: Optional[str] = None  # 图生图时的输入图片(base64)


class DreamWorkConfigForm(BaseModel):
    """即梦配置表单模型"""

    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    text_to_image_model: str = "doubao-seedream-3-0-t2i-250415"
    image_to_image_model: str = "doubao-seededit-3-0-i2i-250628"
    default_size: str = "1024x1024"
    default_guidance_scale: float = 2.5
    watermark_enabled: bool = True
    credits_per_generation: int = 10  # 每次生成消耗的积分
    max_concurrent_tasks: int = 5
    task_timeout: int = 300000  # 5分钟超时


class DreamWorkTaskForm(BaseModel):
    """即梦任务表单模型"""

    id: str
    action: str  # TEXT_TO_IMAGE, IMAGE_TO_IMAGE
    status: str
    prompt: str
    model: str
    size: str
    guidance_scale: Optional[float] = None
    seed: Optional[int] = None
    watermark: bool = True
    submit_time: int
    finish_time: Optional[int] = None
    progress: str = "0%"
    image_url: Optional[str] = None
    fail_reason: Optional[str] = None
    input_image: Optional[str] = None  # 图生图的输入图片


# ======================== SQLAlchemy 模型 ========================


class DreamWorkConfig(Base):
    """即梦配置表"""

    __tablename__ = "dreamwork_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    base_url = Column(String(500))
    api_key = Column(Text)
    text_to_image_model = Column(String(100), default="doubao-seedream-3-0-t2i-250415")
    image_to_image_model = Column(String(100), default="doubao-seededit-3-0-i2i-250628")
    default_size = Column(String(50), default="1024x1024")
    default_guidance_scale = Column(Float, default=2.5)
    watermark_enabled = Column(Boolean, default=True)
    credits_per_generation = Column(Integer, default=10)
    max_concurrent_tasks = Column(Integer, default=5)
    task_timeout = Column(Integer, default=300000)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def get_config(cls):
        """获取配置"""
        with get_db() as db:
            config = db.query(cls).first()
            return config

    @classmethod
    def save_config(cls, config_data: dict):
        """保存配置"""
        with get_db() as db:
            config = db.query(cls).first()
            if config:
                # 更新现有配置
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                config.updated_at = datetime.utcnow()
            else:
                # 创建新配置
                config_data["created_at"] = datetime.utcnow()
                config_data["updated_at"] = datetime.utcnow()
                config = cls(**config_data)
                db.add(config)

            db.commit()
            db.refresh(config)
            return config

    def save(self):
        """保存当前配置"""
        with get_db() as db:
            self.updated_at = datetime.utcnow()
            db.merge(self)
            db.commit()

    def to_dict(self):
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "text_to_image_model": self.text_to_image_model,
            "image_to_image_model": self.image_to_image_model,
            "default_size": self.default_size,
            "default_guidance_scale": self.default_guidance_scale,
            "watermark_enabled": self.watermark_enabled,
            "credits_per_generation": self.credits_per_generation,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
        }


class DreamWorkTask(Base):
    """即梦任务表"""

    __tablename__ = "dreamwork_tasks"

    id = Column(String(50), primary_key=True)  # 任务ID
    user_id = Column(String(50), index=True)
    action = Column(String(50))  # TEXT_TO_IMAGE, IMAGE_TO_IMAGE
    status = Column(
        String(50), default="SUBMITTED"
    )  # SUBMITTED, IN_PROGRESS, SUCCESS, FAILURE
    prompt = Column(Text)
    model = Column(String(100))  # 使用的模型
    size = Column(String(50), default="1024x1024")
    guidance_scale = Column(Float)
    seed = Column(Integer)
    watermark = Column(Boolean, default=True)
    credits_cost = Column(Integer, default=0)

    # 时间字段
    submit_time = Column(DateTime, default=func.now())
    start_time = Column(DateTime)
    finish_time = Column(DateTime)
    progress = Column(String(20), default="0%")

    # 结果字段
    image_url = Column(Text)
    fail_reason = Column(Text)
    input_image = Column(Text)  # 图生图的输入图片(base64或URL)

    # 元数据
    properties = Column(JSON)  # 额外属性
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 创建索引
    __table_args__ = (
        Index("idx_dreamwork_user_created", "user_id", "created_at"),
        Index("idx_dreamwork_status_updated", "status", "updated_at"),
    )

    @classmethod
    def create_task(
        cls,
        user_id: str,
        action: str,
        prompt: str,
        model: str,
        size: str = "1024x1024",
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        watermark: bool = True,
        credits_cost: int = 10,
        input_image: Optional[str] = None,
        properties: Optional[dict] = None,
    ):
        """创建任务记录"""
        with get_db() as db:
            task_id = str(uuid.uuid4())
            task = cls(
                id=task_id,
                user_id=user_id,
                action=action,
                prompt=prompt,
                model=model,
                size=size,
                guidance_scale=guidance_scale,
                seed=seed,
                watermark=watermark,
                credits_cost=credits_cost,
                input_image=input_image,
                properties=properties or {},
                status="SUBMITTED",
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    @classmethod
    def get_task_by_id(cls, task_id: str):
        """根据ID获取任务"""
        with get_db() as db:
            return db.query(cls).filter(cls.id == task_id).first()

    @classmethod
    def get_user_tasks(cls, user_id: str, page: int = 1, limit: int = 20):
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
    def get_user_task_count(cls, user_id: str):
        """获取用户任务总数"""
        with get_db() as db:
            return db.query(cls).filter(cls.user_id == user_id).count()

    @classmethod
    def get_user_recent_tasks(cls, user_id: str, limit: int = 10):
        """获取用户最近任务"""
        with get_db() as db:
            return (
                db.query(cls)
                .filter(cls.user_id == user_id)
                .filter(cls.updated_at > datetime.utcnow() - timedelta(minutes=30))
                .order_by(cls.updated_at.desc())
                .limit(limit)
                .all()
            )

    def update_status(self, status: str):
        """更新任务状态"""
        with get_db() as db:
            self.status = status
            self.updated_at = datetime.utcnow()
            if status == "IN_PROGRESS" and not self.start_time:
                self.start_time = datetime.utcnow()
            elif status in ["SUCCESS", "FAILURE"]:
                self.finish_time = datetime.utcnow()
                self.progress = "100%" if status == "SUCCESS" else "0%"
            db.commit()

    def update_from_api_response(self, api_response: dict):
        """从API响应更新任务数据"""
        try:
            with get_db() as db:
                print(f"🎨 【DreamWork】更新任务: {self.id}")

                # 更新状态
                if "error" in api_response:
                    self.status = "FAILURE"
                    self.fail_reason = api_response.get("error", {}).get(
                        "message", "生成失败"
                    )
                    self.progress = "0%"
                elif "data" in api_response and api_response["data"]:
                    # 成功生成
                    self.status = "SUCCESS"
                    self.progress = "100%"
                    # 获取图片URL
                    image_data = (
                        api_response["data"][0]
                        if isinstance(api_response["data"], list)
                        else api_response["data"]
                    )
                    self.image_url = image_data.get("url", "")
                    if not self.finish_time:
                        self.finish_time = datetime.utcnow()

                self.updated_at = datetime.utcnow()
                db.add(self)
                db.commit()
                db.refresh(self)

                print(f"🎨 【DreamWork】任务更新完成: {self.id}, 状态: {self.status}")

        except Exception as e:
            print(f"❌ 【DreamWork】更新任务失败: {e}")
            import traceback

            traceback.print_exc()
            raise

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "action": self.action,
            "status": self.status,
            "prompt": self.prompt,
            "model": self.model,
            "size": self.size,
            "guidance_scale": self.guidance_scale,
            "seed": self.seed,
            "watermark": self.watermark,
            "submitTime": (
                int(self.submit_time.timestamp() * 1000) if self.submit_time else 0
            ),
            "startTime": (
                int(self.start_time.timestamp() * 1000) if self.start_time else 0
            ),
            "finishTime": (
                int(self.finish_time.timestamp() * 1000) if self.finish_time else 0
            ),
            "progress": self.progress,
            "imageUrl": self.image_url,
            "failReason": self.fail_reason,
            "inputImage": self.input_image,
            "creditsCost": self.credits_cost,
            "properties": self.properties or {},
        }


class DreamWorkCredit(Base):
    """即梦积分记录表"""

    __tablename__ = "dreamwork_credits"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), index=True)
    amount = Column(Integer)  # 正数为充值，负数为消费
    balance = Column(Integer)  # 操作后余额
    reason = Column(String(200))  # 操作原因
    task_id = Column(String(50))  # 关联任务ID（如果有）
    created_at = Column(DateTime, default=func.now())

    # 创建索引
    __table_args__ = (Index("idx_dreamwork_user_created", "user_id", "created_at"),)

    @classmethod
    def add_credit_record(
        cls, user_id: str, amount: int, reason: str, task_id: Optional[str] = None
    ):
        """添加积分记录"""
        with get_db() as db:
            # 获取当前余额
            last_record = (
                db.query(cls)
                .filter(cls.user_id == user_id)
                .order_by(cls.created_at.desc())
                .first()
            )

            current_balance = last_record.balance if last_record else 0
            new_balance = current_balance + amount

            record = cls(
                user_id=user_id,
                amount=amount,
                balance=new_balance,
                reason=reason,
                task_id=task_id,
            )
            db.add(record)
            db.commit()
            return new_balance

    @classmethod
    def get_user_balance(cls, user_id: str):
        """获取用户当前余额"""
        with get_db() as db:
            last_record = (
                db.query(cls)
                .filter(cls.user_id == user_id)
                .order_by(cls.created_at.desc())
                .first()
            )
            return last_record.balance if last_record else 0

    @classmethod
    def get_user_credit_history(cls, user_id: str, page: int = 1, limit: int = 50):
        """获取用户积分历史"""
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
