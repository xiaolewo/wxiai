"""
Veo视频生成数据模型
支持Google Veo API的完整数据模型定义
包含文生视频、图生视频和任务状态管理
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import uuid

from open_webui.internal.db import Base, get_db

# ======================== SQLAlchemy 数据库模型 ========================


class VeoConfig(Base):
    __tablename__ = "veo_config"

    id = Column(String(255), primary_key=True, default="default")
    enabled = Column(Boolean, default=False, nullable=False)
    base_url = Column(String(500), default="https://api.veo.ai", nullable=False)
    api_key = Column(Text, nullable=True)

    default_model = Column(String(255), nullable=True)
    max_concurrent_tasks = Column(Integer, default=3, nullable=False)
    task_timeout = Column(Integer, default=600000, nullable=False)
    credits_per_generation = Column(Integer, default=50, nullable=False)
    default_duration = Column(Integer, default=5, nullable=False)
    default_aspect_ratio = Column(String(20), default="16:9", nullable=False)
    additional_config = Column(String(10000), nullable=False)

    created_at = Column(
        Text, nullable=False, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    updated_at = Column(Text)
    # 模型积分配置 - JSON格式支持灵活配置
    model_credits_config = Column(String(10000), nullable=True)
    query_interval = Column(Integer, default=15000, nullable=False)  # 15秒
    # 系统配置
    default_enhance_prompt = Column(Boolean, default=True, nullable=False)

    @classmethod
    def get_config(cls):
        """获取Veo配置"""
        try:
            with get_db() as db:
                return db.query(cls).filter(cls.id == "default").first()
        except Exception as e:
            # 如果出现表不存在的错误，尝试创建表
            if "no such table" in str(e).lower():
                print(f"⚠️ 检测到Veo表不存在错误，尝试自动创建表: {e}")
                try:
                    cls._ensure_tables_exist()
                    # 重试获取配置
                    with get_db() as db:
                        return db.query(cls).filter(cls.id == "default").first()
                except Exception as create_error:
                    print(f"❌ 自动创建Veo表失败: {create_error}")
                    raise create_error
            else:
                raise e

    @classmethod
    def save_config(cls, config_data: dict):
        """保存Veo配置"""
        try:
            with get_db() as db:
                config = db.query(cls).filter(cls.id == "default").first()

                if config:
                    # 更新现有配置
                    for key, value in config_data.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
                    config.updated_at = datetime.now().isoformat()
                    config.model_credits_config = json.dumps(
                        config_data.get("model_credits_config")
                    )
                else:
                    # 创建新配置
                    config_data["id"] = "default"
                    config = cls(**config_data)
                    config.updated_at = datetime.now().isoformat()
                    config.model_credits_config = json.dumps(
                        config_data.get("model_credits_config")
                    )
                    db.add(config)

                db.commit()
                db.refresh(config)
                return config
        except Exception as e:
            # 如果出现表不存在的错误，尝试创建表
            if "no such table" in str(e).lower():
                print(f"⚠️ 检测到Veo表不存在错误，尝试自动创建表: {e}")
                try:
                    cls._ensure_tables_exist()
                    # 重试保存配置
                    with get_db() as db:
                        config_data["id"] = 1
                        config = cls(**config_data)
                        db.add(config)
                        db.commit()
                        db.refresh(config)
                        print("✅ Veo表创建成功并保存配置")
                        return config
                except Exception as create_error:
                    import traceback

                    print(traceback.format_exc())
                    print(f"❌ 自动创建Veo表失败: {create_error}")
                    raise create_error
            else:
                raise e

    def to_iso(self, dt):
        if isinstance(dt, datetime):
            return dt.isoformat()
        return dt  # 已经是字符串或 None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model_credits_config": self.model_credits_config
            or self._get_default_model_credits(),
            "default_model": self.default_model,
            "default_enhance_prompt": self.default_enhance_prompt,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
            "query_interval": self.query_interval,
            "created_at": self.to_iso(self.created_at),
            "updated_at": self.to_iso(self.created_at),
        }

    def _get_default_model_credits(self) -> dict:
        """获取默认的模型积分配置"""
        return {
            "veo3": 100,
            "veo3-fast": 80,
            "veo3-pro": 150,
            "veo3-pro-frames": 200,
            "veo2": 90,
            "veo2-fast": 70,
            "veo2-fast-frames": 120,
            "veo2-fast-components": 160,
            "veo2-pro": 140,
            "veo3-fast-frames": 90,
        }

    def get_credits_cost(self, model_name: str) -> int:
        """根据模型获取积分消耗"""
        # 优先使用自定义配置
        if self.model_credits_config and model_name in self.model_credits_config:
            return int(self.model_credits_config[model_name])

        # 回退到默认配置
        default_credits = self._get_default_model_credits()
        return default_credits.get(model_name, 100)

    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        if self.model_credits_config:
            return list(self.model_credits_config.keys())
        return list(self._get_default_model_credits().keys())

    def get_model_image_limits(self, model_name: str) -> dict:
        """获取模型的图片数量限制"""
        limits = {
            # 特殊功能模型 - 有特定的图片数量限制
            "veo3-pro-frames": {"max": 1, "description": "最多支持1个首帧"},
            "veo2-fast-frames": {"max": 2, "description": "最多支持2张图(首尾帧)"},
            "veo2-fast-components": {
                "max": 3,
                "description": "最多支持3张图(视频元素)",
            },
            "veo3-fast-frames": {"max": 1, "description": "最多支持1个首帧"},
            # 基础模型 - 都支持单张图片生成视频
            "veo2": {"max": 1, "description": "支持单张图片生成视频"},
            "veo2-fast": {"max": 1, "description": "支持单张图片生成视频"},
            "veo2-pro": {"max": 1, "description": "支持单张图片生成视频"},
            "veo3": {"max": 1, "description": "支持单张图片生成视频"},
            "veo3-fast": {"max": 1, "description": "支持单张图片生成视频"},
            "veo3-pro": {"max": 1, "description": "支持单张图片生成视频"},
        }
        return limits.get(model_name, {"max": 0, "description": "不支持图片输入"})

    @classmethod
    def _ensure_tables_exist(cls):
        """确保Veo相关表存在，如果不存在则创建"""
        from sqlalchemy import text

        with get_db() as db:
            # 创建veo_config表
            db.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS veo_config (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    enabled BOOLEAN NOT NULL DEFAULT 0,
                    base_url VARCHAR(500) NOT NULL DEFAULT 'https://api.veoai.com',
                    api_key TEXT,
                    model_credits_config JSON,
                    default_model VARCHAR(50) NOT NULL DEFAULT 'veo3',
                    default_enhance_prompt BOOLEAN NOT NULL DEFAULT 1,
                    max_concurrent_tasks INTEGER NOT NULL DEFAULT 3,
                    task_timeout INTEGER NOT NULL DEFAULT 900000,
                    query_interval INTEGER NOT NULL DEFAULT 15000,
                    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    updated_at DATETIME
                )
            """
                )
            )

            # 创建索引（如果不存在）
            try:
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_veo_config_id ON veo_config (id)"
                    )
                )
            except:
                pass

            # 创建veo_tasks表
            db.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS veo_tasks (
                    id VARCHAR(50) NOT NULL PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'submitted',
                    prompt TEXT NOT NULL,
                    model VARCHAR(50) NOT NULL,
                    enhance_prompt BOOLEAN NOT NULL DEFAULT 1,
                    input_images JSON,
                    cloud_input_images JSON,
                    result_video_url TEXT,
                    cloud_video_url TEXT,
                    external_task_id VARCHAR(100),
                    progress VARCHAR(10) DEFAULT '0%',
                    fail_reason TEXT,
                    credits_cost INTEGER,
                    properties JSON,
                    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    updated_at DATETIME,
                    finish_time DATETIME
                )
            """
                )
            )

            # 创建veo_tasks表索引
            try:
                db.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_veo_tasks_id ON veo_tasks (id)")
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_veo_tasks_user_id ON veo_tasks (user_id)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_veo_tasks_status ON veo_tasks (status)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_veo_tasks_created_at ON veo_tasks (created_at)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_veo_tasks_external_task_id ON veo_tasks (external_task_id)"
                    )
                )
            except:
                pass

            # 创建veo_credits表
            db.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS veo_credits (
                    id VARCHAR(50) NOT NULL PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    task_id VARCHAR(50) NOT NULL,
                    credit_amount INTEGER NOT NULL,
                    credits_before INTEGER,
                    credits_after INTEGER,
                    operation_type VARCHAR(20) NOT NULL DEFAULT 'deduct',
                    model_name VARCHAR(50),
                    description TEXT,
                    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
                )
            """
                )
            )

            # 创建veo_credits表索引
            try:
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_veo_credits_id ON veo_credits (id)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_veo_credits_user_id ON veo_credits (user_id)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_veo_credits_task_id ON veo_credits (task_id)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_veo_credits_created_at ON veo_credits (created_at)"
                    )
                )
            except:
                pass

            db.commit()
            print("✅ 所有Veo数据库表已确保存在")


