# 谷歌视频生成功能完整集成方案

## 📋 项目概述

基于现有的Kling和Jimeng视频功能架构，为项目添加谷歌视频生成服务。命名统一为"谷歌视频"，支持文生视频和图生视频两种模式。

## 🔧 技术架构

### API接口完整性

- ✅ **提交任务**: `POST /BASE_URL/google/v1/models/veo/videos`
- ✅ **查询结果**: `GET /BASE_URL/google/v1/tasks/{task_id}`
- ✅ **任务状态**: NOT_START → SUBMITTED → IN_PROGRESS → SUCCESS/FAILURE

### 支持的模型

#### 文生视频模型 (10个)

- veo3, veo3-fast, veo3-pro, veo3-pro-frames
- veo2, veo2-fast, veo2-fast-frames, veo2-fast-components, veo2-pro
- veo3-fast-frames

#### 图生视频模型详细规格 (4个)

| 模型                     | 最大图片数 | 图片类型 | 描述                                                |
| ------------------------ | ---------- | -------- | --------------------------------------------------- |
| **veo3-pro-frames**      | 1张        | 首帧     | 支持图生视频的专业版本，最多支持一个首帧            |
| **veo3-fast-frames**     | 1张        | 首帧     | 快速图生视频，最多支持一个首帧                      |
| **veo2-fast-frames**     | 2张        | 首尾帧   | 经典快速图生视频，最多支持两个，分别是首尾帧        |
| **veo2-fast-components** | 3张        | 视频元素 | 组件化快速生成，最多支持3个，此时图片为视频中的元素 |

## 📦 开发计划

### Phase 1: 后端数据模型 (2-3小时)

#### A) 数据库模型 (`backend/open_webui/models/google_video.py`)

```python
"""
谷歌视频生成数据模型
基于谷歌Veo API规范的完整数据模型定义
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
            "model_credits_config": self.model_credits_config or self.get_default_model_credits(),
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
    cloud_upload_status = Column(String(20), default="pending")  # pending/uploaded/failed

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

    def update_from_api_response(self, api_response: dict):
        """从API响应更新任务信息"""
        with get_db() as db:
            # 保存完整响应
            self.response_data = json.dumps(api_response, ensure_ascii=False)

            # 提取任务信息
            data = api_response.get("data", {})

            # 更新基本信息
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

            # 处理结果数据
            if data.get("video_url"):
                self.video_url = data["video_url"]

            # 处理失败情况
            if self.status == "FAILURE":
                self.fail_reason = data.get("fail_reason", "未知错误")

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
    images: List[str] = Field(..., min_items=1, max_items=3, description="输入图片URL或base64数组")

    @validator('images')
    def validate_images_for_model(cls, v, values):
        """验证图片数量符合模型限制"""
        model = values.get('model', '')
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
    model_credits_config: Dict[str, int] = Field(default_factory=dict, description="模型积分配置")
    max_concurrent_tasks: int = Field(3, description="最大并发任务数")
    task_timeout: int = Field(600000, description="任务超时时间(毫秒)")
```

#### B) 数据库迁移文件 (`backend/open_webui/migrations/versions/xxx_add_google_video_tables.py`)

```python
"""add_google_video_tables

Revision ID: google_video_001
Revises: merge_heads_final
Create Date: 2025-08-20 xx:xx:xx.xxxxxx
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = "google_video_001"
down_revision: Union[str, None] = "merge_heads_final"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级：创建谷歌视频相关表"""

    # 1. 创建 google_video_config 表
    op.create_table(
        "google_video_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=True, default=False),
        sa.Column("base_url", sa.String(500), nullable=True, default=""),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("default_text_model", sa.String(100), nullable=True, default="veo3"),
        sa.Column("default_image_model", sa.String(100), nullable=True, default="veo3-pro-frames"),
        sa.Column("default_enhance_prompt", sa.Boolean(), nullable=True, default=False),
        sa.Column("model_credits_config", sa.JSON(), nullable=True),
        sa.Column("max_concurrent_tasks", sa.Integer(), nullable=True, default=3),
        sa.Column("task_timeout", sa.Integer(), nullable=True, default=600000),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. 创建 google_video_tasks 表
    op.create_table(
        "google_video_tasks",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=False),
        sa.Column("external_task_id", sa.String(100), nullable=True),
        sa.Column("task_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(50), nullable=True, default="SUBMITTED"),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("enhance_prompt", sa.Boolean(), nullable=True, default=False),
        sa.Column("input_images", sa.JSON(), nullable=True),
        sa.Column("uploaded_images", sa.JSON(), nullable=True),
        sa.Column("submit_time", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.Integer(), nullable=True),
        sa.Column("finish_time", sa.Integer(), nullable=True),
        sa.Column("progress", sa.String(20), nullable=True, default="0%"),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("cloud_video_url", sa.Text(), nullable=True),
        sa.Column("video_duration", sa.Float(), nullable=True),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("credits_cost", sa.Integer(), nullable=True, default=0),
        sa.Column("request_data", sa.Text(), nullable=True),
        sa.Column("response_data", sa.Text(), nullable=True),
        sa.Column("cloud_upload_status", sa.String(20), nullable=True, default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. 创建 google_video_credits 表
    op.create_table(
        "google_video_credits",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("task_id", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. 创建索引优化查询性能
    op.create_index("idx_google_video_tasks_user_id", "google_video_tasks", ["user_id"])
    op.create_index("idx_google_video_tasks_status", "google_video_tasks", ["status"])
    op.create_index("idx_google_video_tasks_external_id", "google_video_tasks", ["external_task_id"])
    op.create_index("idx_google_video_credits_user_id", "google_video_credits", ["user_id"])


def downgrade() -> None:
    """降级：删除谷歌视频相关表（生产环境不建议执行）"""

    # 删除索引
    op.drop_index("idx_google_video_credits_user_id", "google_video_credits")
    op.drop_index("idx_google_video_tasks_external_id", "google_video_tasks")
    op.drop_index("idx_google_video_tasks_status", "google_video_tasks")
    op.drop_index("idx_google_video_tasks_user_id", "google_video_tasks")

    # 删除表
    op.drop_table("google_video_credits")
    op.drop_table("google_video_tasks")
    op.drop_table("google_video_config")
```

