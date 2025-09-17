"""
Flux 数据库模型
包含配置、任务、积分记录等所有相关模型
支持多种Flux模型：Dev、Schnell、Pro、Pro Max等
"""

from pydantic import BaseModel, Field, validator
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


class FluxTextToImageRequest(BaseModel):
    """文本生成图片请求 - 支持所有Flux版本"""

    model: str = Field(..., description="Flux模型名称")
    prompt: str = Field(..., description="图片描述词，必填项")

    # 图片数量（根据模型动态验证限制）
    num_images: Optional[int] = Field(
        1,
        ge=1,
        le=8,
        description="生成图片数量：Dev/Schnell最大4，Pro最大6，Pro Max最大8",
    )

    # 尺寸参数（Dev版本使用image_size，其他版本使用aspect_ratio）
    image_size: Optional[Union[str, Dict[str, int]]] = Field(
        None, description="图片尺寸（Dev版本）：预设或自定义"
    )
    aspect_ratio: Optional[str] = Field(None, description="长宽比（Pro等版本）")

    # 生成参数
    guidance_scale: Optional[float] = Field(
        3.5, ge=1.0, le=20.0, description="引导系数，默认3.5，范围1~20"
    )
    num_inference_steps: Optional[int] = Field(
        28, ge=1, le=50, description="推理迭代步数，默认28，范围1~50"
    )
    seed: Optional[int] = Field(
        None, description="随机种子，设置后同样参数多次请求生成一致图片"
    )

    # 模式参数
    sync_mode: Optional[bool] = Field(
        False, description="同步生成，true等图片上传后直接返回，false异步"
    )

    # 安全参数
    safety_tolerance: Optional[str] = Field(
        "2", pattern=r"^[1-6]$", description="安全容忍度，1最严格，6最宽松，默认2"
    )
    enable_safety_checker: Optional[bool] = Field(True, description="启用内容安全检查")

    # 输出参数
    output_format: Optional[str] = Field(
        "jpeg", pattern=r"^(jpeg|png)$", description="输出格式，支持jpeg/png"
    )

    # 验证尺寸参数
    @validator("image_size")
    def validate_image_size(cls, v):
        if v is None:
            return v

        # 预设尺寸枚举
        PRESET_SIZES = {
            "square_hd",
            "square",
            "portrait_4_3",
            "portrait_16_9",
            "landscape_4_3",
            "landscape_16_9",
        }

        if isinstance(v, str):
            if v not in PRESET_SIZES:
                raise ValueError(f"不支持的预设尺寸: {v}。支持的选项: {PRESET_SIZES}")
        elif isinstance(v, dict):
            if "width" not in v or "height" not in v:
                raise ValueError("自定义尺寸必须包含 width 和 height")
            if v["width"] > 14142 or v["height"] > 14142:
                raise ValueError("宽高不能超过14142")
        return v

    @validator("aspect_ratio")
    def validate_aspect_ratio(cls, v):
        if v is None:
            return v

        VALID_RATIOS = {
            "21:9",
            "16:9",
            "4:3",
            "3:2",
            "1:1",
            "2:3",
            "3:4",
            "9:16",
            "9:21",
        }

        if v not in VALID_RATIOS:
            raise ValueError(f"不支持的长宽比: {v}。支持的选项: {VALID_RATIOS}")
        return v

    @validator("num_images")
    def validate_num_images(cls, v, values):
        """根据模型验证图片数量限制"""
        if v is None:
            return 1

        # 获取模型信息
        model = values.get("model", "")

        # 不同模型的图片数量限制
        if "pro/kontext/max" in model:
            max_images = 8  # Pro Max支持最多
            model_name = "FLUX.1 Pro Max"
        elif "pro/kontext" in model:
            max_images = 6  # Pro版本
            model_name = "FLUX.1 Pro"
        elif "schnell" in model:
            max_images = 4  # Schnell版本
            model_name = "FLUX.1 Schnell"
        elif "dev" in model:
            max_images = 4  # Dev版本
            model_name = "FLUX.1 Dev"
        else:
            max_images = 4  # 默认限制
            model_name = "当前模型"

        if v < 1:
            raise ValueError("图片数量必须至少为1")
        if v > max_images:
            raise ValueError(
                f"{model_name}最多支持生成{max_images}张图片，您请求的是{v}张"
            )

        return v


class FluxImageToImageRequest(BaseModel):
    """单图片生成图片请求"""

    model: str = Field(..., description="Flux模型名称")
    prompt: str = Field(..., description="文本提示，用于描述需要生成哪种风格或内容")
    image_url: str = Field(..., description="原始图片的公网URL（必填）")

    # 图生图专用参数
    strength: Optional[float] = Field(
        0.95, ge=0.01, le=1.0, description="初始图片风格保留程度，越高保留越多"
    )

    # 基本生成参数
    num_images: Optional[int] = Field(
        1, ge=1, le=4, description="要生成的图片数量，默认1张，图生图模式最大4张"
    )
    num_inference_steps: Optional[int] = Field(
        40, ge=10, le=50, description="生成采样步数，步数越多质量可能越高但速度更慢"
    )
    guidance_scale: Optional[float] = Field(
        3.5,
        ge=1.0,
        le=20.0,
        description="控制生成图片与prompt的契合程度，数值越高越接近prompt",
    )
    seed: Optional[int] = Field(
        None, description="随机种子，用于结果复现，同样参数和seed会得到一致结果"
    )

    # 模式参数
    sync_mode: Optional[bool] = Field(False, description="是否启用同步模式，建议异步")
    enable_safety_checker: Optional[bool] = Field(
        True, description="是否启用安全检测，过滤不安全内容"
    )

    # 尺寸参数（Redux版本使用）
    image_size: Optional[Union[str, Dict[str, int]]] = Field(
        None, description="图片尺寸（Redux版本）"
    )

    @validator("image_size")
    def validate_image_size(cls, v):
        if v is None:
            return v

        PRESET_SIZES = {
            "square_hd",
            "square",
            "portrait_4_3",
            "portrait_16_9",
            "landscape_4_3",
            "landscape_16_9",
        }

        if isinstance(v, str) and v not in PRESET_SIZES:
            raise ValueError(f"不支持的预设尺寸: {v}")
        elif isinstance(v, dict):
            if "width" not in v or "height" not in v:
                raise ValueError("自定义尺寸必须包含 width 和 height")
            if v["width"] > 14142 or v["height"] > 14142:
                raise ValueError("宽高不能超过14142")
        return v


class FluxMultiImageRequest(BaseModel):
    """多图片编辑请求（实验性功能）"""

    model: str = Field(..., description="Flux模型名称，必须是 multi_image 类型")
    prompt: str = Field(..., description="描述你想对图片实现的编辑目标，必填")
    image_urls: List[str] = Field(
        ..., min_items=1, description="要编辑的图片URL列表，必填"
    )

    # 基本参数
    num_images: Optional[int] = Field(
        1, ge=1, le=4, description="返回图片数量，多图编辑模式1-4张"
    )
    guidance_scale: Optional[float] = Field(
        3.5, description="引导强度，数值越大越偏向prompt描述"
    )
    seed: Optional[int] = Field(
        None, description="生成图片的随机种子（可选，相同seed可复刻同样生成结果）"
    )

    # 尺寸参数
    aspect_ratio: Optional[str] = Field(
        None, description="可选。输出图片宽高比。如'16:9'"
    )

    # 模式参数
    sync_mode: Optional[bool] = Field(
        False, description="是否同步返回结果，true同步返回图片，false异步（推荐）"
    )

    # 安全和输出参数
    safety_tolerance: Optional[str] = Field(
        "2", pattern=r"^[1-6]$", description="风险内容检测敏感级别。1最严，6最宽松"
    )
    output_format: Optional[str] = Field(
        "jpeg", pattern=r"^(jpeg|png)$", description="图片返回格式，可选jpeg/png"
    )

    @validator("aspect_ratio")
    def validate_aspect_ratio(cls, v):
        if v is None:
            return v

        VALID_RATIOS = {
            "21:9",
            "16:9",
            "4:3",
            "3:2",
            "1:1",
            "2:3",
            "3:4",
            "9:16",
            "9:21",
        }

        if v not in VALID_RATIOS:
            raise ValueError(f"不支持的长宽比: {v}。支持的选项: {VALID_RATIOS}")
        return v


