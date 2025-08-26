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


class JimengInpaintingConfig(Base):
    __tablename__ = "jimeng_inpainting_config"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    base_url = Column(String(500), default="https://visual.volcengineapi.com")
    api_key = Column(Text)
    credits_cost = Column(Integer, default=30)  # 涂抹消除功能积分消耗
    edit_credits_cost = Column(Integer, default=40)  # 涂抹编辑功能积分消耗
    default_steps = Column(Integer, default=30)
    default_strength = Column(Float, default=0.8)
    default_scale = Column(Float, default=7.0)
    default_quality = Column(String(10), default="M")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class JimengInpaintingTask(Base):
    __tablename__ = "jimeng_inpainting_tasks"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, index=True)

    # 任务状态
    status = Column(String(50), default="submitted", index=True)
    progress = Column(String(10), default="0%")

    # 功能模式和提示词
    mode = Column(String(20), default="remove", nullable=False)  # 'remove' 或 'edit'
    custom_prompt = Column(Text, nullable=True)  # 涂抹编辑模式的提示词

    # 输入参数
    original_image_url = Column(Text, nullable=False)
    mask_image_url = Column(Text, nullable=False)
    steps = Column(Integer, default=30)
    strength = Column(Float, default=0.8)
    scale = Column(Float, default=7.0)
    seed = Column(Integer, default=0)
    dilate_size = Column(Integer, default=15)
    quality = Column(String(10), default="M")

    # 结果数据
    result_image_url = Column(Text)
    cloud_image_url = Column(Text)  # 云存储URL

    # 任务状态
    credits_cost = Column(Integer, default=30)
    fail_reason = Column(Text)
    properties = Column(JSON)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    finish_time = Column(DateTime)


class JimengInpaintingCredit(Base):
    __tablename__ = "jimeng_inpainting_credits"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, index=True)
    task_id = Column(String(50), nullable=False)
    credit_amount = Column(Integer, nullable=False)
    operation_type = Column(String(20), nullable=False)  # deduct, refund
    created_at = Column(DateTime, default=func.now())


####################
# PYDANTIC MODELS
####################


class JimengInpaintingConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    enabled: bool = False
    base_url: str = "https://visual.volcengineapi.com"
    api_key: str = ""
    credits_cost: int = 30  # 涂抹消除积分
    edit_credits_cost: int = 40  # 涂抹编辑积分
    default_steps: int = 30
    default_strength: float = 0.8
    default_scale: float = 7.0
    default_quality: str = "M"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class JimengInpaintingConfigForm(BaseModel):
    enabled: bool = False
    base_url: str = "https://visual.volcengineapi.com"
    api_key: str = ""
    credits_cost: int = 30  # 涂抹消除积分
    edit_credits_cost: int = 40  # 涂抹编辑积分
    default_steps: int = 30
    default_strength: float = 0.8
    default_scale: float = 7.0
    default_quality: str = "M"


class JimengInpaintingRequestModel(BaseModel):
    original_image_url: str
    mask_image_url: str
    mode: Optional[str] = "remove"  # 'remove' 或 'edit'
    custom_prompt: Optional[str] = None  # 编辑模式的提示词
    steps: Optional[int] = 30
    strength: Optional[float] = 0.8
    scale: Optional[float] = 7.0
    seed: Optional[int] = 0
    dilate_size: Optional[int] = 15
    quality: Optional[str] = "M"
    return_url: Optional[bool] = True


class JimengInpaintingTaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: str
    progress: str = "0%"
    mode: str = "remove"
    custom_prompt: Optional[str] = None
    original_image_url: str
    mask_image_url: str
    steps: int
    strength: float
    scale: float
    seed: int
    dilate_size: int
    quality: str
    result_image_url: Optional[str] = None
    cloud_image_url: Optional[str] = None
    credits_cost: int
    fail_reason: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    finish_time: Optional[datetime] = None


class JimengInpaintingTaskResponse(BaseModel):
    data: List[JimengInpaintingTaskModel]
    total: int
    page: int
    limit: int


####################
# HELPER FUNCTIONS
####################


class JimengInpaintingTable:
    def __init__(self, db=None):
        self.db = db
        self._tables_ensured = False

    def get_config(self) -> Optional[JimengInpaintingConfig]:
        """获取配置"""
        with get_db() as db:
            return db.query(JimengInpaintingConfig).first()

    def upsert_config(
        self, config: JimengInpaintingConfigForm
    ) -> JimengInpaintingConfig:
        """创建或更新配置"""
        with get_db() as db:
            existing_config = db.query(JimengInpaintingConfig).first()

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
                new_config = JimengInpaintingConfig(**config.model_dump())
                db.add(new_config)
                db.commit()
                db.refresh(new_config)
                return new_config

    def get_task_by_id(
        self, task_id: str, user_id: str = None
    ) -> Optional[JimengInpaintingTask]:
        """根据ID获取任务"""
        with get_db() as db:
            query = db.query(JimengInpaintingTask).filter(
                JimengInpaintingTask.id == task_id
            )
            if user_id:
                query = query.filter(JimengInpaintingTask.user_id == user_id)
            return query.first()

    def create_task(self, task_data: dict) -> JimengInpaintingTask:
        """创建任务"""
        with get_db() as db:
            task = JimengInpaintingTask(**task_data)
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    def update_task(
        self, task_id: str, updates: dict
    ) -> Optional[JimengInpaintingTask]:
        """更新任务"""
        with get_db() as db:
            task = (
                db.query(JimengInpaintingTask)
                .filter(JimengInpaintingTask.id == task_id)
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
                db.query(JimengInpaintingTask)
                .filter(JimengInpaintingTask.user_id == user_id)
                .count()
            )

            # 获取任务列表
            tasks = (
                db.query(JimengInpaintingTask)
                .filter(JimengInpaintingTask.user_id == user_id)
                .order_by(JimengInpaintingTask.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return tasks, total

    def delete_task(self, task_id: str, user_id: str) -> bool:
        """删除任务"""
        with get_db() as db:
            task = (
                db.query(JimengInpaintingTask)
                .filter(
                    JimengInpaintingTask.id == task_id,
                    JimengInpaintingTask.user_id == user_id,
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
            credit_record = JimengInpaintingCredit(
                user_id=user_id,
                task_id=task_id,
                credit_amount=amount,
                operation_type=operation_type,
            )
            db.add(credit_record)
            db.commit()
            return credit_record


# 全局实例
JimengInpaintingConfigs = JimengInpaintingTable()
JimengInpaintingTasks = JimengInpaintingTable()
JimengInpaintingCredits = JimengInpaintingTable()