### Phase 2: API客户端和工具 (3-4小时)

#### A) API客户端 (`backend/open_webui/utils/google_video.py`)

```python
"""
谷歌视频生成工具类
包含API客户端、积分管理、任务处理等工具
"""

import httpx
import asyncio
import json
import base64
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from open_webui.models.google_video import (
    GoogleVideoConfig,
    GoogleVideoTask,
    GoogleVideoTextToVideoRequest,
    GoogleVideoImageToVideoRequest
)


class GoogleVideoApiClient:
    """谷歌视频API客户端"""

    def __init__(self, config: GoogleVideoConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def submit_text_to_video(self, request: GoogleVideoTextToVideoRequest) -> dict:
        """提交文生视频任务"""
        url = f"{self.base_url}/google/v1/models/veo/videos"

        # 构建请求数据
        request_data = {
            "prompt": request.prompt.strip(),
            "model": request.model,
            "enhance_prompt": request.enhance_prompt,
        }

        print(f"🎬 【谷歌视频API】文生视频请求URL: {url}")
        print(f"🎬 【谷歌视频API】请求参数: {json.dumps(request_data, ensure_ascii=False)}")

        return await self._make_request("POST", url, request_data)

    async def submit_image_to_video(self, request: GoogleVideoImageToVideoRequest) -> dict:
        """提交图生视频任务"""
        url = f"{self.base_url}/google/v1/models/veo/videos"

        # 构建请求数据
        request_data = {
            "prompt": request.prompt.strip(),
            "model": request.model,
            "enhance_prompt": request.enhance_prompt,
            "images": request.images,  # URL或base64数组
        }

        print(f"🎬 【谷歌视频API】图生视频请求URL: {url}")
        print(f"🎬 【谷歌视频API】请求参数: {json.dumps(request_data, ensure_ascii=False)}")

        return await self._make_request("POST", url, request_data)

    async def get_task_status(self, task_id: str) -> dict:
        """查询任务状态"""
        url = f"{self.base_url}/google/v1/tasks/{task_id}"

        print(f"🎬 【谷歌视频API】查询任务状态URL: {url}")
        return await self._make_request("GET", url)

    async def _make_request(self, method: str, url: str, data: dict = None) -> dict:
        """统一HTTP请求处理"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"🎬 【谷歌视频API】开始发送 {method} 请求到: {url}")

                if method == "GET":
                    response = await client.get(url, headers=self.headers)
                else:
                    response = await client.post(url, json=data, headers=self.headers)

                print(f"🎬 【谷歌视频API】响应状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"🎬 【谷歌视频API】响应成功: {json.dumps(result, ensure_ascii=False)}")
                    return result
                else:
                    error_text = response.text
                    print(f"🎬 【谷歌视频API】响应失败: {error_text}")
                    raise Exception(f"API请求失败: {response.status_code} - {error_text}")

        except Exception as e:
            print(f"🎬 【谷歌视频API】请求异常: {str(e)}")
            raise e

    async def test_connection(self) -> bool:
        """测试API连接"""
        try:
            # 尝试提交一个简单的测试任务来验证连接
            test_request = GoogleVideoTextToVideoRequest(
                prompt="test connection",
                model="veo3-fast",
                enhance_prompt=False
            )

            await self.submit_text_to_video(test_request)
            return True
        except Exception as e:
            print(f"🎬 【谷歌视频API】连接测试失败: {str(e)}")
            return False


# ======================== 积分管理工具 ========================

def get_user_google_video_credits(user_id: str) -> int:
    """获取用户谷歌视频积分余额"""
    # 这里需要集成现有的积分系统
    # 可以复用Kling的积分管理逻辑
    from open_webui.utils.kling import get_user_credit_balance
    return get_user_credit_balance(user_id)


def deduct_user_google_video_credits(user_id: str, amount: int, task_id: str, reason: str) -> bool:
    """扣除用户谷歌视频积分"""
    from open_webui.utils.kling import deduct_user_credits
    return deduct_user_credits(user_id, amount, task_id, reason)


def validate_user_google_video_credits(user_id: str, required_credits: int) -> bool:
    """验证用户积分是否足够"""
    current_credits = get_user_google_video_credits(user_id)
    return current_credits >= required_credits


# ======================== 模型验证工具 ========================

def validate_image_to_video_request(model: str, images: List[str]) -> tuple[bool, str]:
    """验证图生视频请求的图片数量限制"""

    model_limits = {
        "veo3-pro-frames": {"max": 1, "type": "首帧"},
        "veo3-fast-frames": {"max": 1, "type": "首帧"},
        "veo2-fast-frames": {"max": 2, "type": "首尾帧"},
        "veo2-fast-components": {"max": 3, "type": "视频元素"}
    }

    if model not in model_limits:
        return False, f"不支持的图生视频模型: {model}"

    limit = model_limits[model]
    if len(images) > limit["max"]:
        return False, f"{model} 模型最多支持 {limit['max']} 张图片（{limit['type']}）"

    if len(images) == 0:
        return False, "图生视频必须提供至少一张图片"

    return True, ""


# ======================== 任务处理工具 ========================

async def process_google_video_task_polling(task: GoogleVideoTask, client: GoogleVideoApiClient):
    """轮询任务状态直到完成"""
    max_attempts = 120  # 最多轮询2小时（每分钟一次）
    poll_interval = 60  # 60秒轮询一次

    for attempt in range(max_attempts):
        try:
            # 查询任务状态
            response = await client.get_task_status(task.external_task_id)

            if response.get("code") == "success":
                # 更新任务信息
                task.update_from_api_response(response)

                # 检查任务是否完成
                status = response.get("data", {}).get("status", "")
                if status in ["SUCCESS", "FAILURE"]:
                    print(f"🎬 【谷歌视频】任务 {task.id} 已完成，状态: {status}")

                    # 如果成功，触发云存储上传
                    if status == "SUCCESS" and task.video_url:
                        await upload_video_to_cloud_storage(task)

                    break
                else:
                    print(f"🎬 【谷歌视频】任务 {task.id} 进行中，状态: {status}, 进度: {task.progress}")
            else:
                print(f"🎬 【谷歌视频】查询任务 {task.id} 失败: {response}")

        except Exception as e:
            print(f"🎬 【谷歌视频】轮询任务 {task.id} 异常: {str(e)}")

        # 等待下次轮询
        if attempt < max_attempts - 1:
            await asyncio.sleep(poll_interval)

    else:
        # 超时处理
        print(f"🎬 【谷歌视频】任务 {task.id} 轮询超时")
        task.status = "FAILURE"
        task.fail_reason = "任务轮询超时"
        with get_db() as db:
            db.merge(task)
            db.commit()


async def upload_video_to_cloud_storage(task: GoogleVideoTask):
    """上传视频到云存储"""
    try:
        from open_webui.services.file_manager import get_file_manager

        file_manager = get_file_manager()

        # 上传视频到云存储
        cloud_url = await file_manager.upload_url_to_cloud(
            url=task.video_url,
            user_id=task.user_id,
            source_type="google_video",
            source_task_id=task.id,
            file_type="video"
        )

        if cloud_url:
            task.cloud_video_url = cloud_url
            task.cloud_upload_status = "uploaded"
            print(f"🎬 【谷歌视频】任务 {task.id} 视频已上传到云存储: {cloud_url}")
        else:
            task.cloud_upload_status = "failed"
            print(f"🎬 【谷歌视频】任务 {task.id} 视频上传到云存储失败")

        with get_db() as db:
            db.merge(task)
            db.commit()

    except Exception as e:
        print(f"🎬 【谷歌视频】上传视频到云存储异常: {str(e)}")
        task.cloud_upload_status = "failed"
        with get_db() as db:
            db.merge(task)
            db.commit()
```

### Phase 3: API路由开发 (3-4小时)

#### A) API路由 (`backend/open_webui/routers/google_video.py`)

```python
"""
谷歌视频生成 API 路由
实现完整的谷歌视频生成功能，包括文生视频、图生视频等
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import uuid
from datetime import datetime

from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.google_video import (
    GoogleVideoConfig,
    GoogleVideoTask,
    GoogleVideoCredit,
    GoogleVideoConfigForm,
    GoogleVideoTextToVideoRequest,
    GoogleVideoImageToVideoRequest,
)
from open_webui.utils.google_video import (
    GoogleVideoApiClient,
    get_user_google_video_credits,
    deduct_user_google_video_credits,
    validate_user_google_video_credits,
    process_google_video_task_polling,
)
from open_webui.services.file_manager import get_file_manager

router = APIRouter(prefix="/google-video", tags=["google_video"])

# 全局变量存储客户端
google_video_config = None
google_video_client = None


def get_google_video_client():
    """获取谷歌视频API客户端"""
    global google_video_client, google_video_config
    if not google_video_client or not google_video_config:
        config = GoogleVideoConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="谷歌视频服务未配置或已禁用")
        google_video_client = GoogleVideoApiClient(config)
        google_video_config = config
    return google_video_client


# ======================== 配置管理 ========================

@router.get("/config")
async def get_google_video_config(user=Depends(get_admin_user)):
    """获取谷歌视频配置 - 管理员专用"""
    config = GoogleVideoConfig.get_config()
    if not config:
        # 返回默认配置
        default_config = GoogleVideoConfig()
        return {
            "enabled": False,
            "base_url": "",
            "api_key": "",
            "default_text_model": "veo3",
            "default_image_model": "veo3-pro-frames",
            "default_enhance_prompt": False,
            "model_credits_config": default_config.get_default_model_credits(),
            "max_concurrent_tasks": 3,
            "task_timeout": 600000,
        }
    return config.to_dict()


@router.post("/config")
async def save_google_video_config(
    config_form: GoogleVideoConfigForm, user=Depends(get_admin_user)
):
    """保存谷歌视频配置 - 管理员专用"""
    try:
        # 清除全局客户端缓存
        global google_video_client, google_video_config
        google_video_client = None
        google_video_config = None

        # 保存配置
        config = GoogleVideoConfig.save_config(config_form.dict())
        return {"success": True, "message": "配置保存成功", "config": config.to_dict()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/config/user")
async def get_google_video_user_config(user=Depends(get_verified_user)):
    """获取谷歌视频用户配置 - 只返回用户需要的配置信息"""
    config = GoogleVideoConfig.get_config()
    if not config:
        return {
            "enabled": False,
            "default_text_model": "veo3",
            "default_image_model": "veo3-pro-frames",
            "default_enhance_prompt": False,
        }

    return {
        "enabled": config.enabled,
        "default_text_model": config.default_text_model,
        "default_image_model": config.default_image_model,
        "default_enhance_prompt": config.default_enhance_prompt,
        "model_credits_config": config.model_credits_config or config.get_default_model_credits(),
    }


@router.post("/test-connection")
async def test_google_video_connection(user=Depends(get_admin_user)):
    """测试谷歌视频API连接"""
    try:
        client = get_google_video_client()
        success = await client.test_connection()

        if success:
            return {"success": True, "message": "连接测试成功"}
        else:
            return {"success": False, "message": "连接测试失败"}

    except Exception as e:
        return {"success": False, "message": f"连接测试失败: {str(e)}"}


# ======================== 模型管理 ========================

@router.get("/models")
async def get_google_video_models(user=Depends(get_verified_user)):
    """获取支持的谷歌视频模型列表"""
    return {
        "text_to_video_models": [
            {"id": "veo3", "name": "Veo 3.0", "description": "最新版本，高质量输出"},
            {"id": "veo3-fast", "name": "Veo 3.0 Fast", "description": "快速生成版本"},
            {"id": "veo3-pro", "name": "Veo 3.0 Pro", "description": "专业版本，最高质量"},
            {"id": "veo3-pro-frames", "name": "Veo 3.0 Pro Frames", "description": "支持图生视频的专业版本"},
            {"id": "veo2", "name": "Veo 2.0", "description": "经典版本"},
            {"id": "veo2-fast", "name": "Veo 2.0 Fast", "description": "快速版本"},
            {"id": "veo2-pro", "name": "Veo 2.0 Pro", "description": "专业版本"},
            {"id": "veo3-fast-frames", "name": "Veo 3.0 Fast Frames", "description": "快速帧处理版本"},
        ],
        "image_to_video_models": [
            {"id": "veo3-pro-frames", "name": "Veo 3.0 Pro Frames", "description": "支持图生视频的专业版本", "maxImages": 1, "imageType": "首帧"},
            {"id": "veo3-fast-frames", "name": "Veo 3.0 Fast Frames", "description": "快速图生视频", "maxImages": 1, "imageType": "首帧"},
            {"id": "veo2-fast-frames", "name": "Veo 2.0 Fast Frames", "description": "经典快速图生视频", "maxImages": 2, "imageType": "首尾帧"},
            {"id": "veo2-fast-components", "name": "Veo 2.0 Fast Components", "description": "组件化快速生成", "maxImages": 3, "imageType": "视频元素"},
        ]
    }


# ======================== 任务管理 ========================

@router.post("/text-to-video")
async def create_text_to_video_task(
    request: GoogleVideoTextToVideoRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """创建文生视频任务"""
    try:
        # 获取配置和客户端
        config = GoogleVideoConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="谷歌视频服务未启用")

        client = get_google_video_client()

        # 计算积分消耗
        credits_cost = config.get_credits_cost(request.model)

        # 验证用户积分
        if not validate_user_google_video_credits(user.id, credits_cost):
            current_credits = get_user_google_video_credits(user.id)
            raise HTTPException(
                status_code=400,
                detail=f"积分不足。当前积分: {current_credits}，需要积分: {credits_cost}",
            )

        # 扣除积分
        if not deduct_user_google_video_credits(
            user.id, credits_cost, "", "谷歌视频文生视频任务"
        ):
            raise HTTPException(status_code=400, detail="积分扣除失败")

        # 创建数据库任务记录
        task = GoogleVideoTask.create_task(
            user_id=user.id,
            task_type="text_to_video",
            prompt=request.prompt,
            model=request.model,
            enhance_prompt=request.enhance_prompt,
            credits_cost=credits_cost,
        )

        # 提交任务到API
        try:
            api_response = await client.submit_text_to_video(request)

            if api_response.get("code") == "success":
                # 更新任务信息
                task.update_from_api_response(api_response)

                # 启动后台轮询任务
                background_tasks.add_task(process_google_video_task_polling, task, client)

                return {"success": True, "task": task.to_dict()}
            else:
                raise Exception(f"API返回错误: {api_response}")

        except Exception as e:
            # API调用失败，标记任务失败
            task.status = "FAILURE"
            task.fail_reason = str(e)
            with get_db() as db:
                db.merge(task)
                db.commit()
            raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/image-to-video")
async def create_image_to_video_task(
    request: GoogleVideoImageToVideoRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """创建图生视频任务"""
    try:
        # 验证图片数量限制
        is_valid, error_msg = validate_image_to_video_request(request.model, request.images)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # 获取配置和客户端
        config = GoogleVideoConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="谷歌视频服务未启用")

        client = get_google_video_client()

        # 计算积分消耗
        credits_cost = config.get_credits_cost(request.model)

        # 验证用户积分
        if not validate_user_google_video_credits(user.id, credits_cost):
            current_credits = get_user_google_video_credits(user.id)
            raise HTTPException(
                status_code=400,
                detail=f"积分不足。当前积分: {current_credits}，需要积分: {credits_cost}",
            )

        # 扣除积分
        if not deduct_user_google_video_credits(
            user.id, credits_cost, "", "谷歌视频图生视频任务"
        ):
            raise HTTPException(status_code=400, detail="积分扣除失败")

        # 创建数据库任务记录
        task = GoogleVideoTask.create_task(
            user_id=user.id,
            task_type="image_to_video",
            prompt=request.prompt,
            model=request.model,
            enhance_prompt=request.enhance_prompt,
            credits_cost=credits_cost,
            input_images=request.images,
        )

        # 提交任务到API
        try:
            api_response = await client.submit_image_to_video(request)

            if api_response.get("code") == "success":
                # 更新任务信息
                task.update_from_api_response(api_response)

                # 启动后台轮询任务
                background_tasks.add_task(process_google_video_task_polling, task, client)

                return {"success": True, "task": task.to_dict()}
            else:
                raise Exception(f"API返回错误: {api_response}")

        except Exception as e:
            # API调用失败，标记任务失败
            task.status = "FAILURE"
            task.fail_reason = str(e)
            with get_db() as db:
                db.merge(task)
                db.commit()
            raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/task/{task_id}")
async def get_task_status(task_id: str, user=Depends(get_verified_user)):
    """获取任务状态"""
    try:
        task = GoogleVideoTask.get_task_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问此任务")

        return {"success": True, "task": task.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_task(task_id: str, user=Depends(get_verified_user)):
    """删除任务"""
    try:
        task = GoogleVideoTask.get_task_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问此任务")

        # 删除任务记录
        with get_db() as db:
            db.delete(task)
            db.commit()

        return {"success": True, "message": "任务已删除"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


@router.get("/history")
async def get_user_task_history(
    page: int = 1,
    limit: int = 20,
    user=Depends(get_verified_user),
):
    """获取用户任务历史记录"""
    try:
        tasks = GoogleVideoTask.get_user_tasks(user.id, page, limit)
        task_list = [task.to_dict() for task in tasks]

        return {
            "success": True,
            "tasks": task_list,
            "page": page,
            "limit": limit,
            "total": len(task_list),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


# ======================== 文件管理 ========================

@router.post("/upload-image")
async def upload_image_for_video(
    file: UploadFile = File(...),
    user=Depends(get_verified_user),
):
    """上传图片用于图生视频"""
    try:
        # 验证文件类型
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只支持图片文件")

        # 验证文件大小 (最大10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

        # 上传到云存储
        file_manager = get_file_manager()

        cloud_url = await file_manager.upload_file_content(
            file_content=file_content,
            filename=file.filename,
            user_id=user.id,
            source_type="google_video_input",
            file_type="image"
        )

        if cloud_url:
            return {"success": True, "url": cloud_url}
        else:
            raise HTTPException(status_code=500, detail="图片上传失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传图片失败: {str(e)}")


# ======================== 积分管理 ========================

@router.get("/credits")
async def get_user_credits(user=Depends(get_verified_user)):
    """获取用户谷歌视频积分余额"""
    try:
        credits = get_user_google_video_credits(user.id)
        return {"success": True, "credits": credits}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取积分失败: {str(e)}")


# ======================== 服务监控 ========================

@router.get("/health")
async def health_check():
    """服务健康检查"""
    try:
        config = GoogleVideoConfig.get_config()

        return {
            "success": True,
            "service": "google_video",
            "status": "healthy",
            "enabled": config.enabled if config else False,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "service": "google_video",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
```

