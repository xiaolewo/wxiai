from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.sql import func
from open_webui.internal.db import Base, get_db
import uuid
import json
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

####################
# DB MODEL
####################


class KlingLipSyncConfig(Base):
    __tablename__ = "kling_lip_sync_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    base_url = Column(String(500), default="https://api.kling.com")
    api_key = Column(Text)
    default_voice_id = Column(String(50), default="genshin_vindi2")
    default_voice_language = Column(String(10), default="zh")
    default_voice_speed = Column(Float, default=1.0)
    credits_cost = Column(Integer, default=50)  # 每次对口型消耗的积分
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class KlingLipSyncTask(Base):
    __tablename__ = "kling_lip_sync_tasks"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, index=True)

    # 任务状态
    status = Column(String(50), default="submitted", index=True)
    task_status_msg = Column(Text)

    # 输入参数
    mode = Column(String(20), nullable=False)  # text2video, audio2video
    video_input = Column(Text, nullable=False)  # video_id 或 video_url
    input_type = Column(String(20), nullable=False)  # video_id, video_url

    # 文本转视频参数
    text = Column(Text)
    voice_id = Column(String(50))
    voice_language = Column(String(10))
    voice_speed = Column(Float)

    # 音频转视频参数
    audio_file = Column(Text)  # base64 或 URL
    audio_type = Column(String(10))  # file, url

    # 结果
    video_url = Column(Text)
    video_duration = Column(String(10))
    fail_reason = Column(Text)

    # 任务管理
    credits_cost = Column(Integer, default=50)
    submit_time = Column(DateTime, default=func.now())
    finish_time = Column(DateTime)
    progress = Column(String(10), default="0%")

    # 元数据
    properties = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class KlingLipSyncCredit(Base):
    __tablename__ = "kling_lip_sync_credits"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, index=True)
    task_id = Column(String(50), nullable=False)
    credit_amount = Column(Integer, nullable=False)
    operation_type = Column(String(20), nullable=False)  # deduct, refund
    created_at = Column(DateTime, default=func.now())


####################
# PYDANTIC MODELS
####################


class KlingLipSyncConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    enabled: bool = False
    base_url: str = "https://api.kling.com"
    api_key: str = ""
    default_voice_id: str = "genshin_vindi2"
    default_voice_language: str = "zh"
    default_voice_speed: float = 1.0
    credits_cost: int = 50
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class KlingLipSyncConfigForm(BaseModel):
    enabled: bool = False
    base_url: str = "https://api.kling.com"
    api_key: str = ""
    default_voice_id: str = "genshin_vindi2"
    default_voice_language: str = "zh"
    default_voice_speed: float = 1.0
    credits_cost: int = 50


class KlingLipSyncRequestModel(BaseModel):
    mode: str  # text2video, audio2video
    video_input: str  # video_id, video_url
    input_type: str  # video_id, video_url

    # 文本转视频参数
    text: Optional[str] = None
    voice_id: Optional[str] = None
    voice_language: Optional[str] = "zh"
    voice_speed: Optional[float] = 1.0

    # 音频转视频参数
    audio_file: Optional[str] = None  # base64数据
    audio_url: Optional[str] = None
    audio_type: Optional[str] = "file"

    callback_url: Optional[str] = None


class KlingLipSyncTaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: str
    task_status_msg: Optional[str] = None
    mode: str
    video_input: str
    input_type: str
    text: Optional[str] = None
    voice_id: Optional[str] = None
    voice_language: Optional[str] = None
    voice_speed: Optional[float] = None
    audio_file: Optional[str] = None
    audio_type: Optional[str] = None
    video_url: Optional[str] = None
    video_duration: Optional[str] = None
    fail_reason: Optional[str] = None
    credits_cost: int
    submit_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    progress: str = "0%"
    properties: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class KlingLipSyncTaskResponse(BaseModel):
    data: List[KlingLipSyncTaskModel]
    total: int
    page: int
    limit: int


####################
# HELPER FUNCTIONS
####################


class KlingLipSyncTable:
    def __init__(self, db=None):
        self.db = db

    def get_config(self) -> Optional[KlingLipSyncConfig]:
        """获取配置"""
        with get_db() as db:
            return db.query(KlingLipSyncConfig).first()

    def upsert_config(self, config: KlingLipSyncConfigForm) -> KlingLipSyncConfig:
        """创建或更新配置"""
        with get_db() as db:
            existing_config = db.query(KlingLipSyncConfig).first()

            if existing_config:
                # 更新现有配置
                for key, value in config.model_dump().items():
                    setattr(existing_config, key, value)
                existing_config.updated_at = func.now()
                db.commit()
                db.refresh(existing_config)
                return existing_config
            else:
                # 创建新配置
                new_config = KlingLipSyncConfig(**config.model_dump())
                db.add(new_config)
                db.commit()
                db.refresh(new_config)
                return new_config

    def get_task_by_id(
        self, task_id: str, user_id: str = None
    ) -> Optional[KlingLipSyncTask]:
        """根据ID获取任务"""
        with get_db() as db:
            query = db.query(KlingLipSyncTask).filter(KlingLipSyncTask.id == task_id)
            if user_id:
                query = query.filter(KlingLipSyncTask.user_id == user_id)
            return query.first()

    def create_task(self, task_data: dict) -> KlingLipSyncTask:
        """创建任务"""
        with get_db() as db:
            task = KlingLipSyncTask(**task_data)
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    def update_task(self, task_id: str, updates: dict) -> Optional[KlingLipSyncTask]:
        """更新任务"""
        with get_db() as db:
            task = (
                db.query(KlingLipSyncTask)
                .filter(KlingLipSyncTask.id == task_id)
                .first()
            )
            if task:
                for key, value in updates.items():
                    setattr(task, key, value)
                task.updated_at = func.now()
                db.commit()
                db.refresh(task)
                return task
            return None

    def get_user_tasks(self, user_id: str, page: int = 1, limit: int = 20) -> tuple:
        """获取用户任务列表"""
        with get_db() as db:
            offset = (page - 1) * limit

            # 获取总数
            total = (
                db.query(KlingLipSyncTask)
                .filter(KlingLipSyncTask.user_id == user_id)
                .count()
            )

            # 获取任务列表
            tasks = (
                db.query(KlingLipSyncTask)
                .filter(KlingLipSyncTask.user_id == user_id)
                .order_by(KlingLipSyncTask.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return tasks, total

    def delete_task(self, task_id: str, user_id: str) -> bool:
        """删除任务"""
        with get_db() as db:
            task = (
                db.query(KlingLipSyncTask)
                .filter(
                    KlingLipSyncTask.id == task_id, KlingLipSyncTask.user_id == user_id
                )
                .first()
            )
            if task:
                db.delete(task)
                db.commit()
                return True
            return False

    def create_credit_record(
        self, user_id: str, task_id: str, amount: int, operation_type: str
    ):
        """创建积分记录"""
        with get_db() as db:
            credit_record = KlingLipSyncCredit(
                user_id=user_id,
                task_id=task_id,
                credit_amount=amount,
                operation_type=operation_type,
            )
            db.add(credit_record)
            db.commit()
            return credit_record


# 全局实例
KlingLipSyncConfigs = KlingLipSyncTable()
KlingLipSyncTasks = KlingLipSyncTable()
KlingLipSyncCredits = KlingLipSyncTable()