class VeoTask(Base):
    __tablename__ = "veo_tasks"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    status = Column(String(20), default="submitted", nullable=False)

    # 输入参数
    prompt = Column(Text, nullable=False)
    model = Column(String(50), nullable=False)
    enhance_prompt = Column(Boolean, default=True, nullable=False)
    input_images = Column(JSON, nullable=True)  # 原始图片URL数组

    # 云存储相关
    cloud_input_images = Column(JSON, nullable=True)  # 云端图片URL数组
    result_video_url = Column(Text, nullable=True)  # 原始视频URL
    cloud_video_url = Column(Text, nullable=True)  # 云端视频URL

    # 任务状态
    external_task_id = Column(String(100), nullable=True)
    progress = Column(String(10), default="0%")
    fail_reason = Column(Text, nullable=True)

    # 积分消耗
    credits_cost = Column(Integer, nullable=True)

    # 扩展属性
    properties = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, nullable=True)
    finish_time = Column(DateTime, nullable=True)

    @classmethod
    def create_task(cls, task_data: dict):
        """创建新任务"""
        if "id" not in task_data:
            task_data["id"] = str(uuid.uuid4())

        try:
            with get_db() as db:
                task = cls(**task_data)
                db.add(task)
                db.commit()
                db.refresh(task)
                return task
        except Exception as e:
            if "no such table" in str(e).lower():
                print(f"⚠️ 检测到Veo任务表不存在错误，尝试自动创建表: {e}")
                VeoConfig._ensure_tables_exist()
                # 重试创建任务
                with get_db() as db:
                    task = cls(**task_data)
                    db.add(task)
                    db.commit()
                    db.refresh(task)
                    return task
            else:
                raise e

    @classmethod
    def get_task_by_id(cls, task_id: str):
        """根据ID获取任务"""
        try:
            with get_db() as db:
                return db.query(cls).filter(cls.id == task_id).first()
        except Exception as e:
            if "no such table" in str(e).lower():
                print(f"⚠️ 检测到Veo任务表不存在错误，尝试自动创建表: {e}")
                VeoConfig._ensure_tables_exist()
                # 重试查询
                with get_db() as db:
                    return db.query(cls).filter(cls.id == task_id).first()
            else:
                raise e

    @classmethod
    def get_tasks_by_user(cls, user_id: str, limit: int = 20, offset: int = 0):
        """获取用户的任务列表"""
        try:
            with get_db() as db:
                return (
                    db.query(cls)
                    .filter(cls.user_id == user_id)
                    .order_by(cls.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )
        except Exception as e:
            if "no such table" in str(e).lower():
                print(f"⚠️ 检测到Veo任务表不存在错误，尝试自动创建表: {e}")
                VeoConfig._ensure_tables_exist()
                # 重试查询
                with get_db() as db:
                    return (
                        db.query(cls)
                        .filter(cls.user_id == user_id)
                        .order_by(cls.created_at.desc())
                        .limit(limit)
                        .offset(offset)
                        .all()
                    )
            else:
                raise e

    @classmethod
    def update_task_status(cls, task_id: str, status_data: dict):
        """更新任务状态"""
        try:
            with get_db() as db:
                task = db.query(cls).filter(cls.id == task_id).first()
                if task:
                    for key, value in status_data.items():
                        if hasattr(task, key):
                            setattr(task, key, value)
                    task.updated_at = datetime.now().isoformat()
                    db.commit()
                    db.refresh(task)
                    return task
                return None
        except Exception as e:
            if "no such table" in str(e).lower():
                print(f"⚠️ 检测到Veo任务表不存在错误，尝试自动创建表: {e}")
                VeoConfig._ensure_tables_exist()
                # 重试更新
                with get_db() as db:
                    task = db.query(cls).filter(cls.id == task_id).first()
                    if task:
                        for key, value in status_data.items():
                            if hasattr(task, key):
                                setattr(task, key, value)
                        task.updated_at = datetime.now().isoformat().isoformat()
                        db.commit()
                        db.refresh(task)
                        return task
                    return None
            else:
                raise e

    @classmethod
    def delete_task(cls, task_id: str) -> bool:
        """删除任务"""
        try:
            with get_db() as db:
                task = db.query(cls).filter(cls.id == task_id).first()
                if task:
                    db.delete(task)
                    db.commit()
                    return True
                return False
        except Exception as e:
            if "no such table" in str(e).lower():
                print(f"⚠️ 检测到Veo任务表不存在错误，尝试自动创建表: {e}")
                VeoConfig._ensure_tables_exist()
                # 重试删除
                with get_db() as db:
                    task = db.query(cls).filter(cls.id == task_id).first()
                    if task:
                        db.delete(task)
                        db.commit()
                        return True
                    return False
            else:
                print(f"删除任务时出错: {str(e)}")
                return False

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "prompt": self.prompt,
            "model": self.model,
            "enhance_prompt": self.enhance_prompt,
            "input_images": self.input_images,
            "cloud_input_images": self.cloud_input_images,
            "result_video_url": self.result_video_url,
            "cloud_video_url": self.cloud_video_url,
            "external_task_id": self.external_task_id,
            "progress": self.progress,
            "fail_reason": self.fail_reason,
            "credits_cost": self.credits_cost,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "finish_time": self.finish_time.isoformat() if self.finish_time else None,
        }


class VeoCredit(Base):
    __tablename__ = "veo_credits"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    task_id = Column(String(50), nullable=False)

    # 积分变化
    credit_amount = Column(Integer, nullable=False)
    credits_before = Column(Integer, nullable=True)
    credits_after = Column(Integer, nullable=True)

    # 操作信息
    operation_type = Column(String(20), default="deduct", nullable=False)
    model_name = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False)

    @classmethod
    def create_credit_log(cls, log_data: dict):
        """创建积分记录"""
        if "id" not in log_data:
            log_data["id"] = str(uuid.uuid4())

        try:
            with get_db() as db:
                credit_log = cls(**log_data)
                db.add(credit_log)
                db.commit()
                db.refresh(credit_log)
                return credit_log
        except Exception as e:
            if "no such table" in str(e).lower():
                print(f"⚠️ 检测到Veo积分表不存在错误，尝试自动创建表: {e}")
                VeoConfig._ensure_tables_exist()
                # 重试创建积分记录
                with get_db() as db:
                    credit_log = cls(**log_data)
                    db.add(credit_log)
                    db.commit()
                    db.refresh(credit_log)
                    return credit_log
            else:
                raise e

    @classmethod
    def get_credits_by_user(cls, user_id: str, limit: int = 50):
        """获取用户的积分记录"""
        try:
            with get_db() as db:
                return (
                    db.query(cls)
                    .filter(cls.user_id == user_id)
                    .order_by(cls.created_at.desc())
                    .limit(limit)
                    .all()
                )
        except Exception as e:
            if "no such table" in str(e).lower():
                print(f"⚠️ 检测到Veo积分表不存在错误，尝试自动创建表: {e}")
                VeoConfig._ensure_tables_exist()
                # 重试查询
                with get_db() as db:
                    return (
                        db.query(cls)
                        .filter(cls.user_id == user_id)
                        .order_by(cls.created_at.desc())
                        .limit(limit)
                        .all()
                    )
            else:
                raise e