### Phase 4: 前端开发 (4-5小时)

#### A) 管理员配置界面 (`src/lib/components/admin/Settings/GoogleVideo.svelte`)

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import {
		getGoogleVideoConfig,
		saveGoogleVideoConfig,
		testGoogleVideoConnection,
		type GoogleVideoConfig
	} from '$lib/apis/google-video';

	let loading = false;
	let testing = false;
	let config: GoogleVideoConfig = {
		enabled: false,
		base_url: '',
		api_key: '',
		default_text_model: 'veo3',
		default_image_model: 'veo3-pro-frames',
		default_enhance_prompt: false,
		model_credits_config: {},
		max_concurrent_tasks: 3,
		task_timeout: 600000
	};

	// 谷歌视频支持的模型
	const GOOGLE_VIDEO_MODELS = {
		text_to_video: [
			{ id: 'veo3', name: 'Veo 3.0', description: '最新版本，高质量输出' },
			{ id: 'veo3-fast', name: 'Veo 3.0 Fast', description: '快速生成版本' },
			{ id: 'veo3-pro', name: 'Veo 3.0 Pro', description: '专业版本，最高质量' },
			{ id: 'veo2', name: 'Veo 2.0', description: '经典版本' },
			{ id: 'veo2-fast', name: 'Veo 2.0 Fast', description: '快速版本' },
			{ id: 'veo2-pro', name: 'Veo 2.0 Pro', description: '专业版本' }
		],
		image_to_video: [
			{
				id: 'veo3-pro-frames',
				name: 'Veo 3.0 Pro Frames',
				description: '支持图生视频的专业版本',
				maxImages: 1,
				imageType: '首帧'
			},
			{
				id: 'veo3-fast-frames',
				name: 'Veo 3.0 Fast Frames',
				description: '快速图生视频',
				maxImages: 1,
				imageType: '首帧'
			},
			{
				id: 'veo2-fast-frames',
				name: 'Veo 2.0 Fast Frames',
				description: '经典快速图生视频',
				maxImages: 2,
				imageType: '首尾帧'
			},
			{
				id: 'veo2-fast-components',
				name: 'Veo 2.0 Fast Components',
				description: '组件化快速生成',
				maxImages: 3,
				imageType: '视频元素'
			}
		]
	};

	function getDefaultModelCredits(): Record<string, number> {
		return {
			veo3: 100,
			'veo3-fast': 80,
			'veo3-pro': 150,
			'veo3-pro-frames': 200,
			veo2: 80,
			'veo2-fast': 60,
			'veo2-pro': 120,
			'veo3-fast-frames': 160,
			'veo2-fast-frames': 120,
			'veo2-fast-components': 100
		};
	}

	onMount(async () => {
		await loadConfig();
	});

	const loadConfig = async () => {
		try {
			loading = true;
			const response = await getGoogleVideoConfig();
			config = response;

			// 确保积分配置存在
			if (!config.model_credits_config || Object.keys(config.model_credits_config).length === 0) {
				config.model_credits_config = getDefaultModelCredits();
			}
		} catch (error) {
			console.error('加载配置失败:', error);
			toast.error('加载配置失败');
		} finally {
			loading = false;
		}
	};

	const handleSaveConfig = async () => {
		try {
			loading = true;
			await saveGoogleVideoConfig(config);
			toast.success('配置保存成功');
		} catch (error) {
			console.error('保存配置失败:', error);
			toast.error('保存配置失败');
		} finally {
			loading = false;
		}
	};

	const handleTestConnection = async () => {
		if (!config.base_url || !config.api_key) {
			toast.error('请先填写API地址和密钥');
			return;
		}

		try {
			testing = true;
			const response = await testGoogleVideoConnection();

			if (response.success) {
				toast.success('连接测试成功');
			} else {
				toast.error(`连接测试失败: ${response.message}`);
			}
		} catch (error) {
			console.error('测试连接失败:', error);
			toast.error('测试连接失败');
		} finally {
			testing = false;
		}
	};
</script>

<div class="flex flex-col h-full justify-between space-y-6">
	<div class="space-y-6">
		<!-- 服务状态 -->
		<div class="flex items-center justify-between">
			<div>
				<h2 class="text-xl font-semibold">谷歌视频配置</h2>
				<p class="text-sm text-gray-600 dark:text-gray-400">
					配置谷歌Veo视频生成服务，支持文生视频和图生视频
				</p>
			</div>
			<div class="flex items-center space-x-2">
				<div class="w-3 h-3 rounded-full {config.enabled ? 'bg-green-500' : 'bg-red-500'}"></div>
				<span class="text-sm {config.enabled ? 'text-green-600' : 'text-red-600'}">
					{config.enabled ? '已启用' : '未启用'}
				</span>
			</div>
		</div>

		<!-- 基本配置 -->
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
			<h3 class="text-lg font-medium">基本配置</h3>

			<!-- 启用开关 -->
			<div class="flex items-center space-x-3">
				<input
					type="checkbox"
					id="enabled"
					bind:checked={config.enabled}
					class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
				/>
				<label for="enabled" class="text-sm font-medium">启用谷歌视频生成服务</label>
			</div>

			<!-- API配置 -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div>
					<label for="base_url" class="block text-sm font-medium mb-1">API Base URL</label>
					<input
						type="text"
						id="base_url"
						bind:value={config.base_url}
						placeholder="https://api.your-provider.com"
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>

				<div>
					<label for="api_key" class="block text-sm font-medium mb-1">API Key</label>
					<input
						type="password"
						id="api_key"
						bind:value={config.api_key}
						placeholder="Bearer token"
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>
			</div>
		</div>

		<!-- 模型配置 -->
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
			<h3 class="text-lg font-medium">模型配置</h3>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div>
					<label for="default_text_model" class="block text-sm font-medium mb-1"
						>默认文生视频模型</label
					>
					<select
						id="default_text_model"
						bind:value={config.default_text_model}
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						{#each GOOGLE_VIDEO_MODELS.text_to_video as model}
							<option value={model.id}>{model.name} - {model.description}</option>
						{/each}
					</select>
				</div>

				<div>
					<label for="default_image_model" class="block text-sm font-medium mb-1"
						>默认图生视频模型</label
					>
					<select
						id="default_image_model"
						bind:value={config.default_image_model}
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						{#each GOOGLE_VIDEO_MODELS.image_to_video as model}
							<option value={model.id}>{model.name} - {model.description}</option>
						{/each}
					</select>
				</div>
			</div>

			<!-- 提示词增强 -->
			<div class="flex items-center space-x-3">
				<input
					type="checkbox"
					id="default_enhance_prompt"
					bind:checked={config.default_enhance_prompt}
					class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
				/>
				<label for="default_enhance_prompt" class="text-sm font-medium">
					默认启用提示词增强（中文转英文）
				</label>
			</div>
		</div>

		<!-- 积分配置 -->
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
			<h3 class="text-lg font-medium">积分配置</h3>
			<p class="text-sm text-gray-600 dark:text-gray-400">设置不同模型的积分消耗</p>

			<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
				{#each Object.keys(config.model_credits_config) as model}
					<div>
						<label for="credits_{model}" class="block text-xs font-medium mb-1">{model}</label>
						<input
							type="number"
							id="credits_{model}"
							bind:value={config.model_credits_config[model]}
							min="1"
							step="1"
							class="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
						/>
					</div>
				{/each}
			</div>
		</div>

		<!-- 系统配置 -->
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
			<h3 class="text-lg font-medium">系统配置</h3>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div>
					<label for="max_concurrent_tasks" class="block text-sm font-medium mb-1"
						>最大并发任务数</label
					>
					<input
						type="number"
						id="max_concurrent_tasks"
						bind:value={config.max_concurrent_tasks}
						min="1"
						max="10"
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>

				<div>
					<label for="task_timeout" class="block text-sm font-medium mb-1"
						>任务超时时间（毫秒）</label
					>
					<input
						type="number"
						id="task_timeout"
						bind:value={config.task_timeout}
						min="60000"
						step="60000"
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					<p class="text-xs text-gray-500 mt-1">
						当前设置: {Math.floor(config.task_timeout / 60000)} 分钟
					</p>
				</div>
			</div>
		</div>

		<!-- 图生视频模型限制提示 -->
		<div class="bg-blue-50 dark:bg-blue-900 rounded-lg p-4 space-y-4">
			<h3 class="text-lg font-medium">图生视频模型限制</h3>
			<p class="text-sm text-gray-600 dark:text-gray-400">不同模型支持的图片数量和类型有所不同</p>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				{#each GOOGLE_VIDEO_MODELS.image_to_video as model}
					<div class="bg-white dark:bg-gray-800 rounded border p-3">
						<div class="font-medium text-sm">{model.name}</div>
						<div class="text-xs text-gray-500 mt-1">{model.description}</div>
						<div class="text-xs text-blue-600 dark:text-blue-400 mt-2">
							最多 {model.maxImages} 张图片（{model.imageType}）
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>

	<!-- 操作按钮 -->
	<div class="flex flex-wrap gap-2">
		<button
			type="button"
			on:click={handleSaveConfig}
			disabled={loading}
			class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
		>
			{#if loading}
				<div class="inline-flex items-center">
					<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					保存中...
				</div>
			{:else}
				保存配置
			{/if}
		</button>

		<button
			type="button"
			on:click={handleTestConnection}
			disabled={testing}
			class="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
		>
			{#if testing}
				<div class="inline-flex items-center">
					<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					测试中...
				</div>
			{:else}
				测试连接
			{/if}
		</button>

		<button
			type="button"
			on:click={loadConfig}
			disabled={loading}
			class="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50"
		>
			重新加载
		</button>
	</div>
</div>

<style>
	/* 响应式样式调整 */
	@media (max-width: 640px) {
		.grid {
			grid-template-columns: 1fr;
		}
	}
</style>
```

#### B) 前端API封装 (`src/lib/apis/google-video/index.ts`)

```typescript
// ======================== 谷歌视频前端API接口 ========================

import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface GoogleVideoConfig {
	enabled: boolean;
	base_url: string;
	api_key: string;
	default_text_model: string;
	default_image_model: string;
	default_enhance_prompt: boolean;
	model_credits_config: Record<string, number>;
	max_concurrent_tasks: number;
	task_timeout: number;
}

export interface GoogleVideoTask {
	id: string;
	user_id: string;
	external_task_id?: string;
	task_type: 'text_to_video' | 'image_to_video';
	status: 'SUBMITTED' | 'NOT_START' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILURE';
	action?: string;
	model: string;
	prompt: string;
	enhance_prompt: boolean;
	input_images?: string[];
	uploaded_images?: string[];
	submit_time?: number;
	start_time?: number;
	finish_time?: number;
	progress: string;
	video_url?: string;
	video_duration?: number;
	fail_reason?: string;
	credits_cost: number;
	cloud_upload_status: string;
	created_at: string;
	updated_at: string;
}

export interface GoogleVideoTextToVideoRequest {
	prompt: string;
	model: string;
	enhance_prompt?: boolean;
}

export interface GoogleVideoImageToVideoRequest {
	prompt: string;
	model: string;
	enhance_prompt?: boolean;
	images: string[];
}

export interface GoogleVideoModel {
	id: string;
	name: string;
	description: string;
	maxImages?: number; // 图生视频模型的最大图片数
	imageType?: string; // 图片类型描述
}

export interface GoogleVideoModels {
	text_to_video_models: GoogleVideoModel[];
	image_to_video_models: GoogleVideoModel[];
}

// ======================== API函数 ========================

export async function getGoogleVideoConfig(token: string = ''): Promise<GoogleVideoConfig> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/config`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function saveGoogleVideoConfig(
	config: GoogleVideoConfig,
	token: string = ''
): Promise<any> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/config`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(config)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoUserConfig(
	token: string = ''
): Promise<Partial<GoogleVideoConfig>> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/config/user`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function testGoogleVideoConnection(
	token: string = ''
): Promise<{ success: boolean; message: string }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/test-connection`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return { success: false, message: error };
		});

	if (error && !res) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoModels(token: string = ''): Promise<GoogleVideoModels> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/models`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function submitGoogleVideoTextToVideo(
	request: GoogleVideoTextToVideoRequest,
	token: string = ''
): Promise<{ success: boolean; task: GoogleVideoTask }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/text-to-video`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(request)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function submitGoogleVideoImageToVideo(
	request: GoogleVideoImageToVideoRequest,
	token: string = ''
): Promise<{ success: boolean; task: GoogleVideoTask }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/image-to-video`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(request)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoTaskStatus(
	taskId: string,
	token: string = ''
): Promise<{ success: boolean; task: GoogleVideoTask }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/task/${taskId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoUserHistory(
	page: number = 1,
	limit: number = 20,
	token: string = ''
): Promise<{
	success: boolean;
	tasks: GoogleVideoTask[];
	page: number;
	limit: number;
	total: number;
}> {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/google-video/history?page=${page}&limit=${limit}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function deleteGoogleVideoTask(
	taskId: string,
	token: string = ''
): Promise<{ success: boolean; message: string }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/task/${taskId}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function uploadGoogleVideoImage(
	file: File,
	token: string = ''
): Promise<{ success: boolean; url: string }> {
	let error = null;

	const formData = new FormData();
	formData.append('file', file);

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/upload-image`, {
		method: 'POST',
		headers: {
			...(token && { authorization: `Bearer ${token}` })
		},
		body: formData
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoUserCredits(
	token: string = ''
): Promise<{ success: boolean; credits: number }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/credits`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

// ======================== 模型验证工具函数 ========================

export function validateImageCountForModel(
	model: string,
	imageCount: number
): { valid: boolean; message: string } {
	const modelLimits: Record<string, { max: number; type: string }> = {
		'veo3-pro-frames': { max: 1, type: '首帧' },
		'veo3-fast-frames': { max: 1, type: '首帧' },
		'veo2-fast-frames': { max: 2, type: '首尾帧' },
		'veo2-fast-components': { max: 3, type: '视频元素' }
	};

	const limit = modelLimits[model];
	if (!limit) {
		return { valid: false, message: '不支持的模型' };
	}

	if (imageCount > limit.max) {
		return {
			valid: false,
			message: `${model} 模型最多支持 ${limit.max} 张图片（${limit.type}）`
		};
	}

	if (imageCount === 0) {
		return { valid: false, message: '图生视频必须提供至少一张图片' };
	}

	return { valid: true, message: '' };
}

export function getModelImageLimit(model: string): { max: number; type: string } | null {
	const modelLimits: Record<string, { max: number; type: string }> = {
		'veo3-pro-frames': { max: 1, type: '首帧' },
		'veo3-fast-frames': { max: 1, type: '首帧' },
		'veo2-fast-frames': { max: 2, type: '首尾帧' },
		'veo2-fast-components': { max: 3, type: '视频元素' }
	};

	return modelLimits[model] || null;
}

// ======================== 工具函数 ========================

export function formatGoogleVideoTaskStatus(status: string): string {
	const statusMap: Record<string, string> = {
		NOT_START: '未启动',
		SUBMITTED: '已提交',
		IN_PROGRESS: '生成中',
		SUCCESS: '已完成',
		FAILURE: '失败'
	};
	return statusMap[status] || status;
}

export function formatGoogleVideoTaskType(type: string): string {
	const typeMap: Record<string, string> = {
		text_to_video: '文生视频',
		image_to_video: '图生视频'
	};
	return typeMap[type] || type;
}

export function getGoogleVideoModelCreditsConfig(): Record<string, number> {
	return {
		veo3: 100,
		'veo3-fast': 80,
		'veo3-pro': 150,
		'veo3-pro-frames': 200,
		veo2: 80,
		'veo2-fast': 60,
		'veo2-pro': 120,
		'veo3-fast-frames': 160,
		'veo2-fast-frames': 120,
		'veo2-fast-components': 100
	};
}

export function getGoogleVideoProgressDescription(status: string, progress: string): string {
	switch (status) {
		case 'NOT_START':
			return '等待开始';
		case 'SUBMITTED':
			return '已提交，等待处理';
		case 'IN_PROGRESS':
			return `生成中 ${progress}`;
		case 'SUCCESS':
			return '生成完成';
		case 'FAILURE':
			return '生成失败';
		default:
			return progress || '未知状态';
	}
}

export function isGoogleVideoTaskCompleted(status: string): boolean {
	return status === 'SUCCESS' || status === 'FAILURE';
}

export function isGoogleVideoTaskFailed(status: string): boolean {
	return status === 'FAILURE';
}

export function isGoogleVideoTaskRunning(status: string): boolean {
	return status === 'SUBMITTED' || status === 'IN_PROGRESS';
}
```

## 📅 开发时间估算

### 总计: 12-16小时

- **Phase 1 - 后端数据模型**: 2-3小时
- **Phase 2 - API客户端**: 3-4小时
- **Phase 3 - API路由**: 3-4小时
- **Phase 4 - 前端开发**: 4-5小时

## ⚠️ 关键注意事项

### 1. 图生视频模型限制 ⭐

**必须严格遵循的图片数量限制:**

| 模型                 | 最大图片数 | 图片类型 | 限制说明                       |
| -------------------- | ---------- | -------- | ------------------------------ |
| veo3-pro-frames      | **1张**    | 首帧     | 专业版本，只支持一个首帧       |
| veo3-fast-frames     | **1张**    | 首帧     | 快速版本，只支持一个首帧       |
| veo2-fast-frames     | **2张**    | 首尾帧   | 经典版本，分别是首尾帧         |
| veo2-fast-components | **3张**    | 视频元素 | 组件化版本，图片为视频中的元素 |

**实现要求:**

- ✅ 前端必须验证图片数量，提交前阻止超限请求
- ✅ 后端必须二次验证，拒绝不合规请求
- ✅ UI界面必须清晰显示每个模型的限制
- ✅ 错误提示必须明确说明限制原因

### 2. 数据库迁移安全

- 新表完全独立，不影响现有功能
- 遵循项目"只添加不删除"原则
- 所有新列设置`nullable=True`
- 自动集成现有的三层容错机制

### 2. API适配完善

- ✅ 完整的提交和查询接口
- ✅ 支持文生视频和图生视频两种模式
- ✅ 明确的任务状态定义
- ✅ 完整的响应数据结构

### 3. 积分系统复用

- 复用现有的Kling积分管理逻辑
- 独立的积分配置和记录
- 灵活的模型积分设置

### 4. 云存储集成

- 无缝集成现有腾讯云COS系统
- 自动上传生成的视频文件
- 提供永久访问链接

### 5. 前端统一体验

- 与现有Kling/Jimeng保持一致的界面风格
- 统一的错误处理和状态显示
- 可选择性集成到现有页面

这个完整方案确保了谷歌视频功能的无缝集成，遵循项目现有架构，保证系统稳定性和用户体验的一致性。
