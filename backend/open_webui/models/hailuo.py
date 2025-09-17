"""
海螺（MiniMax Hailuo）视频生成数据模型
包含配置与任务管理
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from open_webui.internal.db import Base, get_db


class HailuoConfig(Base):
    __tablename__ = "hailuo_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False, nullable=False)
    base_url = Column(String(500), default="https://api.minimaxi.com", nullable=False)
    api_key = Column(Text, nullable=True)

    # 默认参数
    default_model = Column(String(64), default="MiniMax-Hailuo-02", nullable=False)
    default_duration = Column(Integer, default=6, nullable=False)  # seconds: 6/10
    default_resolution = Column(
        String(16), default="768P", nullable=False
    )  # 768P/1080P
    prompt_optimizer = Column(Boolean, default=True, nullable=False)

    # 计费配置：{ model: { resolution: { duration: credits } }, first_last_multiplier: 1.0 }
    model_credits_config = Column(JSON, nullable=True)

    # 并发/轮询
    max_concurrent_tasks = Column(Integer, default=3, nullable=False)
    task_timeout_ms = Column(Integer, default=900000, nullable=False)  # 15min
    query_interval_ms = Column(Integer, default=10000, nullable=False)  # 10s

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())

    @classmethod
    def get_config(cls):
        with get_db() as db:
            return db.query(cls).filter(cls.id == 1).first()

    @classmethod
    def save_config(cls, data: dict):
        with get_db() as db:
            cfg = db.query(cls).filter(cls.id == 1).first()
            if cfg:
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
                cfg.updated_at = datetime.now()
            else:
                data["id"] = 1
                cfg = cls(**data)
                db.add(cfg)
            db.commit()
            db.refresh(cfg)
            return cfg

    def get_default_credits_config(self) -> dict:
        # 粗略默认值，可在面板自定义
        return {
            "first_last_multiplier": 1.3,
            "MiniMax-Hailuo-02": {"768P": {"6": 80, "10": 120}, "1080P": {"6": 120}},
            "I2V-01-Director": {"768P": {"6": 70, "10": 110}},
            "I2V-01-live": {"768P": {"6": 60, "10": 100}},
            "I2V-01": {"768P": {"6": 60, "10": 100}},
        }

    def get_credits_cost(
        self, model: str, resolution: str, duration: int, first_last: bool = False
    ) -> int:
        cfg = self.model_credits_config or self.get_default_credits_config()
        multiplier = float(cfg.get("first_last_multiplier", 1.3)) if first_last else 1.0
        try:
            base = int(cfg[model][resolution][str(duration)])
        except Exception:
            # 回退默认
            base = 100
        return int(round(base * multiplier))


class HailuoTask(Base):
    __tablename__ = "hailuo_tasks"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)

    # 输入
    prompt = Column(Text, nullable=False)
    model = Column(String(64), nullable=False)
    duration = Column(Integer, nullable=False)
    resolution = Column(String(16), nullable=False)
    prompt_optimizer = Column(Boolean, default=True, nullable=False)
    first_frame_url = Column(Text, nullable=True)
    last_frame_url = Column(Text, nullable=True)
    cloud_input_images = Column(JSON, nullable=True)

    # 状态
    status = Column(String(20), default="submitted", nullable=False)
    progress = Column(String(10), default="0%", nullable=True)
    external_task_id = Column(String(100), nullable=True)
    file_id = Column(String(100), nullable=True)
    fail_reason = Column(Text, nullable=True)

    # 结果
    result_video_url = Column(Text, nullable=True)
    cloud_video_url = Column(Text, nullable=True)
    credits_cost = Column(Integer, nullable=True)
    properties = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, nullable=True)
    finish_time = Column(DateTime, nullable=True)

    @classmethod
    def create_task(cls, data: dict):
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        with get_db() as db:
            t = cls(**data)
            db.add(t)
            db.commit()
            db.refresh(t)
            return t

    @classmethod
    def get_task_by_id(cls, task_id: str):
        with get_db() as db:
            return db.query(cls).filter(cls.id == task_id).first()

    @classmethod
    def update_task_status(cls, task_id: str, updates: dict):
        with get_db() as db:
            t = db.query(cls).filter(cls.id == task_id).first()
            if not t:
                return None
            for k, v in updates.items():
                if hasattr(t, k):
                    setattr(t, k, v)
            t.updated_at = datetime.now()
            if updates.get("status") in ("succeed", "failed", "timeout"):
                t.finish_time = datetime.now()
            db.commit()
            db.refresh(t)
            return t

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "prompt": self.prompt,
            "model": self.model,
            "duration": self.duration,
            "resolution": self.resolution,
            "prompt_optimizer": self.prompt_optimizer,
            "first_frame_url": self.first_frame_url,
            "last_frame_url": self.last_frame_url,
            "cloud_input_images": self.cloud_input_images,
            "status": self.status,
            "progress": self.progress,
            "external_task_id": self.external_task_id,
            "file_id": self.file_id,
            "result_video_url": self.result_video_url,
            "cloud_video_url": self.cloud_video_url,
            "credits_cost": self.credits_cost,
            "fail_reason": self.fail_reason,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "finish_time": self.finish_time.isoformat() if self.finish_time else None,
        }


# Pydantic 表单
class HailuoConfigForm(BaseModel):
    enabled: bool = False
    base_url: Optional[str] = "https://api.minimaxi.com"
    api_key: Optional[str] = None
    default_model: str = "MiniMax-Hailuo-02"
    default_duration: int = 6
    default_resolution: str = "768P"
    prompt_optimizer: bool = True
    max_concurrent_tasks: int = 3
    task_timeout_ms: int = 900000
    query_interval_ms: int = 10000
    model_credits_config: Optional[Dict[str, Any]] = None


class HailuoGenerateRequest(BaseModel):
    model: Optional[str] = Field("MiniMax-Hailuo-02")
    prompt: str
    duration: Optional[int] = Field(6)
    resolution: Optional[str] = Field("768P")
    prompt_optimizer: Optional[bool] = True
    # 图生 / 首尾
    first_frame_image: Optional[str] = None  # URL 或 data URL
    last_frame_image: Optional[str] = None  # URL 或 data URL
    external_task_id: Optional[str] = None
    callback_url: Optional[str] = None