# ======================== Pydantic 数据模型 ========================


class VeoConfigForm(BaseModel):
    """Veo配置表单模型"""

    enabled: bool = False
    base_url: Optional[str] = "https://api.veoai.com"
    api_key: Optional[str] = None
    model_credits_config: Optional[Dict[str, int]] = None
    default_model: str = "veo3"
    default_enhance_prompt: bool = True
    max_concurrent_tasks: int = 3
    task_timeout: int = 900000
    query_interval: int = 15000


class VeoGenerateRequest(BaseModel):
    """Veo视频生成请求模型"""

    # 基础参数
    prompt: str = Field(..., description="视频生成提示词")
    model: str = Field("veo3", description="选择的生成模型")
    enhance_prompt: bool = Field(True, description="是否优化提示词")

    # 图片输入 - 支持URL或base64
    images: Optional[List[str]] = Field(None, description="输入图片数组(URL或base64)")

    # 内部使用字段
    external_task_id: Optional[str] = None
    callback_url: Optional[str] = None

    @validator("images")
    def validate_images(cls, v, values):
        """验证图片数量限制"""
        if v is None:
            return v

        model = values.get("model", "veo3")

        # 定义支持图片的模型和限制
        image_support = {
            # 特殊功能模型
            "veo3-pro-frames": {"max": 1, "description": "最多支持1个首帧"},
            "veo2-fast-frames": {"max": 2, "description": "最多支持2张图(首尾帧)"},
            "veo2-fast-components": {
                "max": 3,
                "description": "最多支持3张图(视频元素)",
            },
            "veo3-fast-frames": {"max": 1, "description": "最多支持1个首帧"},
            # 基础模型 - 都支持单张图片生成视频
            "veo2": {"max": 1, "description": "支持单张图片生成视频"},
            "veo2-fast": {"max": 1, "description": "支持单张图片生成视频"},
            "veo2-pro": {"max": 1, "description": "支持单张图片生成视频"},
            "veo3": {"max": 1, "description": "支持单张图片生成视频"},
            "veo3-fast": {"max": 1, "description": "支持单张图片生成视频"},
            "veo3-pro": {"max": 1, "description": "支持单张图片生成视频"},
        }

        # 检查模型是否支持图片输入
        if model not in image_support:
            if v:  # 如果提供了图片但模型不支持
                raise ValueError(f"模型 {model} 不支持图片输入")
            return v

        # 检查图片数量限制
        model_limit = image_support[model]["max"]
        if len(v) > model_limit:
            description = image_support[model]["description"]
            raise ValueError(f"模型 {model} {description}，您提供了 {len(v)} 张图片")

        return v


class VeoTaskForm(BaseModel):
    """Veo任务表单模型"""

    id: str
    user_id: str
    status: str
    prompt: str
    model: str
    enhance_prompt: bool = True
    input_images: Optional[List[str]] = None
    cloud_input_images: Optional[List[str]] = None
    result_video_url: Optional[str] = None
    cloud_video_url: Optional[str] = None
    external_task_id: Optional[str] = None
    progress: str = "0%"
    fail_reason: Optional[str] = None
    credits_cost: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None


class VeoTaskResponse(BaseModel):
    """Veo任务响应模型"""

    id: str
    status: str
    progress: str
    video_url: Optional[str] = None
    fail_reason: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    finish_time: Optional[str] = None


class VeoUserConfig(BaseModel):
    """Veo用户配置模型（隐藏敏感信息）"""

    enabled: bool
    supported_models: List[str]
    model_credits_config: Dict[str, int]
    default_model: str
    default_enhance_prompt: bool
    model_image_limits: Dict[str, Dict[str, Any]]
