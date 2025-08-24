"""
即梦视频生成数据模型
包含配置管理和任务管理
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid
import json

from open_webui.internal.db import Base, SessionLocal, get_db


# ======================== Pydantic 数据模型 ========================


class JimengConfigForm(BaseModel):
    """即梦配置表单模型"""

    enabled: bool = False
    base_url: Optional[str] = "https://ark.cn-beijing.volces.com"
    api_key: Optional[str] = None
    default_duration: str = "5"
    default_aspect_ratio: str = "16:9"
    default_cfg_scale: float = 0.5
    default_watermark: bool = False
    credits_per_5s: int = 30
    credits_per_10s: int = 60
    max_concurrent_tasks: int = 5
    task_timeout: int = 600000
    query_interval: int = 10000
    detected_api_path: Optional[str] = None


class JimengGenerateRequest(BaseModel):
    """即梦视频生成请求模型"""

    # 支持OpenAI格式的content数组或简单字符串prompt
    prompt: Optional[str] = Field(None, description="视频描述")
    content: Optional[Any] = Field(None, description="OpenAI格式的content数组或字符串")

    image_url: Optional[str] = Field(None, description="图生视频输入图片URL")
    image: Optional[str] = Field(None, description="图生视频输入图片base64数据")
    duration: str = Field("5", description="视频时长: 5, 10")
    aspect_ratio: str = Field(
        "16:9", description="画面比例: 1:1, 21:9, 16:9, 9:16, 4:3, 3:4"
    )
    cfg_scale: float = Field(0.5, description="CFG Scale")
    watermark: bool = Field(False, description="是否包含水印")

    # 内部使用字段
    external_task_id: Optional[str] = None
    callback_url: Optional[str] = None

    async def get_parsed_content(
        self, user_id: str, http_request=None
    ) -> tuple[str, str]:
        """
        解析content或prompt，返回(prompt, image_url)
        """
        from open_webui.routers.jimeng import parse_content_for_jimeng

        if self.content is not None:
            # 如果有content字段，解析它
            return await parse_content_for_jimeng(self.content, user_id, http_request)
        else:
            # 否则使用现有的prompt和image_url
            return self.prompt or "", self.image_url or ""


class JimengTaskForm(BaseModel):
    """即梦任务表单模型"""

    id: str
    user_id: str
    action: str
    status: str
    prompt: str
    duration: str
    aspect_ratio: str
    cfg_scale: float
    watermark: bool = False
    image_url: Optional[str] = None
    input_image: Optional[str] = None
    external_task_id: Optional[str] = None
    video_url: Optional[str] = None
    progress: str = "0%"
    fail_reason: Optional[str] = None
    credits_cost: int
    properties: Optional[Dict[str, Any]] = None


# ======================== SQLAlchemy ORM 模型 ========================


class JimengConfig(Base):
    """即梦配置表"""

    __tablename__ = "jimeng_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False, nullable=False, comment="是否启用即梦服务")
    base_url = Column(Text, nullable=True, comment="即梦API基础URL")
    api_key = Column(Text, nullable=True, comment="即梦API密钥")

    # 默认参数配置
    default_duration = Column(
        String(10), default="5", nullable=False, comment="默认视频时长"
    )
    default_aspect_ratio = Column(
        String(10), default="16:9", nullable=False, comment="默认画面比例"
    )
    default_cfg_scale = Column(
        Float, default=0.5, nullable=False, comment="默认CFG Scale"
    )
    default_watermark = Column(
        Boolean, default=False, nullable=False, comment="默认水印设置"
    )

    # 积分配置
    credits_per_5s = Column(
        Integer, default=30, nullable=False, comment="5秒视频积分消耗"
    )
    credits_per_10s = Column(
        Integer, default=60, nullable=False, comment="10秒视频积分消耗"
    )

    # 系统配置
    max_concurrent_tasks = Column(
        Integer, default=5, nullable=False, comment="最大并发任务数"
    )
    task_timeout = Column(
        Integer, default=600000, nullable=False, comment="任务超时时间(毫秒)"
    )
    query_interval = Column(
        Integer, default=10000, nullable=False, comment="轮询间隔(毫秒)"
    )

    # API路径配置
    detected_api_path = Column(Text, nullable=True, comment="检测到的API路径")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    @classmethod
    def get_config(cls) -> Optional["JimengConfig"]:
        """获取即梦配置（安全查询，兼容缺失字段）"""
        with get_db() as db:
            try:
                # 先尝试正常的ORM查询
                return db.query(cls).first()
            except Exception as e:
                # 如果ORM查询失败（通常是因为字段缺失），使用原始SQL查询
                print(f"⚠️  ORM查询失败，使用安全查询: {e}")
                try:
                    # 检查表是否存在
                    import sqlalchemy as sa

                    inspector = sa.inspect(db.bind)
                    if not inspector.has_table("jimeng_config"):
                        return None

                    # 获取现有字段
                    columns = [
                        col["name"] for col in inspector.get_columns("jimeng_config")
                    ]

                    # 构造安全的查询字段列表
                    safe_fields = []
                    field_mapping = {
                        "id": "id",
                        "enabled": "enabled",
                        "base_url": "base_url",
                        "api_key": "api_key",
                        "default_duration": "default_duration",
                        "default_aspect_ratio": "default_aspect_ratio",
                        "default_cfg_scale": "default_cfg_scale",
                        "default_watermark": "default_watermark",  # 可能缺失
                        "credits_per_5s": "credits_per_5s",
                        "credits_per_10s": "credits_per_10s",
                        "max_concurrent_tasks": "max_concurrent_tasks",
                        "task_timeout": "task_timeout",
                        "query_interval": "query_interval",
                        "detected_api_path": "detected_api_path",
                        "created_at": "created_at",
                        "updated_at": "updated_at",
                    }

                    for field, attr in field_mapping.items():
                        if field in columns:
                            safe_fields.append(f"{field} as {attr}")

                    if not safe_fields:
                        return None

                    # 执行安全查询
                    sql = f"SELECT {', '.join(safe_fields)} FROM jimeng_config LIMIT 1"
                    result = db.execute(sa.text(sql)).fetchone()

                    if not result:
                        return None

                    # 手动构造配置对象
                    config = cls()
                    row_dict = dict(result._mapping)

                    for attr, value in row_dict.items():
                        if hasattr(config, attr):
                            setattr(config, attr, value)

                    # 设置缺失字段的默认值
                    if (
                        not hasattr(config, "default_watermark")
                        or config.default_watermark is None
                    ):
                        config.default_watermark = False

                    print(f"✅ 安全查询成功，字段: {list(row_dict.keys())}")
                    return config

                except Exception as safe_error:
                    print(f"❌ 安全查询也失败: {safe_error}")
                    return None

    @classmethod
    def save_config(cls, config_data: dict) -> "JimengConfig":
        """保存即梦配置（安全保存，兼容缺失字段）"""
        with get_db() as db:
            # 使用安全的get_config方法获取现有配置
            config = cls.get_config()

            if config:
                # 更新现有配置
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

                # 确保缺失字段有默认值
                if not hasattr(config, "default_watermark"):
                    config.default_watermark = config_data.get(
                        "default_watermark", False
                    )

                # 使用原生SQL更新，避免ORM字段检查
                try:
                    import sqlalchemy as sa

                    inspector = sa.inspect(db.bind)
                    columns = [
                        col["name"] for col in inspector.get_columns("jimeng_config")
                    ]

                    # 构建安全的UPDATE语句
                    update_fields = []
                    update_values = {}

                    for key, value in config_data.items():
                        if key in columns:  # 只更新存在的字段
                            update_fields.append(f"{key} = :{key}")
                            update_values[key] = value

                    if update_fields:
                        sql = f"UPDATE jimeng_config SET {', '.join(update_fields)}, updated_at = datetime('now') WHERE id = :config_id"
                        update_values["config_id"] = config.id

                        db.execute(sa.text(sql), update_values)
                        db.commit()

                        print(f"✅ 配置更新成功，字段: {list(update_values.keys())}")

                        # 重新获取更新后的配置
                        return cls.get_config()

                except Exception as update_error:
                    print(f"⚠️  安全更新失败: {update_error}")
                    # 如果数据库是只读的，直接返回当前配置对象（已更新内存中的值）
                    if "readonly database" in str(update_error):
                        print("⚠️  数据库只读，返回内存中的配置对象")
                        return config
                    else:
                        # 其他错误，抛出异常
                        raise Exception(f"保存配置失败: {update_error}")
            else:
                # 创建新配置 - 只包含数据库中存在的字段
                try:
                    import sqlalchemy as sa

                    inspector = sa.inspect(db.bind)

                    if inspector.has_table("jimeng_config"):
                        columns = [
                            col["name"]
                            for col in inspector.get_columns("jimeng_config")
                        ]

                        # 过滤掉数据库中不存在的字段
                        safe_data = {}
                        for key, value in config_data.items():
                            if key in columns:
                                safe_data[key] = value

                        # 添加时间戳
                        if "created_at" in columns:
                            safe_data["created_at"] = func.now()
                        if "updated_at" in columns:
                            safe_data["updated_at"] = func.now()

                        # 创建配置对象，只包含安全字段
                        config = cls()
                        for key, value in safe_data.items():
                            if hasattr(config, key):
                                setattr(config, key, value)

                        # 设置缺失字段的默认值
                        if not hasattr(config, "default_watermark"):
                            config.default_watermark = config_data.get(
                                "default_watermark", False
                            )

                        db.add(config)
                        db.commit()
                        db.refresh(config)

                        print(f"✅ 新配置创建成功")
                        return config
                    else:
                        raise Exception("jimeng_config 表不存在")

                except Exception as create_error:
                    print(f"❌ 创建配置失败: {create_error}")
                    raise Exception(f"保存配置失败: {create_error}")

            return config

    def get_credits_cost(self, duration: str) -> int:
        """获取指定时长的积分消耗"""
        if duration == "5":
            return self.credits_per_5s
        elif duration == "10":
            return self.credits_per_10s
        else:
            return self.credits_per_5s  # 默认值

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "default_duration": self.default_duration,
            "default_aspect_ratio": self.default_aspect_ratio,
            "default_cfg_scale": self.default_cfg_scale,
            "default_watermark": getattr(self, "default_watermark", False),
            "credits_per_5s": self.credits_per_5s,
            "credits_per_10s": self.credits_per_10s,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
            "query_interval": self.query_interval,
            "detected_api_path": self.detected_api_path,
            "created_at": (
                self.created_at.isoformat()
                if hasattr(self.created_at, "isoformat") and self.created_at
                else str(self.created_at) if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if hasattr(self.updated_at, "isoformat") and self.updated_at
                else str(self.updated_at) if self.updated_at else None
            ),
        }


class JimengTask(Base):
    """即梦任务表"""

    __tablename__ = "jimeng_tasks"

    id = Column(String(255), primary_key=True, comment="任务ID")
    user_id = Column(String(255), nullable=False, comment="用户ID")
    action = Column(
        String(50), nullable=False, comment="任务类型: TEXT_TO_VIDEO, IMAGE_TO_VIDEO"
    )
    status = Column(String(50), default="submitted", nullable=False, comment="任务状态")

    # 生成参数
    prompt = Column(Text, nullable=False, comment="视频描述")
    duration = Column(String(10), nullable=False, comment="视频时长")
    aspect_ratio = Column(String(10), nullable=False, comment="画面比例")
    cfg_scale = Column(Float, nullable=False, comment="CFG Scale")
    watermark = Column(Boolean, default=False, nullable=False, comment="是否包含水印")

    # 图生视频参数
    image_url = Column(Text, nullable=True, comment="输入图片URL(图生视频)")
    input_image = Column(Text, nullable=True, comment="输入图片base64数据")

    # 任务结果
    external_task_id = Column(String(255), nullable=True, comment="即梦返回的任务ID")
    video_url = Column(Text, nullable=True, comment="生成的视频URL")
    cloud_video_url = Column(Text, nullable=True, comment="云存储视频URL")
    progress = Column(String(50), default="0%", comment="任务进度")
    fail_reason = Column(Text, nullable=True, comment="失败原因")

    # 积分相关
    credits_cost = Column(Integer, nullable=False, comment="积分消耗")

    # 扩展属性
    properties = Column(JSON, nullable=True, comment="扩展属性JSON")

    # 时间戳
    submit_time = Column(
        DateTime, default=func.now(), nullable=False, comment="提交时间"
    )
    start_time = Column(DateTime, nullable=True, comment="开始处理时间")
    complete_time = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # 创建索引
    __table_args__ = (
        Index("idx_jimeng_tasks_user_id", "user_id"),
        Index("idx_jimeng_tasks_status", "status"),
        Index("idx_jimeng_tasks_created_at", "created_at"),
        Index("idx_jimeng_tasks_user_status", "user_id", "status"),
    )

    @classmethod
    def create_task(
        cls,
        user_id: str,
        action: str,
        prompt: str,
        duration: str,
        aspect_ratio: str,
        cfg_scale: float,
        credits_cost: int,
        watermark: bool = False,
        image_url: Optional[str] = None,
        input_image: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "JimengTask":
        """创建即梦任务"""
        task_id = str(uuid.uuid4())

        task = cls(
            id=task_id,
            user_id=user_id,
            action=action,
            status="submitted",
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            cfg_scale=cfg_scale,
            watermark=watermark,
            image_url=image_url,
            input_image=input_image,
            credits_cost=credits_cost,
            properties=properties or {},
        )

        with get_db() as db:
            db.add(task)
            db.commit()
            db.refresh(task)

        return task

    @classmethod
    def get_task_by_id(cls, task_id: str) -> Optional["JimengTask"]:
        """根据ID获取任务（安全查询，兼容缺失字段）"""
        with get_db() as db:
            try:
                # 先尝试ORM查询
                return db.query(cls).filter(cls.id == task_id).first()
            except Exception as e:
                # 如果ORM查询失败，使用原生SQL查询
                print(f"⚠️  JimengTask按ID查询失败，使用安全查询: {e}")
                try:
                    import sqlalchemy as sa

                    inspector = sa.inspect(db.bind)

                    if not inspector.has_table("jimeng_tasks"):
                        return None

                    # 获取现有字段
                    columns = [
                        col["name"] for col in inspector.get_columns("jimeng_tasks")
                    ]

                    # 构建安全的SELECT语句
                    safe_fields = [
                        col
                        for col in columns
                        if col
                        in [
                            "id",
                            "user_id",
                            "action",
                            "status",
                            "prompt",
                            "duration",
                            "aspect_ratio",
                            "cfg_scale",
                            "image_url",
                            "input_image",
                            "external_task_id",
                            "video_url",
                            "cloud_video_url",
                            "progress",
                            "fail_reason",
                            "credits_cost",
                            "properties",
                            "submit_time",
                            "start_time",
                            "complete_time",
                            "created_at",
                            "updated_at",
                            "watermark",
                        ]
                    ]

                    if not safe_fields:
                        return None

                    sql = f"SELECT {', '.join(safe_fields)} FROM jimeng_tasks WHERE id = :task_id"
                    result = db.execute(sa.text(sql), {"task_id": task_id}).fetchone()

                    if not result:
                        return None

                    # 手动构造任务对象
                    task = cls()
                    row_dict = dict(result._mapping)

                    for attr, value in row_dict.items():
                        if hasattr(task, attr):
                            setattr(task, attr, value)

                    # 设置缺失字段的默认值
                    if not hasattr(task, "watermark"):
                        task.watermark = False

                    print(f"✅ 安全查询获取任务成功: {task_id}")
                    return task

                except Exception as safe_error:
                    print(f"❌ 安全查询任务失败: {safe_error}")
                    return None

    @classmethod
    def get_user_tasks(
        cls, user_id: str, page: int = 1, limit: int = 20
    ) -> List["JimengTask"]:
        """获取用户任务列表（安全查询，兼容缺失字段）"""
        with get_db() as db:
            try:
                # 先尝试ORM查询
                offset = (page - 1) * limit
                return (
                    db.query(cls)
                    .filter(cls.user_id == user_id)
                    .order_by(cls.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )
            except Exception as e:
                # 如果ORM查询失败，使用原生SQL查询
                print(f"⚠️  JimengTask ORM查询失败，使用安全查询: {e}")
                try:
                    import sqlalchemy as sa

                    inspector = sa.inspect(db.bind)

                    if not inspector.has_table("jimeng_tasks"):
                        return []

                    # 获取现有字段
                    columns = [
                        col["name"] for col in inspector.get_columns("jimeng_tasks")
                    ]

                    # 构建安全的SELECT语句
                    safe_fields = [
                        col
                        for col in columns
                        if col
                        in [
                            "id",
                            "user_id",
                            "action",
                            "status",
                            "prompt",
                            "duration",
                            "aspect_ratio",
                            "cfg_scale",
                            "image_url",
                            "input_image",
                            "external_task_id",
                            "video_url",
                            "cloud_video_url",
                            "progress",
                            "fail_reason",
                            "credits_cost",
                            "properties",
                            "submit_time",
                            "start_time",
                            "complete_time",
                            "created_at",
                            "updated_at",
                            "watermark",
                        ]
                    ]

                    if not safe_fields:
                        return []

                    offset = (page - 1) * limit
                    sql = f"""
                        SELECT {', '.join(safe_fields)} 
                        FROM jimeng_tasks 
                        WHERE user_id = :user_id 
                        ORDER BY created_at DESC 
                        LIMIT :limit OFFSET :offset
                    """

                    result = db.execute(
                        sa.text(sql),
                        {"user_id": user_id, "limit": limit, "offset": offset},
                    ).fetchall()

                    # 手动构造任务对象列表
                    tasks = []
                    for row in result:
                        task = cls()
                        row_dict = dict(row._mapping)

                        for attr, value in row_dict.items():
                            if hasattr(task, attr):
                                setattr(task, attr, value)

                        # 设置缺失字段的默认值
                        if not hasattr(task, "watermark"):
                            task.watermark = False

                        tasks.append(task)

                    print(f"✅ 安全查询获取到 {len(tasks)} 个任务")
                    return tasks

                except Exception as safe_error:
                    print(f"❌ 安全查询也失败: {safe_error}")
                    return []

    @classmethod
    def get_user_task_count(cls, user_id: str) -> int:
        """获取用户任务总数"""
        with get_db() as db:
            return db.query(cls).filter(cls.user_id == user_id).count()

    def update_status(self, status: str, progress: str = None):
        """更新任务状态"""
        with get_db() as db:
            task = db.query(JimengTask).filter(JimengTask.id == self.id).first()
            if task:
                task.status = status
                if progress:
                    task.progress = progress

                if status == "processing" and not task.start_time:
                    task.start_time = func.now()
                elif status in ["succeed", "failed"] and not task.complete_time:
                    task.complete_time = func.now()

                task.updated_at = func.now()
                db.commit()

                # 更新当前实例
                self.status = status
                if progress:
                    self.progress = progress

    def update_from_api_response(self, response: dict):
        """从API响应更新任务信息"""
        print(f"🎬 【即梦任务】更新任务 {self.id} 从API响应: {response}")

        with get_db() as db:
            task = db.query(JimengTask).filter(JimengTask.id == self.id).first()
            if not task:
                print(f"❌ 【即梦任务】任务 {self.id} 不存在")
                return

            # 解析即梦API响应
            if response.get("code") == "success":
                # 提交成功，保存外部任务ID
                external_task_id = response.get("data")
                if external_task_id:
                    task.external_task_id = str(external_task_id)
                    task.status = "processing"
                    task.start_time = func.now()
                    print(f"🎬 【即梦任务】任务提交成功，外部ID: {external_task_id}")
            else:
                # 提交失败
                error_message = response.get("message", "提交失败")
                task.status = "failed"
                task.fail_reason = error_message
                task.complete_time = func.now()
                print(f"❌ 【即梦任务】任务提交失败: {error_message}")

            task.updated_at = func.now()
            db.commit()

            # 更新当前实例属性
            self.external_task_id = task.external_task_id
            self.status = task.status
            self.fail_reason = task.fail_reason

    def update_result(self, video_url: str, status: str = "succeed"):
        """更新任务结果"""
        with get_db() as db:
            task = db.query(JimengTask).filter(JimengTask.id == self.id).first()
            if task:
                task.video_url = video_url
                task.status = status
                task.progress = "100%"
                task.complete_time = func.now()
                task.updated_at = func.now()
                db.commit()

                # 更新当前实例
                self.video_url = video_url
                self.status = status
                self.progress = "100%"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "status": self.status,
            "prompt": self.prompt,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "cfg_scale": self.cfg_scale,
            "watermark": getattr(self, "watermark", False),
            "image_url": self.image_url,
            "input_image": self.input_image,
            "external_task_id": self.external_task_id,
            "video_url": self.cloud_video_url or self.video_url,  # 优先返回云存储URL
            "progress": self.progress,
            "fail_reason": self.fail_reason,
            "credits_cost": self.credits_cost,
            "properties": self.properties,
            "submit_time": (
                self.submit_time.isoformat()
                if hasattr(self.submit_time, "isoformat") and self.submit_time
                else str(self.submit_time) if self.submit_time else None
            ),
            "start_time": (
                self.start_time.isoformat()
                if hasattr(self.start_time, "isoformat") and self.start_time
                else str(self.start_time) if self.start_time else None
            ),
            "complete_time": (
                self.complete_time.isoformat()
                if hasattr(self.complete_time, "isoformat") and self.complete_time
                else str(self.complete_time) if self.complete_time else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if hasattr(self.created_at, "isoformat") and self.created_at
                else str(self.created_at) if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if hasattr(self.updated_at, "isoformat") and self.updated_at
                else str(self.updated_at) if self.updated_at else None
            ),
            # 添加服务类型标识
            "serviceType": "jimeng",
        }
