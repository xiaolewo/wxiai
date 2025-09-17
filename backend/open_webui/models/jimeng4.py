"""Jimeng4 image generation models"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.sql import func

from open_webui.internal.db import Base, get_db


class Jimeng4ConfigForm(BaseModel):
    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    default_model: str = "doubao-seedream-4-0-250828"
    default_size: str = "2K"
    default_watermark: bool = True
    default_sequential_mode: str = "auto"
    default_n: int = 1
    credits_per_image: int = 30
    max_concurrent_tasks: int = 5
    task_timeout: int = 5 * 60 * 1000  # milliseconds

    @field_validator("default_n")
    @classmethod
    def validate_default_n(cls, value: int) -> int:
        if value < 1 or value > 10:
            raise ValueError("n must be between 1 and 10")
        return value


class Jimeng4UploadResponse(BaseModel):
    success: bool
    message: str
    url: Optional[str] = None
    file_id: Optional[str] = None


class Jimeng4GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    image: Optional[List[str]] = None
    n: Optional[int] = None
    sequential_image_generation: Optional[str] = None
    response_format: Optional[str] = "url"
    size: Optional[str] = None
    stream: Optional[bool] = False
    watermark: Optional[bool] = None

    @field_validator("image")
    @classmethod
    def validate_images(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value:
            return [url for url in value if url]
        return value

    @field_validator("n")
    @classmethod
    def validate_n(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and (value < 1 or value > 10):
            raise ValueError("n must be between 1 and 10")
        return value


class Jimeng4Config(Base):
    __tablename__ = "jimeng4_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False, nullable=False)
    base_url = Column(String(500), nullable=False, default="")
    api_key = Column(Text, nullable=False, default="")
    default_model = Column(String(200), nullable=False)
    default_size = Column(String(50), nullable=False)
    default_watermark = Column(Boolean, nullable=False, default=True)
    default_sequential_mode = Column(String(50), nullable=False, default="auto")
    default_n = Column(Integer, nullable=False, default=1)
    credits_per_image = Column(Integer, nullable=False, default=30)
    max_concurrent_tasks = Column(Integer, nullable=False, default=5)
    task_timeout = Column(Integer, nullable=False, default=300000)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    @classmethod
    def get_config(cls) -> Optional["Jimeng4Config"]:
        with get_db() as db:
            return db.query(cls).first()

    @classmethod
    def save_config(cls, config_data: Dict[str, Any]) -> "Jimeng4Config":
        with get_db() as db:
            existing = db.query(cls).first()
            if existing:
                for key, value in config_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                return existing

            config = cls(**config_data)
            db.add(config)
            db.commit()
            db.refresh(config)
            return config

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "default_model": self.default_model,
            "default_size": self.default_size,
            "default_watermark": self.default_watermark,
            "default_sequential_mode": self.default_sequential_mode,
            "default_n": self.default_n,
            "credits_per_image": self.credits_per_image,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
        }


class Jimeng4Task(Base):
    __tablename__ = "jimeng4_tasks"

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="submitted", index=True)
    prompt = Column(Text, nullable=False)
    model = Column(String(200), nullable=False)
    size = Column(String(50), nullable=False)
    sequential_mode = Column(String(50), nullable=True)
    n = Column(Integer, nullable=False, default=1)
    request_image_urls = Column(JSON, nullable=True)
    response_format = Column(String(50), nullable=True)
    stream = Column(Boolean, nullable=False, default=False)
    watermark = Column(Boolean, nullable=False, default=True)
    response_urls = Column(JSON, nullable=True)
    cloud_image_urls = Column(JSON, nullable=True)
    stream_events = Column(JSON, nullable=True)
    raw_stream = Column(Text, nullable=True)
    fail_reason = Column(Text, nullable=True)
    usage = Column(JSON, nullable=True)
    credits_cost = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("idx_jimeng4_tasks_user_created", "user_id", "created_at"),)

    @classmethod
    def create_task(
        cls,
        user_id: str,
        prompt: str,
        model: str,
        size: str,
        sequential_mode: Optional[str],
        n: int,
        request_image_urls: Optional[List[str]],
        response_format: Optional[str],
        stream: bool,
        watermark: bool,
        credits_cost: int,
    ) -> "Jimeng4Task":
        with get_db() as db:
            task = cls(
                user_id=user_id,
                prompt=prompt,
                model=model,
                size=size,
                sequential_mode=sequential_mode,
                n=n,
                request_image_urls=request_image_urls,
                response_format=response_format,
                stream=stream,
                watermark=watermark,
                credits_cost=credits_cost,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    @classmethod
    def get_task(cls, task_id: str) -> Optional["Jimeng4Task"]:
        with get_db() as db:
            return db.query(cls).filter(cls.id == task_id).first()

    @classmethod
    def list_tasks(
        cls, user_id: str, limit: int = 20, offset: int = 0
    ) -> List["Jimeng4Task"]:
        with get_db() as db:
            return (
                db.query(cls)
                .filter(cls.user_id == user_id)
                .order_by(cls.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

    @classmethod
    def update_task(
        cls,
        task_id: str,
        **updates: Any,
    ) -> Optional["Jimeng4Task"]:
        with get_db() as db:
            task = db.query(cls).filter(cls.id == task_id).first()
            if not task:
                return None
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
            return task

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "prompt": self.prompt,
            "model": self.model,
            "size": self.size,
            "sequential_mode": self.sequential_mode,
            "n": self.n,
            "request_image_urls": self.request_image_urls,
            "response_format": self.response_format,
            "stream": self.stream,
            "watermark": self.watermark,
            "response_urls": self.response_urls,
            "cloud_image_urls": self.cloud_image_urls,
            "fail_reason": self.fail_reason,
            "usage": self.usage,
            "credits_cost": self.credits_cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }
