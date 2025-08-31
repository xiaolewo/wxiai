"""
可灵视频生成数据模型
基于可灵API规范的完整数据模型定义
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON, Float
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import uuid

from open_webui.internal.db import Base, get_db

# ======================== SQLAlchemy 数据库模型 ========================


class KlingConfig(Base):
    __tablename__ = "kling_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False)
    base_url = Column(String(500), default="https://api.klingai.com")
    api_key = Column(Text)

    # 模型配置
    text_to_video_model = Column(String(100), default="kling-v1")
    image_to_video_model = Column(String(100), default="kling-v1")

    # 默认参数
    default_mode = Column(String(20), default="std")
    default_duration = Column(String(10), default="5")
    default_aspect_ratio = Column(String(20), default="16:9")
    default_cfg_scale = Column(Float, default=0.5)

    # 积分配置 - 兼容旧版本的通用配置
    credits_per_std_5s = Column(Integer, default=50)
    credits_per_std_10s = Column(Integer, default=100)
    credits_per_pro_5s = Column(Integer, default=100)
    credits_per_pro_10s = Column(Integer, default=200)

    # 视频延长积分配置
    credits_per_extend = Column(Integer, default=30)

    # 模型版本积分配置 - JSON存储，支持灵活配置
    model_credits_config = Column(JSON)

    # 系统配置
    max_concurrent_tasks = Column(Integer, default=3)
    task_timeout = Column(Integer, default=600000)

    # API路径配置
    detected_api_path = Column(String(200))  # 自动检测到的有效API路径

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def get_config(cls):
        """获取可灵配置"""
        with get_db() as db:
            return db.query(cls).filter(cls.id == 1).first()

    @classmethod
    def save_config(cls, config_data: dict):
        """保存可灵配置"""
        with get_db() as db:
            config = db.query(cls).filter(cls.id == 1).first()

            if config:
                # 更新现有配置
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                config.updated_at = datetime.now()
            else:
                # 创建新配置
                config_data["id"] = 1
                config = cls(**config_data)
                db.add(config)

            db.commit()
            db.refresh(config)
            return config

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "text_to_video_model": self.text_to_video_model,
            "image_to_video_model": self.image_to_video_model,
            "default_mode": self.default_mode,
            "default_duration": self.default_duration,
            "default_aspect_ratio": self.default_aspect_ratio,
            "default_cfg_scale": self.default_cfg_scale,
            "credits_per_std_5s": self.credits_per_std_5s,
            "credits_per_std_10s": self.credits_per_std_10s,
            "credits_per_pro_5s": self.credits_per_pro_5s,
            "credits_per_pro_10s": self.credits_per_pro_10s,
            "credits_per_extend": self.credits_per_extend,
            "model_credits_config": self.model_credits_config
            or self._get_default_model_credits(),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
            "detected_api_path": self.detected_api_path,
            "created_at": (
                self.created_at.isoformat() if self.created_at is not None else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at is not None else None
            ),
        }

    def _get_default_model_credits(self) -> dict:
        """获取默认的模型积分配置"""
        return {
            "kling-v1": {
                "std": {"5": 50, "10": 100, "extend": 30}, 
                "pro": {"5": 100, "10": 200, "extend": 50}
            },
            "kling-v1-5": {
                "std": {"5": 60, "10": 120, "extend": 35}, 
                "pro": {"5": 120, "10": 240, "extend": 60}
            },
            "kling-v1-6": {
                "std": {"5": 70, "10": 140, "extend": 40}, 
                "pro": {"5": 140, "10": 280, "extend": 70}
            },
            "kling-v2-master": {
                "std": {"5": 100, "10": 200},
                "pro": {"5": 200, "10": 400},
            },
            "kling-v2-1": {"std": {"5": 110, "10": 220}, "pro": {"5": 220, "10": 440}},
            "kling-v2-1-master": {
                "std": {"5": 120, "10": 240},
                "pro": {"5": 240, "10": 480},
            },
        }

    def get_credits_cost(self, mode: str, duration: str, model_name: str = None) -> int:
        """根据模式、时长和模型版本获取积分消耗"""
        mode = mode.lower()
        duration = str(duration)

        # 如果有模型版本积分配置，优先使用
        if model_name and self.model_credits_config:
            model_config = self.model_credits_config.get(model_name)
            if (
                model_config
                and model_config.get(mode)
                and model_config[mode].get(duration)
            ):
                return int(model_config[mode][duration])

        # 回退到默认配置（向后兼容）
        if mode == "std" and duration == "5":
            return self.credits_per_std_5s
        elif mode == "std" and duration == "10":
            return self.credits_per_std_10s
        elif mode == "pro" and duration == "5":
            return self.credits_per_pro_5s
        elif mode == "pro" and duration == "10":
            return self.credits_per_pro_10s
        else:
            # 默认按标准5秒计算
            return self.credits_per_std_5s

    def get_extend_credits_cost(self, mode: str, model_name: str = None) -> int:
        """根据模式和模型版本获取视频延长积分消耗"""
        mode = mode.lower()
        
        # 如果有模型版本积分配置，优先使用
        if model_name and self.model_credits_config:
            model_config = self.model_credits_config.get(model_name)
            if (
                model_config
                and model_config.get(mode)
                and model_config[mode].get("extend")
            ):
                return int(model_config[mode]["extend"])
        
        # 使用默认配置中的extend值
        default_config = self._get_default_model_credits()
        if model_name and model_name in default_config:
            model_config = default_config[model_name]
            if model_config.get(mode) and model_config[mode].get("extend"):
                return int(model_config[mode]["extend"])
        
        # 回退到通用延长积分配置
        if self.credits_per_extend:
            return self.credits_per_extend
            
        # 最终兜底：根据模式返回默认值
        return 50 if mode == "pro" else 30


class KlingTask(Base):
    __tablename__ = "kling_tasks"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    external_task_id = Column(String(100))

    # 任务类型和状态
    action = Column(String(50), nullable=False)  # TEXT_TO_VIDEO, IMAGE_TO_VIDEO, MULTI_IMAGE_TO_VIDEO
    status = Column(String(50), default="SUBMITTED")
    task_status_msg = Column(Text)

    # 多图支持字段
    generation_mode = Column(String(20), default="single_image")
    input_images = Column(JSON)
    image_count = Column(Integer, default=0)

    # 基础视频生成参数
    model_name = Column(String(100))
    prompt = Column(Text)
    negative_prompt = Column(Text)
    cfg_scale = Column(Float)
    mode = Column(String(20))
    duration = Column(String(10))
    aspect_ratio = Column(String(20))

    # 图生视频专用参数
    input_image = Column(Text)
    image_tail = Column(Text)
    static_mask = Column(Text)
    dynamic_masks = Column(JSON)

    # 摄像机控制参数
    camera_control = Column(JSON)

    # 积分和任务管理
    credits_cost = Column(Integer, default=0)
    submit_time = Column(DateTime)
    start_time = Column(DateTime)
    finish_time = Column(DateTime)

    # 结果数据
    video_id = Column(String(100))
    video_url = Column(Text)
    cloud_video_url = Column(Text, comment="云存储视频URL")
    video_duration = Column(String(10))
    fail_reason = Column(Text)

    # 请求和响应数据存储
    request_data = Column(Text)
    response_data = Column(Text)

    # 元数据
    properties = Column(JSON)
    progress = Column(String(20), default="0%")

    # 视频延长相关字段
    parent_task_id = Column(String(50), nullable=True, comment="父任务ID，延长任务专用")
    is_extended = Column(Boolean, default=False, comment="是否为延长任务")
    original_duration = Column(String(10), nullable=True, comment="原视频时长")
    extend_count = Column(Integer, default=0, comment="延长次数")

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def create_task(
        cls,
        user_id: str,
        action: str,
        prompt: str,
        model_name: Optional[str] = None,
        mode: str = "std",
        duration: str = "5",
        aspect_ratio: str = "16:9",
        cfg_scale: Optional[float] = None,
        negative_prompt: Optional[str] = None,
        credits_cost: int = 0,
        input_image: Optional[str] = None,
        image_tail: Optional[str] = None,
        static_mask: Optional[str] = None,
        dynamic_masks: Optional[List[Dict]] = None,
        camera_control: Optional[Dict] = None,
        properties: Optional[Dict] = None,
        generation_mode: str = "single_image",
        input_images: Optional[List[Dict]] = None,
        image_count: int = 0,
        # 视频延长相关参数
        parent_task_id: Optional[str] = None,
        is_extended: bool = False,
        original_duration: Optional[str] = None,
        extend_count: int = 0,
    ):
        """创建新任务"""
        task_id = str(uuid.uuid4())

        with get_db() as db:
            task = cls(
                id=task_id,
                user_id=user_id,
                action=action,
                prompt=prompt,
                model_name=model_name,
                mode=mode,
                duration=duration,
                aspect_ratio=aspect_ratio,
                cfg_scale=cfg_scale,
                negative_prompt=negative_prompt,
                credits_cost=credits_cost,
                input_image=input_image,
                image_tail=image_tail,
                static_mask=static_mask,
                dynamic_masks=dynamic_masks,
                camera_control=camera_control,
                properties=properties,
                generation_mode=generation_mode,
                input_images=input_images,
                image_count=image_count,
                parent_task_id=parent_task_id,
                is_extended=is_extended,
                original_duration=original_duration,
                extend_count=extend_count,
                submit_time=datetime.now(),
            )

            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    @classmethod
    def get_task_by_id(cls, task_id: str):
        """根据任务ID获取任务"""
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
    def get_user_task_count(cls, user_id: str) -> int:
        """获取用户任务总数"""
        with get_db() as db:
            return db.query(cls).filter(cls.user_id == user_id).count()

    @classmethod
    def get_task_by_video_id(cls, video_id: str):
        """根据视频ID获取任务"""
        with get_db() as db:
            return db.query(cls).filter(cls.video_id == video_id).first()

    @classmethod
    def get_task_extend_count(cls, task_id: str) -> int:
        """获取任务的延长次数"""
        with get_db() as db:
            # 统计以该任务为父任务的延长任务数量
            return db.query(cls).filter(cls.parent_task_id == task_id).count()
    
    def can_extend(self) -> tuple[bool, str, int]:
        """
        检查任务是否可以延长
        Returns:
            tuple[bool, str, int]: (是否可以延长, 原因, 需要的积分)
        """
        # 支持的模型版本
        SUPPORTED_MODELS = ["kling-v1", "kling-v1-5", "kling-v1-6"]
        
        # 检查任务状态
        if self.status != "succeed":
            return False, "只能延长已成功生成的视频", 0
            
        # 检查是否有视频URL
        if not self.video_url:
            return False, "视频文件不存在，无法延长", 0
            
        # 检查模型版本支持
        if self.model_name not in SUPPORTED_MODELS:
            return False, f"当前模型 {self.model_name} 不支持视频延长，仅支持 {', '.join(SUPPORTED_MODELS)}", 0
            
        # 检查视频创建时间（30天限制）
        if self.created_at:
            from datetime import datetime, timedelta
            creation_time = self.created_at
            if isinstance(creation_time, str):
                creation_time = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            
            days_since_creation = (datetime.now() - creation_time.replace(tzinfo=None)).days
            if days_since_creation > 30:
                return False, "视频已超过30天，无法延长", 0
                
        # 计算当前视频总时长
        current_duration = self.get_total_duration()
        
        # 检查是否超过最大时长限制（180秒）
        MAX_DURATION = 180
        if current_duration >= MAX_DURATION:
            return False, f"视频时长已达到最大限制({MAX_DURATION}秒)，无法继续延长", 0
            
        # 获取延长积分消耗
        config = KlingConfig.get_config()
        if not config:
            return False, "系统配置未找到，无法计算积分", 0
            
        credits_cost = config.get_extend_credits_cost(self.mode, self.model_name)
        
        return True, "", credits_cost
    
    def get_total_duration(self) -> int:
        """
        获取视频总时长（包括所有延长）
        Returns:
            int: 总时长（秒）
        """
        if not self.video_duration:
            # 如果没有视频时长信息，使用任务设置的时长
            return int(self.duration or "5")
            
        try:
            return int(float(self.video_duration))
        except (ValueError, TypeError):
            # 解析失败时回退到任务设置时长
            return int(self.duration or "5")
    
    @classmethod  
    def get_original_task(cls, task_id: str):
        """
        获取原始任务（非延长任务）
        如果传入的是延长任务，则返回其根任务
        """
        with get_db() as db:
            task = db.query(cls).filter(cls.id == task_id).first()
            if not task:
                return None
                
            # 如果是延长任务，找到根任务
            while task.parent_task_id:
                parent_task = db.query(cls).filter(cls.id == task.parent_task_id).first()
                if not parent_task:
                    break
                task = parent_task
                
            return task

    def update_status(self, status: str, task_status_msg: Optional[str] = None):
        """更新任务状态"""
        with get_db() as db:
            self.status = status
            if task_status_msg:
                self.task_status_msg = task_status_msg

            if status == "processing" and self.start_time is None:
                self.start_time = datetime.now()
            elif status in ["succeed", "failed"]:
                self.finish_time = datetime.now()

            self.updated_at = datetime.now()
            db.merge(self)
            db.commit()

    def update_from_api_response(self, api_response: dict):
        """从API响应更新任务信息"""
        with get_db() as db:
            # 保存完整响应
            self.response_data = json.dumps(api_response, ensure_ascii=False)

            # 提取任务信息
            data = api_response.get("data", {})

            # 更新任务状态
            self.status = data.get("task_status", "submitted")
            self.task_status_msg = data.get("task_status_msg")

            # 更新外部任务ID
            if self.external_task_id is None or self.external_task_id == "":
                self.external_task_id = data.get("task_id")

            # 处理任务结果
            task_result = data.get("task_result", {})
            if task_result and "videos" in task_result:
                videos = task_result["videos"]
                if videos and len(videos) > 0:
                    video = videos[0]
                    self.video_id = video.get("id")
                    self.video_url = video.get("url")
                    self.video_duration = video.get("duration")

            # 更新进度和时间戳
            if self.status == "submitted":
                self.progress = "等待中..."
            elif self.status == "processing":
                self.progress = "生成中..."
                if self.start_time is None:
                    self.start_time = datetime.now()
            elif self.status == "succeed":
                self.progress = "100%"
                if self.finish_time is None:
                    self.finish_time = datetime.now()
            elif self.status == "failed":
                self.progress = "失败"
                if self.finish_time is None:
                    self.finish_time = datetime.now()

            self.updated_at = datetime.now()
            db.merge(self)
            db.commit()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "external_task_id": self.external_task_id,
            "action": self.action,
            "status": self.status,
            "task_status_msg": self.task_status_msg,
            "model_name": self.model_name,
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "cfg_scale": self.cfg_scale,
            "mode": self.mode,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "input_image": self.input_image,
            "image_tail": self.image_tail,
            "static_mask": self.static_mask,
            "dynamic_masks": self.dynamic_masks,
            "camera_control": self.camera_control,
            "generation_mode": self.generation_mode,
            "input_images": self.input_images,
            "image_count": self.image_count,
            "parent_task_id": self.parent_task_id,
            "is_extended": self.is_extended,
            "original_duration": self.original_duration,
            "extend_count": self.extend_count,
            "credits_cost": self.credits_cost,
            "submit_time": (
                self.submit_time.isoformat() if self.submit_time is not None else None
            ),
            "start_time": (
                self.start_time.isoformat() if self.start_time is not None else None
            ),
            "finish_time": (
                self.finish_time.isoformat() if self.finish_time is not None else None
            ),
            "video_id": self.video_id,
            "video_url": self.cloud_video_url or self.video_url,  # 优先返回云存储URL
            "video_duration": self.video_duration,
            "fail_reason": self.fail_reason,
            "properties": self.properties,
            "progress": self.progress,
            "created_at": (
                self.created_at.isoformat() if self.created_at is not None else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at is not None else None
            ),
            # 添加服务类型标识
            "serviceType": "kling",
        }


class KlingCredit(Base):
    __tablename__ = "kling_credits"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    balance = Column(Integer, nullable=False)
    reason = Column(String(200))
    task_id = Column(String(50))
    created_at = Column(DateTime, default=func.now())

    @classmethod
    def create_record(
        cls,
        user_id: str,
        amount: int,
        balance: int,
        reason: str,
        task_id: Optional[str] = None,
    ):
        """创建积分记录"""
        record_id = str(uuid.uuid4())

        with get_db() as db:
            record = cls(
                id=record_id,
                user_id=user_id,
                amount=amount,
                balance=balance,
                reason=reason,
                task_id=task_id,
            )

            db.add(record)
            db.commit()
            db.refresh(record)
            return record


# ======================== Pydantic 请求/响应模型 ========================


class CameraControlConfig(BaseModel):
    """摄像机控制配置"""

    horizontal: Optional[float] = Field(None, ge=-10, le=10, description="水平运镜")
    vertical: Optional[float] = Field(None, ge=-10, le=10, description="垂直运镜")
    pan: Optional[float] = Field(None, ge=-10, le=10, description="水平摇镜")
    tilt: Optional[float] = Field(None, ge=-10, le=10, description="垂直摇镜")
    roll: Optional[float] = Field(None, ge=-10, le=10, description="旋转运镜")
    zoom: Optional[float] = Field(None, ge=-10, le=10, description="变焦")


class CameraControl(BaseModel):
    """摄像机控制"""

    type: Optional[str] = Field(None, description="运镜类型")
    config: Optional[CameraControlConfig] = Field(None, description="运镜配置")


class TrajectoryPoint(BaseModel):
    """轨迹点"""

    x: int = Field(..., description="横坐标")
    y: int = Field(..., description="纵坐标")


class DynamicMask(BaseModel):
    """动态笔刷"""

    mask: str = Field(..., description="动态笔刷涂抹区域")
    trajectories: List[TrajectoryPoint] = Field(
        ..., min_items=2, max_items=77, description="运动轨迹"
    )


class KlingGenerateRequest(BaseModel):
    """可灵视频生成请求"""

    model_name: Optional[str] = Field("kling-v1", description="模型名称")
    prompt: str = Field(..., max_length=2500, description="正向提示词")
    negative_prompt: Optional[str] = Field(
        None, max_length=2500, description="负向提示词"
    )
    cfg_scale: Optional[float] = Field(0.5, ge=0, le=1, description="生成自由度")
    mode: Optional[str] = Field("std", description="生成模式 std/pro")
    duration: Optional[str] = Field("5", description="视频时长")
    aspect_ratio: Optional[str] = Field("16:9", description="画面比例")

    # 图生视频专用
    image: Optional[str] = Field(None, description="输入图片")
    image_tail: Optional[str] = Field(None, description="尾帧图片")
    static_mask: Optional[str] = Field(None, description="静态笔刷")
    dynamic_masks: Optional[List[DynamicMask]] = Field(
        None, max_items=6, description="动态笔刷"
    )

    # 多图参考生成专用
    generation_mode: Optional[str] = Field("single_image", description="生成模式: single_image, multi_image")
    image_list: Optional[List[Dict[str, str]]] = Field(
        None, max_items=4, description="多图参考列表，最多4张"
    )

    # 摄像机控制
    camera_control: Optional[CameraControl] = Field(None, description="摄像机控制")

    # 回调和自定义ID
    callback_url: Optional[str] = Field(None, description="回调地址")
    external_task_id: Optional[str] = Field(None, description="自定义任务ID")


class KlingConfigForm(BaseModel):
    """可灵配置表单"""

    enabled: bool = Field(False, description="启用状态")
    base_url: str = Field("https://api.klingai.com", description="API地址")
    api_key: str = Field(..., description="API密钥")
    text_to_video_model: str = Field("kling-v1", description="文生视频模型")
    image_to_video_model: str = Field("kling-v1", description="图生视频模型")
    default_mode: str = Field("std", description="默认模式")
    default_duration: str = Field("5", description="默认时长")
    default_aspect_ratio: str = Field("16:9", description="默认比例")
    default_cfg_scale: float = Field(0.5, description="默认CFG")
    credits_per_std_5s: int = Field(50, description="标准5秒积分")
    credits_per_std_10s: int = Field(100, description="标准10秒积分")
    credits_per_pro_5s: int = Field(100, description="专家5秒积分")
    credits_per_pro_10s: int = Field(200, description="专家10秒积分")
    credits_per_extend: int = Field(30, description="视频延长积分")
    max_concurrent_tasks: int = Field(3, description="最大并发任务")
    task_timeout: int = Field(600000, description="任务超时时间")


class KlingTaskForm(BaseModel):
    """可灵任务表单"""

    action: str = Field(..., description="任务类型")
    request: KlingGenerateRequest = Field(..., description="生成请求")


class KlingVideoExtendRequest(BaseModel):
    """可灵视频延长请求"""
    
    video_id: str = Field(..., description="源视频ID")
    prompt: Optional[str] = Field(None, max_length=2500, description="正向提示词")
    negative_prompt: Optional[str] = Field(None, max_length=2500, description="负向提示词")
    cfg_scale: Optional[float] = Field(0.5, ge=0, le=1, description="提示词参考强度")
    callback_url: Optional[str] = Field(None, description="回调地址")


class KlingVideoExtendCheck(BaseModel):
    """延长资格检查响应"""
    
    can_extend: bool = Field(..., description="是否可以延长")
    reason: Optional[str] = Field(None, description="不能延长的原因")
    credits_cost: Optional[int] = Field(None, description="延长需要的积分")
    current_duration: Optional[str] = Field(None, description="当前视频时长")
    max_duration: str = Field("180", description="最大允许时长(秒)")
    extend_count: Optional[int] = Field(None, description="已延长次数")
