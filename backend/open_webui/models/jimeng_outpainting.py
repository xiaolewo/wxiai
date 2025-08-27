from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float
from sqlalchemy.sql import func
from open_webui.internal.db import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JimengOutpaintingConfig(Base):
    """即梦智能扩图配置表"""

    __tablename__ = "jimeng_outpainting_config"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=False, nullable=False)
    base_url = Column(String(255), default="https://visual.volcengineapi.com")
    api_key = Column(Text)
    credits_cost = Column(Integer, default=25, nullable=False)  # 默认积分消耗

    # 默认参数
    default_steps = Column(Integer, default=30, nullable=False)
    default_strength = Column(Float, default=0.8, nullable=False)
    default_scale = Column(Float, default=7.0, nullable=False)
    default_quality = Column(String(10), default="M", nullable=False)
    default_max_width = Column(Integer, default=1920, nullable=False)
    default_max_height = Column(Integer, default=1920, nullable=False)

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class JimengOutpaintingTask(Base):
    """即梦智能扩图任务表"""

    __tablename__ = "jimeng_outpainting_tasks"

    id = Column(String(50), primary_key=True, index=True)  # 任务ID
    user_id = Column(String(50), nullable=False, index=True)

    # 输入参数
    original_image_url = Column(Text, nullable=False)  # 原始图片URL
    mask_image_url = Column(Text)  # 遮罩图片URL (画布模式使用)
    expansion_mode = Column(
        String(20), default="equal", nullable=False
    )  # equal/aspect/custom/canvas
    custom_prompt = Column(Text)  # 用户提示词

    # 扩展参数
    top = Column(Float, default=0.1)  # 向上扩展比例
    bottom = Column(Float, default=0.1)  # 向下扩展比例
    left = Column(Float, default=0.1)  # 向左扩展比例
    right = Column(Float, default=0.1)  # 向右扩展比例

    # 生成参数
    steps = Column(Integer, default=30)
    strength = Column(Float, default=0.8)
    scale = Column(Float, default=7.0)
    seed = Column(Integer, default=0)
    quality = Column(String(10), default="M")
    max_width = Column(Integer, default=1920)
    max_height = Column(Integer, default=1920)

    # 任务状态
    status = Column(
        String(20), default="submitted", nullable=False
    )  # submitted/processing/succeed/failed
    progress = Column(String(10), default="0%")
    fail_reason = Column(Text)

    # 结果
    result_image_url = Column(Text)  # 处理结果图片URL
    cloud_image_url = Column(Text)  # 云端图片URL
    request_id = Column(String(100))  # 请求ID

    # 积分消耗
    credits_cost = Column(Integer, default=25)

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class JimengOutpaintingCredit(Base):
    """即梦智能扩图积分记录表"""

    __tablename__ = "jimeng_outpainting_credits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    task_id = Column(String(50), nullable=False)

    # 积分变化
    credits_used = Column(Integer, nullable=False)
    credits_before = Column(Integer, nullable=False)
    credits_after = Column(Integer, nullable=False)

    # 操作信息
    operation_type = Column(String(20), default="outpainting", nullable=False)
    description = Column(Text)

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())


# Pydantic Models for API


class JimengOutpaintingConfigModel(BaseModel):
    enabled: bool = False
    base_url: str = "https://visual.volcengineapi.com"
    api_key: Optional[str] = None
    credits_cost: int = 25
    default_steps: int = 30
    default_strength: float = 0.8
    default_scale: float = 7.0
    default_quality: str = "M"
    default_max_width: int = 1920
    default_max_height: int = 1920


class JimengOutpaintingRequest(BaseModel):
    original_image_url: str
    mask_image_url: Optional[str] = None
    expansion_mode: str = "equal"  # equal/aspect/custom/canvas
    custom_prompt: Optional[str] = None

    # 扩展参数
    top: Optional[float] = 0.1
    bottom: Optional[float] = 0.1
    left: Optional[float] = 0.1
    right: Optional[float] = 0.1

    # 生成参数
    steps: Optional[int] = 30
    strength: Optional[float] = 0.8
    scale: Optional[float] = 7.0
    seed: Optional[int] = 0
    quality: Optional[str] = "M"
    max_width: Optional[int] = 1920
    max_height: Optional[int] = 1920
    return_url: Optional[bool] = True


class JimengOutpaintingTaskResponse(BaseModel):
    id: str
    user_id: str
    original_image_url: str
    mask_image_url: Optional[str] = None
    expansion_mode: str
    custom_prompt: Optional[str] = None

    top: Optional[float] = None
    bottom: Optional[float] = None
    left: Optional[float] = None
    right: Optional[float] = None

    steps: int
    strength: float
    scale: float
    seed: int
    quality: str
    max_width: int
    max_height: int

    status: str
    progress: Optional[str] = None
    fail_reason: Optional[str] = None
    result_image_url: Optional[str] = None
    cloud_image_url: Optional[str] = None
    request_id: Optional[str] = None
    credits_cost: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class JimengOutpaintingHistoryResponse(BaseModel):
    data: list[JimengOutpaintingTaskResponse]
    total: int
    page: int
    limit: int


class JimengOutpaintingCreditsResponse(BaseModel):
    balance: int
    used_today: int = 0
