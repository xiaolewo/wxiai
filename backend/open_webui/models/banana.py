"""Banana image generation models"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.sql import func

from open_webui.internal.db import Base, get_db


class BananaConfigForm(BaseModel):
    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    default_model: str = "nano-banana"
    default_output_format: str = "url"
    default_aspect_ratio: str = "1:1"
    credits_per_generation: int = 10
    credits_per_edit: int = 10
    max_concurrent_tasks: int = 5
    task_timeout: int = 5 * 60 * 1000

    @field_validator("default_output_format")
    @classmethod
    def validate_output_format(cls, value: str) -> str:
        if value not in {"url", "b64_json"}:
            raise ValueError("default_output_format must be 'url' or 'b64_json'")
        return value

    @field_validator("default_aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, value: str) -> str:
        allowed = {"4:3", "3:4", "16:9", "9:16", "2:3", "3:2", "1:1", "21:9"}
        if value not in allowed:
            raise ValueError("Unsupported aspect ratio")
        return value


class BananaConfig(Base):
    __tablename__ = "banana_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, nullable=False, default=False)
    base_url = Column(String(500), nullable=False, default="")
    api_key = Column(Text, nullable=False, default="")
    default_model = Column(String(200), nullable=False)
    default_output_format = Column(String(50), nullable=False, default="url")
    default_aspect_ratio = Column(String(20), nullable=False, default="1:1")
    credits_per_generation = Column(Integer, nullable=False, default=10)
    credits_per_edit = Column(Integer, nullable=False, default=10)
    max_concurrent_tasks = Column(Integer, nullable=False, default=5)
    task_timeout = Column(Integer, nullable=False, default=300000)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    @classmethod
    def get_config(cls) -> Optional["BananaConfig"]:
        with get_db() as db:
            return db.query(cls).first()

    @classmethod
    def save_config(cls, config_data: Dict[str, Any]) -> "BananaConfig":
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
            "default_output_format": self.default_output_format,
            "default_aspect_ratio": self.default_aspect_ratio,
            "credits_per_generation": self.credits_per_generation,
            "credits_per_edit": self.credits_per_edit,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
        }


class BananaTask(Base):
    __tablename__ = "banana_tasks"

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(64), nullable=False, index=True)
    task_type = Column(String(32), nullable=False)  # generation or edit
    prompt = Column(Text, nullable=False)
    model = Column(String(200), nullable=False)
    aspect_ratio = Column(String(20), nullable=True)
    response_format = Column(String(20), nullable=False, default="url")
    request_image_urls = Column(JSON, nullable=True)
    response_urls = Column(JSON, nullable=True)
    cloud_image_urls = Column(JSON, nullable=True)
    fail_reason = Column(Text, nullable=True)
    usage = Column(JSON, nullable=True)
    credits_cost = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="submitted", index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("idx_banana_tasks_user_created", "user_id", "created_at"),)

    @classmethod
    def create_task(
        cls,
        user_id: str,
        task_type: str,
        prompt: str,
        model: str,
        aspect_ratio: Optional[str],
        response_format: str,
        request_image_urls: Optional[List[str]],
        credits_cost: int,
    ) -> "BananaTask":
        with get_db() as db:
            task = cls(
                user_id=user_id,
                task_type=task_type,
                prompt=prompt,
                model=model,
                aspect_ratio=aspect_ratio,
                response_format=response_format,
                request_image_urls=request_image_urls,
                credits_cost=credits_cost,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    @classmethod
    def get_task(cls, task_id: str) -> Optional["BananaTask"]:
        with get_db() as db:
            return db.query(cls).filter(cls.id == task_id).first()

    @classmethod
    def list_tasks(
        cls, user_id: str, limit: int = 20, offset: int = 0
    ) -> List["BananaTask"]:
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
    def update_task(cls, task_id: str, **updates: Any) -> Optional["BananaTask"]:
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
            "task_type": self.task_type,
            "prompt": self.prompt,
            "model": self.model,
            "aspect_ratio": self.aspect_ratio,
            "response_format": self.response_format,
            "request_image_urls": self.request_image_urls,
            "response_urls": self.response_urls,
            "cloud_image_urls": self.cloud_image_urls,
            "status": self.status,
            "fail_reason": self.fail_reason,
            "usage": self.usage,
            "credits_cost": self.credits_cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }
