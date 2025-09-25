"""Seedance (新即梦) 视频生成数据模型"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from open_webui.internal.db import Base, get_db


class SeedanceConfig(Base):
    """Seedance 视频服务配置"""

    __tablename__ = "seedance_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False)
    base_url = Column(String(500), default="https://ark.cn-beijing.volces.com")
    api_key = Column(Text)

    # 默认参数
    default_model = Column(String(100), default="doubao-seedance-1-0-pro-250528")
    default_duration = Column(String(10), default="5")
    default_resolution = Column(String(20), default="720p")
    default_ratio = Column(String(20), default="16:9")
    default_watermark = Column(Boolean, default=False)
    default_camera_fixed = Column(Boolean, default=False)
    default_return_last_frame = Column(Boolean, default=False)

    # 积分及任务配置
    credits_per_5s = Column(Integer, default=40)
    credits_per_10s = Column(Integer, default=80)
    max_concurrent_tasks = Column(Integer, default=5)
    task_timeout = Column(Integer, default=600_000)
    query_interval = Column(Integer, default=10_000)

    # 可扩展的模型积分映射
    model_credits_config = Column(JSON)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def get_config(cls) -> Optional["SeedanceConfig"]:
        with get_db() as db:
            return db.query(cls).filter(cls.id == 1).first()

    @classmethod
    def save_config(cls, data: Dict[str, Any]) -> "SeedanceConfig":
        with get_db() as db:
            config = db.query(cls).filter(cls.id == 1).first()
            if config:
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                config.updated_at = datetime.now()
            else:
                data.setdefault("id", 1)
                config = cls(**data)
                db.add(config)
            db.commit()
            db.refresh(config)
            return config

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "default_model": self.default_model,
            "default_duration": self.default_duration,
            "default_resolution": self.default_resolution,
            "default_ratio": self.default_ratio,
            "default_watermark": self.default_watermark,
            "default_camera_fixed": self.default_camera_fixed,
            "default_return_last_frame": self.default_return_last_frame,
            "credits_per_5s": self.credits_per_5s,
            "credits_per_10s": self.credits_per_10s,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
            "query_interval": self.query_interval,
            "model_credits_config": self.model_credits_config or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_credits_cost(self, duration: str) -> int:
        duration = str(duration or self.default_duration or "5")
        duration = duration.strip()
        if duration == "10":
            return self.credits_per_10s or self.credits_per_5s
        return self.credits_per_5s or 0


class SeedanceTask(Base):
    """Seedance 任务记录"""

    __tablename__ = "seedance_tasks"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, index=True)
    external_task_id = Column(String(100), index=True)

    action = Column(
        String(50), nullable=False
    )  # TEXT_TO_VIDEO, IMAGE_TO_VIDEO, IMAGE_TO_VIDEO_FIRST_LAST
    status = Column(String(50), default="submitted", index=True)
    task_status_msg = Column(Text)

    # 请求参数
    prompt = Column(Text)
    model = Column(String(100))
    duration = Column(String(10))
    resolution = Column(String(20))
    ratio = Column(String(20))
    watermark = Column(Boolean)
    seed = Column(Integer)
    camera_fixed = Column(Boolean)
    return_last_frame = Column(Boolean)
    images = Column(JSON)  # 保存生成时使用的图片信息（URL 列表）

    # 任务管理
    credits_cost = Column(Integer, default=0)
    submit_time = Column(DateTime)
    start_time = Column(DateTime)
    finish_time = Column(DateTime)

    # 结果数据
    video_url = Column(Text)
    cloud_video_url = Column(Text)
    last_frame_url = Column(Text)
    cloud_last_frame_url = Column(Text)
    progress = Column(String(20), default="0%")
    fail_reason = Column(Text)

    # 原始请求/响应
    request_data = Column(Text)
    response_data = Column(Text)

    properties = Column(JSON)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def create_task(
        cls,
        user_id: str,
        action: str,
        prompt: str,
        model: Optional[str],
        duration: Optional[str],
        resolution: Optional[str],
        ratio: Optional[str],
        watermark: Optional[bool],
        seed: Optional[int],
        camera_fixed: Optional[bool],
        return_last_frame: Optional[bool],
        images: Optional[List[str]],
        credits_cost: int,
        request_data: Dict[str, Any],
        properties: Optional[Dict[str, Any]] = None,
    ) -> "SeedanceTask":
        with get_db() as db:
            task = cls(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                status="submitted",
                prompt=prompt,
                model=model,
                duration=duration,
                resolution=resolution,
                ratio=ratio,
                watermark=watermark,
                seed=seed,
                camera_fixed=camera_fixed,
                return_last_frame=return_last_frame,
                images=images,
                credits_cost=credits_cost,
                submit_time=datetime.utcnow(),
                request_data=json.dumps(request_data, ensure_ascii=False),
                properties=properties or {"serviceType": "seedance", "action": action},
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    @classmethod
    def get_task_by_id(cls, task_id: str) -> Optional["SeedanceTask"]:
        with get_db() as db:
            return db.query(cls).filter(cls.id == task_id).first()

    @classmethod
    def get_user_tasks(
        cls, user_id: str, page: int, limit: int
    ) -> tuple[List["SeedanceTask"], int]:
        page = max(page, 1)
        limit = min(max(limit, 1), 100)
        offset = (page - 1) * limit
        with get_db() as db:
            query = db.query(cls).filter(cls.user_id == user_id)
            total = query.count()
            tasks = (
                query.order_by(cls.created_at.desc()).offset(offset).limit(limit).all()
            )
            return tasks, total

    def update_status(self, status: str, fail_reason: Optional[str] = None):
        with get_db() as db:
            task = db.query(SeedanceTask).filter(SeedanceTask.id == self.id).first()
            if not task:
                return
            task.status = status
            if fail_reason:
                task.fail_reason = fail_reason
            task.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
            self.status = task.status
            self.fail_reason = task.fail_reason
            self.updated_at = task.updated_at

    def update_from_api_response(self, response: Dict[str, Any]):
        if not response:
            return

        status_map = {
            "NOT_START": "submitted",
            "IN_PROGRESS": "processing",
            "SUCCESS": "succeed",
            "FAILURE": "failed",
        }

        data = response.get("data", {})
        status = response.get("status")
        mapped_status = status_map.get(status, self.status)
        progress = data.get("progress") or response.get("progress")
        video_url = data.get("output") or data.get("video_url")
        last_frame_url = data.get("last_frame_url")
        fail_reason = response.get("fail_reason")

        with get_db() as db:
            task = db.query(SeedanceTask).filter(SeedanceTask.id == self.id).first()
            if not task:
                return

            task.status = mapped_status
            task.progress = progress or task.progress
            task.video_url = video_url or task.video_url
            task.last_frame_url = last_frame_url or task.last_frame_url
            task.fail_reason = fail_reason or task.fail_reason
            task.external_task_id = response.get("task_id") or task.external_task_id
            task.response_data = json.dumps(response, ensure_ascii=False)
            if mapped_status in ("succeed", "failed"):
                task.finish_time = datetime.utcnow()
            if mapped_status == "processing" and not task.start_time:
                task.start_time = datetime.utcnow()
            task.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(task)

            # 同步当前实例
            self.status = task.status
            self.progress = task.progress
            self.video_url = task.video_url
            self.last_frame_url = task.last_frame_url
            self.fail_reason = task.fail_reason
            self.external_task_id = task.external_task_id
            self.response_data = task.response_data
            self.finish_time = task.finish_time
            self.start_time = task.start_time
            self.updated_at = task.updated_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "externalTaskId": self.external_task_id,
            "serviceType": "seedance",
            "action": self.action,
            "status": self.status,
            "taskStatusMsg": self.task_status_msg,
            "prompt": self.prompt,
            "model": self.model,
            "duration": self.duration,
            "resolution": self.resolution,
            "ratio": self.ratio,
            "watermark": self.watermark,
            "seed": self.seed,
            "cameraFixed": self.camera_fixed,
            "returnLastFrame": self.return_last_frame,
            "imageUrls": self.images,
            "creditsCost": self.credits_cost,
            "submitTime": self.submit_time.isoformat() if self.submit_time else None,
            "startTime": self.start_time.isoformat() if self.start_time else None,
            "finishTime": self.finish_time.isoformat() if self.finish_time else None,
            "videoUrl": self.cloud_video_url or self.video_url,
            "rawVideoUrl": self.video_url,
            "cloudVideoUrl": self.cloud_video_url,
            "lastFrameUrl": self.cloud_last_frame_url or self.last_frame_url,
            "cloudLastFrameUrl": self.cloud_last_frame_url,
            "progress": self.progress,
            "failReason": self.fail_reason,
            "properties": self.properties,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class SeedanceConfigForm(BaseModel):
    enabled: bool = False
    base_url: str = "https://ark.cn-beijing.volces.com"
    api_key: str = ""
    default_model: str = "doubao-seedance-1-0-pro-250528"
    default_duration: str = "5"
    default_resolution: str = "720p"
    default_ratio: str = "16:9"
    default_watermark: bool = False
    default_camera_fixed: bool = False
    default_return_last_frame: bool = False
    credits_per_5s: int = 40
    credits_per_10s: int = 80
    max_concurrent_tasks: int = 5
    task_timeout: int = 600_000
    query_interval: int = 10_000
    model_credits_config: Optional[Dict[str, Any]] = None


class SeedanceGenerateRequestModel(BaseModel):
    mode: str = Field(
        ..., description="text_to_video / image_to_video / image_to_video_first_last"
    )
    prompt: Optional[str] = None
    model: str
    duration: Optional[str] = None
    resolution: Optional[str] = None
    ratio: Optional[str] = None
    watermark: Optional[bool] = None
    seed: Optional[int] = None
    camera_fixed: Optional[bool] = None
    return_last_frame: Optional[bool] = None
    images: Optional[List[str]] = Field(default=None, description="Base64 图片列表")


class SeedanceTaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    serviceType: str = "seedance"
    action: str
    status: str
    prompt: Optional[str] = None
    model: Optional[str] = None
    duration: Optional[str] = None
    resolution: Optional[str] = None
    ratio: Optional[str] = None
    watermark: Optional[bool] = None
    seed: Optional[int] = None
    camera_fixed: Optional[bool] = None
    return_last_frame: Optional[bool] = None
    image_urls: Optional[List[str]] = None
    credits_cost: Optional[int] = None
    submit_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    video_url: Optional[str] = None
    cloud_video_url: Optional[str] = None
    last_frame_url: Optional[str] = None
    cloud_last_frame_url: Optional[str] = None
    progress: Optional[str] = None
    fail_reason: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SeedanceTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data: List[SeedanceTaskModel]
    total: int
    page: int
    limit: int


class SeedanceCreditsResponse(BaseModel):
    balance: float