class FluxTaskResponse(BaseModel):
    """Flux任务响应"""

    id: str
    status: str
    model: str
    task_type: str
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    cloud_image_url: Optional[str] = None
    queue_position: Optional[int] = None
    generation_time: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class FluxConfigForm(BaseModel):
    """Flux配置表单"""

    api_key: str = Field(..., description="Fal.ai API密钥")
    base_url: str = Field("https://queue.fal.run", description="API基础URL")
    enabled: bool = Field(True, description="启用状态")
    timeout: int = Field(300, description="请求超时时间")
    max_concurrent_tasks: int = Field(5, description="最大并发任务数")
    default_model: str = Field("fal-ai/flux-1/dev", description="默认模型")
    model_credits: Optional[Dict[str, int]] = Field(None, description="各模型积分配置")


class FluxUploadResponse(BaseModel):
    """图片上传响应"""

    success: bool
    message: str
    url: Optional[str] = None
    file_id: Optional[str] = None


# ======================== SQLAlchemy 数据库模型 ========================


class FluxConfig(Base):
    """Flux配置表"""

    __tablename__ = "flux_config"

    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key = Column(Text, nullable=False, comment="Fal.ai API密钥")
    base_url = Column(
        String(500),
        nullable=False,
        default="https://queue.fal.run",
        comment="API基础URL",
    )
    enabled = Column(Boolean, nullable=False, default=True, comment="启用状态")
    timeout = Column(Integer, nullable=False, default=300, comment="请求超时时间（秒）")
    max_concurrent_tasks = Column(
        Integer, nullable=False, default=5, comment="最大并发任务数"
    )
    default_model = Column(
        String(100), nullable=False, default="fal-ai/flux-1/dev", comment="默认模型"
    )
    model_credits = Column(JSON, comment="各模型积分配置")

    # 时间字段
    created_at = Column(
        DateTime, nullable=False, default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    def to_dict(self):
        """转换为字典格式"""
        # 处理model_credits可能不存在的情况
        model_credits = getattr(self, "model_credits", None)
        if model_credits is None:
            # 使用默认值
            model_credits = {
                "fal-ai/flux-1/schnell": 5,
                "fal-ai/flux-1/dev": 10,
                "fal-ai/flux-1/dev/image-to-image": 10,
                "fal-ai/flux-pro": 20,
                "fal-ai/flux-pro/kontext": 25,
                "fal-ai/flux-pro/kontext/multi": 30,
                "fal-ai/flux-pro/max": 35,
            }

        return {
            "id": self.id,
            "api_key": (
                self.api_key[:8] + "****" if self.api_key else None
            ),  # 隐藏敏感信息
            "base_url": self.base_url,
            "enabled": self.enabled,
            "timeout": self.timeout,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "default_model": self.default_model,
            "model_credits": model_credits,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FluxTask(Base):
    """Flux任务表"""

    __tablename__ = "flux_tasks"

    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True, comment="用户ID")
    request_id = Column(String(255), nullable=False, index=True, comment="Fal.ai请求ID")

    # 任务基本信息
    model = Column(String(100), nullable=False, comment="使用的模型")
    task_type = Column(
        String(20), nullable=False, comment="任务类型: text_to_image, image_to_image"
    )
    status = Column(String(20), nullable=False, default="PENDING", comment="任务状态")

    # 输入参数
    prompt = Column(Text, comment="文本提示词")
    input_image_url = Column(Text, comment="输入图片URL（图生图）")
    input_image_urls = Column(JSON, comment="多图片URL列表（多图编辑）")
    uploaded_image_url = Column(Text, comment="用户上传后的云存储URL")

    # 生成参数
    num_images = Column(Integer, default=1, comment="生成图片数量")
    aspect_ratio = Column(String(20), default="1:1", comment="宽高比")
    image_size = Column(JSON, comment="图片尺寸参数（Dev版本）")
    guidance_scale = Column(Float, default=3.5, comment="引导系数")
    num_inference_steps = Column(Integer, default=28, comment="推理步数")
    seed = Column(Integer, comment="随机种子")
    safety_tolerance = Column(Integer, default=2, comment="安全容忍度")
    strength = Column(Float, default=0.95, comment="图生图强度")
    sync_mode = Column(Boolean, default=False, comment="同步模式")
    output_format = Column(String(10), default="jpeg", comment="输出格式")
    enable_safety_checker = Column(Boolean, default=True, comment="启用安全检查")

    # 结果信息
    image_url = Column(Text, comment="生成的图片URL")
    cloud_image_url = Column(Text, comment="云存储图片URL")
    generation_time = Column(Float, comment="生成耗时（秒）")
    queue_position = Column(Integer, comment="队列位置")

    # 错误信息
    error_message = Column(Text, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")

    # 元数据
    flux_response = Column(JSON, comment="Flux API原始响应")

    # 时间信息
    created_at = Column(
        DateTime, nullable=False, default=func.now(), index=True, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
    completed_at = Column(DateTime, comment="完成时间")

    # 复合索引
    __table_args__ = (
        Index("idx_flux_tasks_user_status", "user_id", "status"),
        Index("idx_flux_tasks_model_status", "model", "status"),
    )

    def to_dict(self):
        """转换为字典格式，用于API返回"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "model": self.model,
            "task_type": self.task_type,
            "status": self.status,
            "prompt": self.prompt,
            "input_image_url": self.input_image_url,
            "input_image_urls": getattr(self, "input_image_urls", None),  # 多图编辑支持
            "uploaded_image_url": self.uploaded_image_url,
            "num_images": self.num_images,
            "aspect_ratio": self.aspect_ratio,
            "guidance_scale": self.guidance_scale,
            "num_inference_steps": self.num_inference_steps,
            "seed": self.seed,
            "safety_tolerance": self.safety_tolerance,
            "strength": self.strength,
            "sync_mode": self.sync_mode,
            "output_format": self.output_format,
            "enable_safety_checker": self.enable_safety_checker,
            "image_url": self.cloud_image_url or self.image_url,  # 优先返回云存储URL
            "cloud_image_url": self.cloud_image_url,
            "generation_time": self.generation_time,
            "queue_position": self.queue_position,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "image_size": getattr(self, "image_size", None),  # Dev版本支持
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    def update_from_flux_response(self, flux_response: Dict[str, Any]):
        """从Flux API响应更新任务信息"""
        import logging

        logger = logging.getLogger(__name__)

        if flux_response is None:
            return

        # 保存原始响应
        self.flux_response = flux_response
        self.updated_at = func.now()

        # 更新状态
        if "status" in flux_response:
            raw_status = flux_response["status"]
            # 状态映射 - 有些API返回不同的状态值
            status_mapping = {
                "COMPLETED": "SUCCESS",
                "DONE": "SUCCESS",
                "FINISHED": "SUCCESS",
                "SUCCESS": "SUCCESS",
                "FAILED": "FAILED",
                "ERROR": "FAILED",
                "CANCELLED": "CANCELLED",
                "CANCELED": "CANCELLED",
                "PENDING": "PENDING",
                "IN_QUEUE": "PENDING",
                "QUEUED": "PENDING",
                "IN_PROGRESS": "IN_PROGRESS",
                "PROCESSING": "IN_PROGRESS",
                "RUNNING": "IN_PROGRESS",
            }

            mapped_status = status_mapping.get(raw_status.upper(), raw_status)
            self.status = mapped_status

        # 更新队列位置
        if "queue_position" in flux_response:
            self.queue_position = flux_response["queue_position"]

        # 更新结果URL - 这是最重要的部分
        if "images" in flux_response and flux_response["images"]:
            image_data = flux_response["images"][0]
            if "url" in image_data:
                self.image_url = image_data["url"]
                self.status = "SUCCESS"
                self.completed_at = func.now()
                logger.info(
                    f"Task {self.id} completed with image URL: {image_data['url']}"
                )
        elif mapped_status == "SUCCESS" and "response_url" in flux_response:
            # 如果状态是SUCCESS但没有images，记录需要获取结果
            logger.warning(
                f"Task {self.id} marked as SUCCESS but no images found, response_url available: {flux_response['response_url']}"
            )

        # 更新生成时间
        if "timings" in flux_response and "inference" in flux_response["timings"]:
            self.generation_time = flux_response["timings"]["inference"]

        # 更新种子
        if "seed" in flux_response:
            self.seed = flux_response["seed"]


class FluxCredits(Base):
    """Flux积分表"""

    __tablename__ = "flux_credits"

    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True, comment="用户ID")
    credits_balance = Column(Integer, nullable=False, default=0, comment="剩余积分")
    total_used = Column(Integer, nullable=False, default=0, comment="已使用积分")

    # 时间字段
    created_at = Column(
        DateTime, nullable=False, default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "credits_balance": self.credits_balance,
            "total_used": self.total_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ======================== 数据库操作类 ========================


class FluxConfigs:
    """Flux配置数据库操作类"""

    @staticmethod
    def get_config() -> Optional[FluxConfig]:
        """获取Flux配置 - 向后兼容处理"""
        import logging
        from sqlalchemy.exc import OperationalError

        logger = logging.getLogger(__name__)

        with get_db() as db:
            try:
                # 尝试正常查询
                return db.query(FluxConfig).first()
            except OperationalError as e:
                if "no such column: flux_config.model_credits" in str(e):
                    # model_credits列不存在，使用原始查询方式
                    logger.warning("model_credits列不存在，使用兼容查询")
                    try:
                        from sqlalchemy import text

                        result = db.execute(
                            text(
                                """
                            SELECT id, api_key, base_url, enabled, timeout, 
                                   max_concurrent_tasks, default_model, created_at, updated_at
                            FROM flux_config 
                            LIMIT 1
                        """
                            )
                        ).fetchone()

                        if result:
                            # 手动创建FluxConfig对象
                            config = FluxConfig()
                            config.id = result[0]
                            config.api_key = result[1]
                            config.base_url = result[2]
                            config.enabled = result[3]
                            config.timeout = result[4]
                            config.max_concurrent_tasks = result[5]
                            config.default_model = result[6]
                            config.created_at = result[7]
                            config.updated_at = result[8]
                            config.model_credits = None  # 旧版本没有这个字段
                            return config

                        return None
                    except Exception as inner_e:
                        logger.error(f"兼容查询也失败: {inner_e}")
                        return None
                else:
                    # 其他类型的错误，重新抛出
                    raise e

    @staticmethod
    def create_or_update_config(form: FluxConfigForm) -> FluxConfig:
        """创建或更新Flux配置 - 向后兼容处理"""
        import logging
        from sqlalchemy.exc import OperationalError

        logger = logging.getLogger(__name__)

        with get_db() as db:
            try:
                # 直接在当前Session中查询配置，避免Session分离问题
                config = db.query(FluxConfig).first()

                if config:
                    # 更新现有配置
                    config.api_key = form.api_key
                    config.base_url = form.base_url
                    config.enabled = form.enabled
                    config.timeout = form.timeout
                    config.max_concurrent_tasks = form.max_concurrent_tasks
                    config.default_model = form.default_model
                    config.model_credits = form.model_credits
                    config.updated_at = func.now()

                    # config已经在当前session中，直接更新
                else:
                    # 创建新配置
                    config = FluxConfig(
                        api_key=form.api_key,
                        base_url=form.base_url,
                        enabled=form.enabled,
                        timeout=form.timeout,
                        max_concurrent_tasks=form.max_concurrent_tasks,
                        default_model=form.default_model,
                        model_credits=form.model_credits,
                    )
                    db.add(config)

                db.commit()
                db.refresh(config)
                return config

            except OperationalError as e:
                if "no such column" in str(e) and "model_credits" in str(e):
                    # model_credits列不存在，忽略该字段进行更新
                    logger.warning("model_credits列不存在，跳过该字段更新")

                    try:
                        from sqlalchemy import text

                        # 重新查询配置以确保在当前Session中
                        existing_config = db.execute(
                            text("SELECT * FROM flux_config LIMIT 1")
                        ).fetchone()

                        if existing_config:
                            # 更新现有配置（不包含model_credits）
                            db.execute(
                                text(
                                    """
                                UPDATE flux_config 
                                SET api_key = :api_key, base_url = :base_url, enabled = :enabled,
                                    timeout = :timeout, max_concurrent_tasks = :max_concurrent_tasks,
                                    default_model = :default_model, updated_at = CURRENT_TIMESTAMP
                                WHERE id = :config_id
                            """
                                ),
                                {
                                    "api_key": form.api_key,
                                    "base_url": form.base_url,
                                    "enabled": form.enabled,
                                    "timeout": form.timeout,
                                    "max_concurrent_tasks": form.max_concurrent_tasks,
                                    "default_model": form.default_model,
                                    "config_id": existing_config[0],  # 使用查询到的ID
                                },
                            )
                            config_id = existing_config[0]
                        else:
                            # 创建新配置（不包含model_credits）
                            import uuid

                            new_id = str(uuid.uuid4())
                            db.execute(
                                text(
                                    """
                                INSERT INTO flux_config 
                                (id, api_key, base_url, enabled, timeout, max_concurrent_tasks, 
                                 default_model, created_at, updated_at)
                                VALUES (:id, :api_key, :base_url, :enabled, :timeout, 
                                        :max_concurrent_tasks, :default_model, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """
                                ),
                                {
                                    "id": new_id,
                                    "api_key": form.api_key,
                                    "base_url": form.base_url,
                                    "enabled": form.enabled,
                                    "timeout": form.timeout,
                                    "max_concurrent_tasks": form.max_concurrent_tasks,
                                    "default_model": form.default_model,
                                },
                            )
                            config_id = new_id

                        db.commit()

                        # 创建返回对象
                        config = FluxConfig()
                        config.id = config_id
                        config.api_key = form.api_key
                        config.base_url = form.base_url
                        config.enabled = form.enabled
                        config.timeout = form.timeout
                        config.max_concurrent_tasks = form.max_concurrent_tasks
                        config.default_model = form.default_model
                        config.model_credits = None  # 旧版本不支持

                        return config

                    except Exception as inner_e:
                        logger.error(f"兼容保存也失败: {inner_e}")
                        raise inner_e
                else:
                    # 其他类型的错误，重新抛出
                    raise e


class FluxTasks:
    """Flux任务数据库操作类"""

    @staticmethod
    def create_task(
        user_id: str,
        model: str,
        task_type: str,
        prompt: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> FluxTask:
        """创建Flux任务"""
        with get_db() as db:
            task = FluxTask(
                user_id=user_id,
                model=model,
                task_type=task_type,
                prompt=prompt,
                request_id=request_id or str(uuid.uuid4()),
                **kwargs,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    @staticmethod
    def get_task_by_id(task_id: str) -> Optional[FluxTask]:
        """根据ID获取任务"""
        with get_db() as db:
            return db.query(FluxTask).filter(FluxTask.id == task_id).first()

    @staticmethod
    def get_task_by_request_id(request_id: str) -> Optional[FluxTask]:
        """根据request_id获取任务"""
        with get_db() as db:
            return db.query(FluxTask).filter(FluxTask.request_id == request_id).first()

    @staticmethod
    def get_user_tasks(
        user_id: str, page: int = 1, limit: int = 20, status: Optional[str] = None
    ) -> List[FluxTask]:
        """获取用户任务列表"""
        with get_db() as db:
            query = db.query(FluxTask).filter(FluxTask.user_id == user_id)

            if status:
                query = query.filter(FluxTask.status == status)

            return (
                query.order_by(FluxTask.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )

    @staticmethod
    def get_user_task_count(user_id: str, status: Optional[str] = None) -> int:
        """获取用户任务总数"""
        with get_db() as db:
            query = db.query(FluxTask).filter(FluxTask.user_id == user_id)

            if status:
                query = query.filter(FluxTask.status == status)

            return query.count()

    @staticmethod
    def update_task_status(task_id: str, status: str, **kwargs) -> bool:
        """更新任务状态"""
        with get_db() as db:
            task = db.query(FluxTask).filter(FluxTask.id == task_id).first()
            if not task:
                return False

            task.status = status
            task.updated_at = func.now()

            # 更新其他字段
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            if status == "SUCCESS":
                task.completed_at = func.now()

            db.commit()
            return True


class FluxCreditsManager:
    """Flux积分管理类"""

    @staticmethod
    def get_user_credits(user_id: str) -> FluxCredits:
        """获取用户积分信息"""
        with get_db() as db:
            credits = (
                db.query(FluxCredits).filter(FluxCredits.user_id == user_id).first()
            )
            if not credits:
                # 创建新的积分记录
                credits = FluxCredits(
                    user_id=user_id, credits_balance=100
                )  # 默认100积分
                db.add(credits)
                db.commit()
                db.refresh(credits)
            return credits

    @staticmethod
    def deduct_credits(user_id: str, amount: int) -> bool:
        """扣除积分"""
        with get_db() as db:
            credits = (
                db.query(FluxCredits).filter(FluxCredits.user_id == user_id).first()
            )
            if not credits or credits.credits_balance < amount:
                return False

            credits.credits_balance -= amount
            credits.total_used += amount
            credits.updated_at = func.now()
            db.commit()
            return True

    @staticmethod
    def add_credits(user_id: str, amount: int) -> bool:
        """增加积分"""
        with get_db() as db:
            credits = (
                db.query(FluxCredits).filter(FluxCredits.user_id == user_id).first()
            )
            if not credits:
                credits = FluxCredits(user_id=user_id, credits_balance=amount)
                db.add(credits)
            else:
                credits.credits_balance += amount
                credits.updated_at = func.now()

            db.commit()
            return True


# ======================== 工具函数 ========================


def get_flux_config() -> Optional[FluxConfig]:
    """获取当前Flux配置"""
    return FluxConfigs.get_config()


def is_flux_enabled() -> bool:
    """检查Flux是否启用"""
    config = get_flux_config()
    return config is not None and config.enabled


def get_supported_flux_models() -> List[Dict[str, str]]:
    """获取支持的Flux模型列表"""
    return [
        {
            "id": "fal-ai/flux-1/dev",
            "name": "FLUX.1 Dev",
            "type": "text_to_image",
            "description": "开发版本，适合测试",
        },
        {
            "id": "fal-ai/flux-1/dev/image-to-image",
            "name": "FLUX.1 Dev 图生图",
            "type": "image_to_image",
            "description": "基于输入图片生成",
        },
        {
            "id": "fal-ai/flux-1/dev/redux",
            "name": "FLUX.1 Dev Redux",
            "type": "redux",
            "description": "Redux风格处理",
        },
        {
            "id": "fal-ai/flux-1/schnell",
            "name": "FLUX.1 Schnell",
            "type": "text_to_image",
            "description": "快速生成版本",
        },
        {
            "id": "fal-ai/flux-1/schnell/redux",
            "name": "FLUX.1 Schnell Redux",
            "type": "redux",
            "description": "快速Redux版本",
        },
        {
            "id": "fal-ai/flux-pro/kontext",
            "name": "FLUX.1 Pro",
            "type": "text_to_image",
            "description": "专业版本",
        },
        {
            "id": "fal-ai/flux-pro/kontext/max",
            "name": "FLUX.1 Pro Max",
            "type": "text_to_image",
            "description": "最高质量版本",
        },
        {
            "id": "fal-ai/flux-pro/kontext/max/multi",
            "name": "FLUX.1 Pro Max Multi",
            "type": "multi_image",
            "description": "实验性多图编辑",
        },
        {
            "id": "fal-ai/flux-pro/kontext/max/text-to-image",
            "name": "FLUX.1 Pro Max T2I",
            "type": "text_to_image",
            "description": "专门的文本转图像",
        },
        {
            "id": "fal-ai/flux-pro/kontext/multi",
            "name": "FLUX.1 Pro Multi",
            "type": "multi_image",
            "description": "实验性多图编辑",
        },
        {
            "id": "fal-ai/flux-pro/kontext/text-to-image",
            "name": "FLUX.1 Pro T2I",
            "type": "text_to_image",
            "description": "专门的文本转图像",
        },
    ]
