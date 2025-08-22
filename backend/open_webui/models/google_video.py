"""
谷歌视频生成数据模型
基于谷歌Veo API规范的完整数据模型定义
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON, Float
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import uuid

from open_webui.internal.db import Base, get_db

# ======================== SQLAlchemy 数据库模型 ========================


class GoogleVideoConfig(Base):
    __tablename__ = "google_video_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False)
    base_url = Column(String(500), default="")
    api_key = Column(Text)

    # 模型配置
    default_text_model = Column(String(100), default="veo3")
    default_image_model = Column(String(100), default="veo3-pro-frames")

    # 默认参数
    default_enhance_prompt = Column(Boolean, default=False)

    # 积分配置 - JSON存储，支持灵活配置
    model_credits_config = Column(JSON)

    # 系统配置
    max_concurrent_tasks = Column(Integer, default=3)
    task_timeout = Column(Integer, default=600000)  # 10分钟

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def get_config(cls):
        """获取谷歌视频配置"""
        with get_db() as db:
            return db.query(cls).filter(cls.id == 1).first()

    @classmethod
    def save_config(cls, config_data: dict):
        """保存谷歌视频配置"""
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

    def get_default_model_credits(self) -> dict:
        """获取默认的模型积分配置"""
        return {
            # 文生视频模型积分配置
            "veo3": 100,
            "veo3-fast": 80,
            "veo3-pro": 150,
            "veo3-pro-frames": 200,
            "veo2": 80,
            "veo2-fast": 60,
            "veo2-pro": 120,
            "veo3-fast-frames": 160,
            "veo2-fast-frames": 120,
            "veo2-fast-components": 100,
        }

    def get_credits_cost(self, model: str) -> int:
        """根据模型获取积分消耗"""
        if self.model_credits_config and model in self.model_credits_config:
            return int(self.model_credits_config[model])

        # 回退到默认配置
        default_credits = self.get_default_model_credits()
        return default_credits.get(model, 100)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "default_text_model": self.default_text_model,
            "default_image_model": self.default_image_model,
            "default_enhance_prompt": self.default_enhance_prompt,
            "model_credits_config": self.model_credits_config
            or self.get_default_model_credits(),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class GoogleVideoTask(Base):
    __tablename__ = "google_video_tasks"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    external_task_id = Column(String(100))  # 谷歌API返回的task_id

    # 任务类型和状态
    task_type = Column(String(20), nullable=False)  # 'text_to_video', 'image_to_video'
    status = Column(String(50), default="SUBMITTED")  # 对应API状态
    action = Column(String(50))  # API返回的action字段

    # 生成参数
    model = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    enhance_prompt = Column(Boolean, default=False)

    # 图生视频参数
    input_images = Column(JSON)  # 输入图片URL数组
    uploaded_images = Column(JSON)  # 上传到云存储的图片URL数组

    # 任务时间管理
    submit_time = Column(Integer)  # API返回的时间戳
    start_time = Column(Integer)
    finish_time = Column(Integer)
    progress = Column(String(20), default="0%")

    # 结果数据
    video_url = Column(Text)  # API返回的视频URL
    cloud_video_url = Column(Text)  # 云存储视频URL
    video_duration = Column(Float)  # 视频时长(秒)
    fail_reason = Column(Text)  # 失败原因

    # 积分管理
    credits_cost = Column(Integer, default=0)

    # 请求和响应数据存储
    request_data = Column(Text)
    response_data = Column(Text)

    # 云存储状态
    cloud_upload_status = Column(
        String(20), default="pending"
    )  # pending/uploaded/failed

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def create_task(
        cls,
        user_id: str,
        task_type: str,
        prompt: str,
        model: str,
        enhance_prompt: bool = False,
        credits_cost: int = 0,
        input_images: Optional[List[str]] = None,
        uploaded_images: Optional[List[str]] = None,
    ):
        """创建新任务"""
        task_id = str(uuid.uuid4())

        with get_db() as db:
            task = cls(
                id=task_id,
                user_id=user_id,
                task_type=task_type,
                prompt=prompt,
                model=model,
                enhance_prompt=enhance_prompt,
                credits_cost=credits_cost,
                input_images=input_images,
                uploaded_images=uploaded_images,
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

    def update_from_api_response(self, api_response):
        """从API响应更新任务信息"""
        with get_db() as db:
            # 检查api_response是否为字典类型
            if not isinstance(api_response, dict):
                # 如果不是字典，说明API调用失败，保存错误信息
                self.response_data = str(api_response)
                self.status = "FAILURE"
                self.fail_reason = f"API调用失败: {str(api_response)}"
                self.updated_at = datetime.now()
                db.merge(self)
                db.commit()
                return

            # 保存完整响应
            self.response_data = json.dumps(api_response, ensure_ascii=False)

            # 检查响应代码
            if api_response.get("code") == "error":
                # API返回错误，标记任务失败
                self.status = "FAILURE"
                self.fail_reason = api_response.get("message", "API调用失败")
                self.updated_at = datetime.now()
                db.merge(self)
                db.commit()
                return

            # 提取任务信息
            data = api_response.get("data")

            # 处理不同的数据格式
            if isinstance(data, str):
                # 创建任务时，data直接是task_id字符串
                if self.external_task_id is None:
                    self.external_task_id = data
                    self.status = "SUBMITTED"
                    self.action = "google-videos"
                    self.progress = "0%"
                    print(
                        f"🎬 【谷歌视频】任务创建成功，external_task_id: {self.external_task_id}"
                    )
            elif isinstance(data, dict):
                # 查询任务状态时，data是字典
                if self.external_task_id is None:
                    self.external_task_id = data.get("task_id")

                self.action = data.get("action", "google-videos")
                self.status = data.get("status", "SUBMITTED")
                self.progress = data.get("progress", "0%")

                # 更新时间戳
                if data.get("submit_time"):
                    self.submit_time = data["submit_time"]
                if data.get("start_time"):
                    self.start_time = data["start_time"]
                if data.get("finish_time"):
                    self.finish_time = data["finish_time"]

                # 处理结果数据 - 注意API文档中有嵌套的data结构
                inner_data = data.get("data", {})
                if isinstance(inner_data, dict):
                    if inner_data.get("video_url"):
                        self.video_url = inner_data["video_url"]
                elif data.get("video_url"):
                    self.video_url = data["video_url"]

                # 处理失败情况
                if self.status == "FAILURE":
                    self.fail_reason = data.get("fail_reason", "未知错误")
            else:
                # 如果data为None或其他类型，标记为失败
                self.status = "FAILURE"
                self.fail_reason = "API响应数据格式错误"
                print(f"🎬 【谷歌视频】数据格式错误: {data}")
                self.updated_at = datetime.now()
                db.merge(self)
                db.commit()
                return

            self.updated_at = datetime.now()
            db.merge(self)
            db.commit()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "external_task_id": self.external_task_id,
            "task_type": self.task_type,
            "status": self.status,
            "action": self.action,
            "model": self.model,
            "prompt": self.prompt,
            "enhance_prompt": self.enhance_prompt,
            "input_images": self.input_images,
            "uploaded_images": self.uploaded_images,
            "submit_time": self.submit_time,
            "start_time": self.start_time,
            "finish_time": self.finish_time,
            "progress": self.progress,
            "video_url": self.cloud_video_url or self.video_url,  # 优先返回云存储URL
            "video_duration": self.video_duration,
            "fail_reason": self.fail_reason,
            "credits_cost": self.credits_cost,
            "cloud_upload_status": self.cloud_upload_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class GoogleVideoCredit(Base):
    __tablename__ = "google_video_credits"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)  # 积分变化量（负数表示消耗）
    balance = Column(Integer, nullable=False)  # 操作后余额
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


def validate_image_to_video_request(model: str, images: List[str]) -> tuple[bool, str]:
    """验证图生视频请求的图片数量限制"""

    model_limits = {
        "veo3-pro-frames": {"max": 1, "type": "首帧"},
        "veo3-fast-frames": {"max": 1, "type": "首帧"},
        "veo2-fast-frames": {"max": 2, "type": "首尾帧"},
        "veo2-fast-components": {"max": 3, "type": "视频元素"},
    }

    if model not in model_limits:
        return False, f"不支持的图生视频模型: {model}"

    limit = model_limits[model]
    if len(images) > limit["max"]:
        return False, f"{model} 模型最多支持 {limit['max']} 张图片（{limit['type']}）"

    if len(images) == 0:
        return False, "图生视频必须提供至少一张图片"

    return True, ""


class GoogleVideoTextToVideoRequest(BaseModel):
    """谷歌视频文生视频请求"""

    prompt: str = Field(..., max_length=2500, description="提示词")
    model: str = Field("veo3", description="模型名称")
    enhance_prompt: bool = Field(False, description="是否优化提示词（中文转英文）")


class GoogleVideoImageToVideoRequest(BaseModel):
    """谷歌视频图生视频请求"""

    prompt: str = Field(..., max_length=2500, description="提示词")
    model: str = Field("veo3-pro-frames", description="模型名称")
    enhance_prompt: bool = Field(False, description="是否优化提示词")
    images: List[str] = Field(
        ..., min_items=1, max_items=3, description="输入图片URL或base64数组"
    )

    @validator("images")
    def validate_images_for_model(cls, v, values):
        """验证图片数量符合模型限制"""
        model = values.get("model", "")
        is_valid, error_msg = validate_image_to_video_request(model, v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class GoogleVideoConfigForm(BaseModel):
    """谷歌视频配置表单"""

    enabled: bool = Field(False, description="启用状态")
    base_url: str = Field("", description="API地址")
    api_key: str = Field("", description="API密钥")
    default_text_model: str = Field("veo3", description="默认文生视频模型")
    default_image_model: str = Field("veo3-pro-frames", description="默认图生视频模型")
    default_enhance_prompt: bool = Field(False, description="默认启用提示词优化")
    model_credits_config: Dict[str, int] = Field(
        default_factory=dict, description="模型积分配置"
    )
    max_concurrent_tasks: int = Field(3, description="最大并发任务数")
    task_timeout: int = Field(600000, description="任务超时时间(毫秒)")
