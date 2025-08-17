"""
Midjourney 数据库模型
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


class MJReferenceImage(BaseModel):
    id: str
    base64: str
    weight: float = 1.0
    type: str = "normal"  # normal, style, character
    filename: Optional[str] = None


class MJAdvancedParams(BaseModel):
    chaos: Optional[int] = None
    stylize: Optional[int] = None
    seed: Optional[int] = None
    weird: Optional[int] = None
    quality: Optional[float] = None
    version: Optional[str] = None
    aspect_ratio: Optional[str] = None
    custom_aspect_ratio: Optional[Dict[str, int]] = None
    tile: Optional[bool] = None
    no_commands: Optional[bool] = None


class MJGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    mode: str = "fast"
    reference_images: Optional[List[MJReferenceImage]] = None
    advanced_params: Optional[MJAdvancedParams] = None


class MJActionRequest(BaseModel):
    task_id: str
    custom_id: str


class MJModalRequest(BaseModel):
    task_id: str
    prompt: Optional[str] = None
    mask_base64: Optional[str] = None


class MJButton(BaseModel):
    custom_id: str
    emoji: str
    label: str
    style: int
    type: int


class MJTaskForm(BaseModel):
    id: str
    action: str
    status: str
    prompt: str
    prompt_en: str
    description: str
    submit_time: int
    start_time: int
    finish_time: int
    progress: str
    image_url: Optional[str] = None
    fail_reason: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    buttons: Optional[List[MJButton]] = None


class MJConfigForm(BaseModel):
    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    modes: Dict[str, Dict[str, Any]] = {
        "turbo": {"enabled": True, "credits": 10},
        "fast": {"enabled": True, "credits": 5},
        "relax": {"enabled": True, "credits": 2},
    }
    default_mode: str = "fast"
    max_concurrent_tasks: int = 5
    task_timeout: int = 300000


# ======================== SQLAlchemy 模型 ========================


class MJConfig(Base):
    """MJ配置表"""

    __tablename__ = "mj_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    base_url = Column(String(500))
    api_key = Column(Text)
    modes = Column(JSON)  # {"turbo": {"enabled": True, "credits": 10}, ...}
    default_mode = Column(String(50), default="fast")
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
        return {
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "modes": self.modes,
            "default_mode": self.default_mode,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
        }


class MJTask(Base):
    """MJ任务表"""

    __tablename__ = "mj_tasks"

    id = Column(String(50), primary_key=True)  # MJ任务ID
    user_id = Column(String(50), index=True)
    action = Column(String(50))  # IMAGINE, UPSCALE, VARIATION, etc.
    status = Column(String(50), default="SUBMITTED")  # NOT_START, SUBMITTED, etc.
    prompt = Column(Text)
    prompt_en = Column(Text)
    description = Column(Text)
    mode = Column(String(50), default="fast")
    credits_cost = Column(Integer, default=0)

    # 时间字段
    submit_time = Column(DateTime, default=func.now())
    start_time = Column(DateTime)
    finish_time = Column(DateTime)
    progress = Column(String(20), default="0%")

    # 结果字段
    image_url = Column(Text)
    fail_reason = Column(Text)
    properties = Column(JSON)
    buttons = Column(JSON)

    # 关系字段
    parent_task_id = Column(String(50))  # 父任务ID（用于动作任务）

    # 元数据
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 创建索引
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
        Index("idx_status_updated", "status", "updated_at"),
    )

    @classmethod
    def create_task(
        cls,
        id: str,
        user_id: str,
        action: str,
        prompt: str,
        mode: str,
        credits_cost: int,
        mj_response: dict,
        parent_task_id: Optional[str] = None,
    ):
        """创建任务记录"""
        with get_db() as db:
            task = cls(
                id=id,
                user_id=user_id,
                action=action,
                prompt=prompt,
                prompt_en=prompt,  # 可以后续翻译
                description=f"/{action.lower()} {prompt}",
                mode=mode,
                credits_cost=credits_cost,
                parent_task_id=parent_task_id,
                properties=mj_response.get("properties", {}),
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
            db.commit()

    def update_from_mj_response(self, mj_data: dict):
        """从MJ响应更新任务数据 - 修复版本"""
        try:
            with get_db() as db:
                print(f"🔥 【数据库修复版】开始更新任务: {self.id}")

                # 获取图片URL
                new_image_url = mj_data.get("imageUrl", self.image_url)
                new_status = mj_data.get("status", self.status)

                print(
                    f"🔥 【数据库修复版】原始数据: 状态={new_status}, 图片={bool(new_image_url)}"
                )

                # 🔥 核心修复：如果有图片URL，直接强制设置为SUCCESS
                if new_image_url:
                    print(
                        f"🔥 【数据库修复版】发现图片URL，强制完成: {new_image_url[:50]}..."
                    )
                    new_status = "SUCCESS"
                    mj_data = mj_data.copy()  # 避免修改原始数据
                    mj_data["status"] = "SUCCESS"
                    mj_data["progress"] = "100%"

                # 更新字段
                old_status = self.status
                old_progress = self.progress
                old_image_url = self.image_url

                self.status = new_status
                self.image_url = new_image_url
                self.fail_reason = mj_data.get("failReason", self.fail_reason)
                self.properties = mj_data.get("properties", self.properties)
                self.buttons = mj_data.get("buttons", self.buttons)

                # 标准化进度格式
                raw_progress = mj_data.get("progress", self.progress)
                self.progress = self._normalize_progress(raw_progress)

                # 🔥 如果有图片，强制设置为100%
                if new_image_url:
                    self.progress = "100%"

                # 更新时间字段
                if mj_data.get("startTime"):
                    self.start_time = datetime.fromtimestamp(
                        mj_data["startTime"] / 1000
                    )
                if mj_data.get("finishTime"):
                    self.finish_time = datetime.fromtimestamp(
                        mj_data["finishTime"] / 1000
                    )

                # 🔥 如果状态变为SUCCESS，设置完成时间
                if self.status == "SUCCESS" and not self.finish_time:
                    self.finish_time = datetime.utcnow()

                self.updated_at = datetime.utcnow()

                # 🔥 强制提交到数据库
                db.add(self)
                db.commit()
                db.refresh(self)

                print(f"🔥 【数据库修复版】更新完成:")
                print(f"   状态: {old_status} -> {self.status}")
                print(f"   进度: {old_progress} -> {self.progress}")
                print(f"   图片: {bool(old_image_url)} -> {bool(self.image_url)}")

                # 🔥 验证数据库中的实际值
                with get_db() as verify_db:
                    verified_task = (
                        verify_db.query(MJTask).filter(MJTask.id == self.id).first()
                    )
                    if verified_task:
                        print(
                            f"🔥 【数据库修复版】验证成功: 状态={verified_task.status}, 进度={verified_task.progress}, 图片={bool(verified_task.image_url)}"
                        )
                    else:
                        print(f"❌ 【数据库修复版】验证失败: 任务不存在")

        except Exception as e:
            print(f"❌ 【数据库修复版】更新失败: {e}")
            import traceback

            traceback.print_exc()
            raise

    def _normalize_progress(self, progress):
        """标准化进度格式"""
        if not progress:
            return "0%"

        # 如果已经是字符串格式的百分比
        if isinstance(progress, str):
            if "%" in progress:
                return progress
            # 尝试转换为数字
            try:
                num = float(progress)
                return f"{min(max(int(num), 0), 100)}%"
            except (ValueError, TypeError):
                return progress if progress else "0%"

        # 如果是数字
        if isinstance(progress, (int, float)):
            return f"{min(max(int(progress), 0), 100)}%"

        return "0%"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "action": self.action,
            "status": self.status,
            "prompt": self.prompt,
            "promptEn": self.prompt_en,
            "description": self.description,
            "mode": self.mode,
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
            "properties": self.properties or {},
            "buttons": self.buttons or [],
            "creditsCost": self.credits_cost,
            "parentTaskId": self.parent_task_id,
        }


class MJCredit(Base):
    """MJ积分记录表"""

    __tablename__ = "mj_credits"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), index=True)
    amount = Column(Integer)  # 正数为充值，负数为消费
    balance = Column(Integer)  # 操作后余额
    reason = Column(String(200))  # 操作原因
    task_id = Column(String(50))  # 关联任务ID（如果有）
    created_at = Column(DateTime, default=func.now())

    # 创建索引
    __table_args__ = (Index("idx_user_created", "user_id", "created_at"),)

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
