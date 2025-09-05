"""
ComfyUI 数据库模型
基于哩布ComfyUI API的工作流管理、任务执行、积分记录等功能
支持动态参数处理和工作流管理
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
    ForeignKey,
)
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import json
import uuid

from open_webui.internal.db import Base, get_db


# ======================== Pydantic 请求/响应模型 ========================


class ComfyUIConfigForm(BaseModel):
    """ComfyUI配置表单"""

    access_key: str = Field(..., description="哩布API访问凭证")
    secret_key: str = Field(..., description="哩布API访问密钥")
    base_url: str = Field("https://openapi.liblibai.cloud", description="API基础URL")
    enabled: bool = Field(False, description="启用状态")
    timeout: int = Field(300, description="请求超时时间")
    max_concurrent_tasks: int = Field(5, description="最大并发任务数")


class ComfyUIConfigResponse(BaseModel):
    """ComfyUI配置响应"""

    id: str
    access_key: Optional[str] = None  # 隐藏敏感信息
    secret_key: Optional[str] = None  # 隐藏敏感信息
    base_url: str
    enabled: bool
    timeout: int
    max_concurrent_tasks: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ComfyUIWorkflowForm(BaseModel):
    """ComfyUI工作流表单"""

    template_uuid: str = Field(..., description="哩布模板UUID")
    workflow_uuid: str = Field(..., description="哩布工作流UUID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    category: Optional[str] = Field(None, description="分类")
    preview_image: Optional[str] = Field(None, description="预览图URL")
    parameter_schema: Dict[str, Any] = Field(..., description="参数结构定义")
    default_params: Optional[Dict[str, Any]] = Field(None, description="默认参数值")
    base_credits: int = Field(10, description="基础积分消耗")
    complexity_multiplier: float = Field(1.0, description="复杂度系数")
    enabled: bool = Field(True, description="启用状态")
    is_public: bool = Field(False, description="是否公开显示")
    sort_order: int = Field(0, description="排序权重")


class ComfyUIWorkflowResponse(BaseModel):
    """ComfyUI工作流响应"""

    id: str
    template_uuid: str
    workflow_uuid: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    preview_image: Optional[str] = None
    parameter_schema: Dict[str, Any]
    default_params: Optional[Dict[str, Any]] = None
    base_credits: int
    complexity_multiplier: float
    enabled: bool
    is_public: bool
    sort_order: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ComfyUITaskRequest(BaseModel):
    """ComfyUI任务请求"""

    workflow_id: str = Field(..., description="工作流ID")
    input_params: Dict[str, Any] = Field(..., description="输入参数")


class ComfyUITaskResponse(BaseModel):
    """ComfyUI任务响应"""

    id: str
    user_id: str
    workflow_id: str
    generate_uuid: Optional[str] = None
    input_params: Dict[str, Any]
    template_uuid: str
    workflow_uuid: str
    status: str
    generate_status: Optional[int] = None
    percent_completed: float
    output_images: Optional[List[Dict[str, Any]]] = None
    output_videos: Optional[List[Dict[str, Any]]] = None
    cloud_images: Optional[List[str]] = None
    cloud_videos: Optional[List[str]] = None
    credits_cost: Optional[int] = None
    generation_time: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


# ======================== SQLAlchemy 数据库模型 ========================


class ComfyUIConfig(Base):
    """ComfyUI配置表"""

    __tablename__ = "comfyui_config"

    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    access_key = Column(Text, nullable=False, comment="哩布API访问凭证")
    secret_key = Column(Text, nullable=False, comment="哩布API访问密钥")
    base_url = Column(
        String(500),
        nullable=False,
        default="https://openapi.liblibai.cloud",
        comment="API基础URL",
    )
    enabled = Column(Boolean, nullable=False, default=False, comment="启用状态")
    timeout = Column(Integer, nullable=False, default=300, comment="请求超时时间（秒）")
    max_concurrent_tasks = Column(
        Integer, nullable=False, default=5, comment="最大并发任务数"
    )

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
            "access_key": (
                self.access_key[:8] + "****" if self.access_key else None
            ),  # 隐藏敏感信息
            "secret_key": (
                self.secret_key[:8] + "****" if self.secret_key else None
            ),  # 隐藏敏感信息
            "base_url": self.base_url,
            "enabled": self.enabled,
            "timeout": self.timeout,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ComfyUIWorkflow(Base):
    """ComfyUI工作流管理表"""

    __tablename__ = "comfyui_workflows"

    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_uuid = Column(String(255), nullable=False, comment="哩布模板UUID")
    workflow_uuid = Column(String(255), nullable=False, comment="哩布工作流UUID")
    name = Column(String(255), nullable=False, comment="工作流名称")
    description = Column(Text, nullable=True, comment="工作流描述")
    category = Column(String(100), nullable=True, comment="分类")
    preview_image = Column(Text, nullable=True, comment="预览图URL")

    # 参数配置
    parameter_schema = Column(JSON, nullable=False, comment="参数结构定义")
    default_params = Column(JSON, nullable=True, comment="默认参数值")

    # 积分配置
    base_credits = Column(Integer, nullable=False, default=10, comment="基础积分消耗")
    complexity_multiplier = Column(
        Float, nullable=False, default=1.0, comment="复杂度系数"
    )

    # 状态配置
    enabled = Column(Boolean, nullable=False, default=True, comment="启用状态")
    is_public = Column(Boolean, nullable=False, default=False, comment="是否公开显示")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序权重")

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

    # 复合索引
    __table_args__ = (
        Index("idx_comfyui_workflows_public_enabled", "is_public", "enabled"),
        Index("idx_comfyui_workflows_category", "category"),
    )

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "template_uuid": self.template_uuid,
            "workflow_uuid": self.workflow_uuid,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "preview_image": self.preview_image,
            "parameter_schema": self.parameter_schema,
            "default_params": self.default_params,
            "base_credits": self.base_credits,
            "complexity_multiplier": self.complexity_multiplier,
            "enabled": self.enabled,
            "is_public": self.is_public,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ComfyUITask(Base):
    """ComfyUI任务执行表"""

    __tablename__ = "comfyui_tasks"

    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True, comment="用户ID")
    workflow_id = Column(String(255), nullable=False, comment="工作流ID")
    generate_uuid = Column(
        String(255), nullable=True, index=True, comment="哩布API返回的任务UUID"
    )

    # 任务参数
    input_params = Column(JSON, nullable=False, comment="输入参数")
    template_uuid = Column(String(255), nullable=False, comment="模板UUID")
    workflow_uuid = Column(String(255), nullable=False, comment="工作流UUID")

    # 任务状态
    status = Column(String(20), nullable=False, default="PENDING", comment="任务状态")
    generate_status = Column(Integer, nullable=True, comment="哩布返回的状态码")
    percent_completed = Column(Float, nullable=False, default=0.0, comment="完成进度")

    # 结果数据
    output_images = Column(JSON, nullable=True, comment="输出图片列表")
    output_videos = Column(JSON, nullable=True, comment="输出视频列表")
    cloud_images = Column(JSON, nullable=True, comment="云存储图片URLs")
    cloud_videos = Column(JSON, nullable=True, comment="云存储视频URLs")

    # 消耗信息
    credits_cost = Column(Integer, nullable=True, comment="积分消耗")
    generation_time = Column(Float, nullable=True, comment="生成耗时")

    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    retry_count = Column(Integer, nullable=False, default=0, comment="重试次数")
    liblib_response = Column(JSON, nullable=True, comment="哩布API原始响应")

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
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 复合索引
    __table_args__ = (
        Index("idx_comfyui_tasks_user_status", "user_id", "status"),
        Index("idx_comfyui_tasks_workflow_status", "workflow_id", "status"),
    )

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "workflow_id": self.workflow_id,
            "generate_uuid": self.generate_uuid,
            "input_params": self.input_params,
            "template_uuid": self.template_uuid,
            "workflow_uuid": self.workflow_uuid,
            "status": self.status,
            "generate_status": self.generate_status,
            "percent_completed": self.percent_completed,
            "output_images": self.output_images,
            "output_videos": self.output_videos,
            "cloud_images": self.cloud_images,
            "cloud_videos": self.cloud_videos,
            "credits_cost": self.credits_cost,
            "generation_time": self.generation_time,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    def update_from_liblib_response(self, liblib_response: Dict[str, Any]):
        """从哩布API响应更新任务信息"""
        import logging

        logger = logging.getLogger(__name__)

        if liblib_response is None:
            return

        # 保存原始响应
        self.liblib_response = liblib_response
        self.updated_at = func.now()

        # 更新状态
        if "generateStatus" in liblib_response:
            raw_status = liblib_response["generateStatus"]
            # 状态映射：1等待执行, 2执行中, 3已生图, 4审核中, 5任务成功, 6任务失败
            status_mapping = {
                1: "PENDING",  # 等待执行
                2: "IN_PROGRESS",  # 执行中
                3: "PROCESSING",  # 已生图
                4: "PROCESSING",  # 审核中
                5: "SUCCESS",  # 任务成功
                6: "FAILED",  # 任务失败
            }
            self.status = status_mapping.get(raw_status, "UNKNOWN")
            self.generate_status = raw_status

        # 更新进度
        if "percentCompleted" in liblib_response:
            self.percent_completed = liblib_response["percentCompleted"]

        # 更新结果
        if "images" in liblib_response and liblib_response["images"]:
            self.output_images = liblib_response["images"]
            if self.status != "FAILED":
                self.status = "SUCCESS"
                self.completed_at = func.now()

        if "videos" in liblib_response and liblib_response["videos"]:
            self.output_videos = liblib_response["videos"]

        # 更新积分消耗
        if "pointsCost" in liblib_response:
            self.credits_cost = liblib_response["pointsCost"]

        # 处理错误信息
        if self.status == "FAILED":
            error_msg = None
            # 尝试从不同字段获取错误信息
            if "generateMsg" in liblib_response:
                error_msg = liblib_response["generateMsg"]
            elif "failMessage" in liblib_response:
                error_msg = liblib_response["failMessage"]
            elif "message" in liblib_response:
                error_msg = liblib_response["message"]
            elif "error" in liblib_response:
                error_msg = liblib_response["error"]

            if error_msg:
                self.error_message = str(error_msg)
                logger.info(f"任务失败，错误信息: {error_msg}")

            # 退还积分（如果还没有退还过）
            if self.credits_cost and not hasattr(self, "_refund_processed"):
                try:
                    from open_webui.models.credits import (
                        Credits,
                        AddCreditForm,
                        SetCreditFormDetail,
                    )
                    from decimal import Decimal

                    add_form = AddCreditForm(
                        user_id=self.user_id,
                        amount=Decimal(self.credits_cost),
                        detail=SetCreditFormDetail(
                            desc=f"ComfyUI任务失败退还积分: {error_msg or '任务执行失败'}",
                            api_path="/api/v1/comfyui/tasks",
                            api_params={"task_id": self.id, "action": "refund"},
                            usage={"credits_refunded": self.credits_cost},
                        ),
                    )

                    updated_credits = Credits.add_credit_by_user_id(add_form)
                    if updated_credits:
                        logger.info(
                            f"💰 任务 {self.id} 失败，已退还 {self.credits_cost} 积分给用户 {self.user_id}"
                        )
                        # 标记已处理退费，避免重复退费
                        self._refund_processed = True
                    else:
                        logger.error(f"💰 任务 {self.id} 失败，退还积分失败")
                except Exception as refund_error:
                    logger.error(
                        f"💰 任务 {self.id} 失败，退还积分时出错: {refund_error}"
                    )
            else:
                self.error_message = "任务执行失败，详情请查看原始响应"
                logger.warning(f"任务失败但无错误信息，原始响应: {liblib_response}")


# ======================== 数据库操作类 ========================


class ComfyUIConfigs:
    """ComfyUI配置数据库操作类"""

    @staticmethod
    def get_config() -> Optional[ComfyUIConfig]:
        """获取ComfyUI配置"""
        with get_db() as db:
            return db.query(ComfyUIConfig).first()

    @staticmethod
    def create_or_update_config(form: ComfyUIConfigForm) -> ComfyUIConfig:
        """创建或更新ComfyUI配置"""
        with get_db() as db:
            config = db.query(ComfyUIConfig).first()

            if config:
                # 更新现有配置
                config.access_key = form.access_key
                config.secret_key = form.secret_key
                config.base_url = form.base_url
                config.enabled = form.enabled
                config.timeout = form.timeout
                config.max_concurrent_tasks = form.max_concurrent_tasks
                config.updated_at = func.now()
            else:
                # 创建新配置
                config = ComfyUIConfig(
                    access_key=form.access_key,
                    secret_key=form.secret_key,
                    base_url=form.base_url,
                    enabled=form.enabled,
                    timeout=form.timeout,
                    max_concurrent_tasks=form.max_concurrent_tasks,
                )
                db.add(config)

            db.commit()
            db.refresh(config)
            return config


class ComfyUIWorkflows:
    """ComfyUI工作流数据库操作类"""

    @staticmethod
    def create_workflow(form: ComfyUIWorkflowForm) -> ComfyUIWorkflow:
        """创建工作流"""
        with get_db() as db:
            workflow = ComfyUIWorkflow(**form.model_dump())
            db.add(workflow)
            db.commit()
            db.refresh(workflow)
            return workflow

    @staticmethod
    def get_workflow_by_id(workflow_id: str) -> Optional[ComfyUIWorkflow]:
        """根据ID获取工作流"""
        with get_db() as db:
            return (
                db.query(ComfyUIWorkflow)
                .filter(ComfyUIWorkflow.id == workflow_id)
                .first()
            )

    @staticmethod
    def get_public_workflows(category: Optional[str] = None) -> List[ComfyUIWorkflow]:
        """获取公开工作流列表"""
        with get_db() as db:
            query = db.query(ComfyUIWorkflow).filter(
                ComfyUIWorkflow.is_public == True, ComfyUIWorkflow.enabled == True
            )

            if category:
                query = query.filter(ComfyUIWorkflow.category == category)

            return query.order_by(
                ComfyUIWorkflow.sort_order.desc(), ComfyUIWorkflow.created_at.desc()
            ).all()

    @staticmethod
    def get_all_workflows() -> List[ComfyUIWorkflow]:
        """获取所有工作流（管理员用）"""
        with get_db() as db:
            return (
                db.query(ComfyUIWorkflow)
                .order_by(ComfyUIWorkflow.created_at.desc())
                .all()
            )

    @staticmethod
    def update_workflow(
        workflow_id: str, form: ComfyUIWorkflowForm
    ) -> Optional[ComfyUIWorkflow]:
        """更新工作流"""
        with get_db() as db:
            workflow = (
                db.query(ComfyUIWorkflow)
                .filter(ComfyUIWorkflow.id == workflow_id)
                .first()
            )
            if not workflow:
                return None

            for key, value in form.model_dump().items():
                setattr(workflow, key, value)
            workflow.updated_at = func.now()

            db.commit()
            db.refresh(workflow)
            return workflow

    @staticmethod
    def delete_workflow(workflow_id: str) -> bool:
        """删除工作流"""
        with get_db() as db:
            workflow = (
                db.query(ComfyUIWorkflow)
                .filter(ComfyUIWorkflow.id == workflow_id)
                .first()
            )
            if not workflow:
                return False

            db.delete(workflow)
            db.commit()
            return True


class ComfyUITasks:
    """ComfyUI任务数据库操作类"""

    @staticmethod
    def create_task(
        user_id: str, workflow_id: str, input_params: Dict[str, Any]
    ) -> ComfyUITask:
        """创建任务"""
        with get_db() as db:
            # 获取工作流信息
            workflow = (
                db.query(ComfyUIWorkflow)
                .filter(ComfyUIWorkflow.id == workflow_id)
                .first()
            )
            if not workflow:
                raise ValueError(f"工作流 {workflow_id} 不存在")

            task = ComfyUITask(
                user_id=user_id,
                workflow_id=workflow_id,
                input_params=input_params,
                template_uuid=workflow.template_uuid,
                workflow_uuid=workflow.workflow_uuid,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    @staticmethod
    def get_task_by_id(task_id: str) -> Optional[ComfyUITask]:
        """根据ID获取任务"""
        with get_db() as db:
            return db.query(ComfyUITask).filter(ComfyUITask.id == task_id).first()

    @staticmethod
    def get_task_by_generate_uuid(generate_uuid: str) -> Optional[ComfyUITask]:
        """根据generate_uuid获取任务"""
        with get_db() as db:
            return (
                db.query(ComfyUITask)
                .filter(ComfyUITask.generate_uuid == generate_uuid)
                .first()
            )

    @staticmethod
    def get_user_tasks(
        user_id: str, page: int = 1, limit: int = 20, status: Optional[str] = None
    ) -> List[ComfyUITask]:
        """获取用户任务列表"""
        with get_db() as db:
            query = db.query(ComfyUITask).filter(ComfyUITask.user_id == user_id)

            if status:
                query = query.filter(ComfyUITask.status == status)

            return (
                query.order_by(ComfyUITask.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )

    @staticmethod
    def update_task_status(task_id: str, status: str, **kwargs) -> bool:
        """更新任务状态"""
        with get_db() as db:
            task = db.query(ComfyUITask).filter(ComfyUITask.id == task_id).first()
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


# ======================== 强制表检查机制 ========================


def _ensure_comfyui_tables():
    """确保ComfyUI相关表存在"""
    from open_webui.internal.db import SessionLocal
    from sqlalchemy import inspect, text

    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        existing_tables = inspector.get_table_names()

        # 检查必需的表（移除独立积分表）
        required_tables = ["comfyui_config", "comfyui_workflows", "comfyui_tasks"]
        missing_tables = [
            table for table in required_tables if table not in existing_tables
        ]

        if missing_tables:
            print(f"🔧 检测到缺失的ComfyUI表: {missing_tables}")

            # 创建表
            Base.metadata.create_all(
                db.bind,
                tables=[
                    ComfyUIConfig.__table__,
                    ComfyUIWorkflow.__table__,
                    ComfyUITask.__table__,
                ],
            )
            print("🎨 ComfyUI表已创建")

            # 检查是否需要创建默认配置
            config_count = db.execute(
                text("SELECT COUNT(*) FROM comfyui_config")
            ).scalar()
            if config_count == 0:
                # 插入默认配置
                db.execute(
                    text(
                        """
                    INSERT INTO comfyui_config 
                    (id, access_key, secret_key, base_url, enabled, timeout, max_concurrent_tasks, created_at, updated_at) 
                    VALUES 
                    ('default', '', '', 'https://openapi.liblibai.cloud', 1, 300, 5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                    )
                )
                db.commit()
                print("🎨 默认ComfyUI配置已创建")

    except Exception as e:
        print(f"🔧 ComfyUI表检查过程中出错: {e}")
        # 回滚以防出错
        db.rollback()
    finally:
        db.close()


# ======================== 工具函数 ========================


def get_comfyui_config() -> Optional[ComfyUIConfig]:
    """获取当前ComfyUI配置"""
    return ComfyUIConfigs.get_config()


def is_comfyui_enabled() -> bool:
    """检查ComfyUI是否启用"""
    config = get_comfyui_config()
    return config is not None and config.enabled


def calculate_workflow_credits(
    workflow: ComfyUIWorkflow, params: Dict[str, Any]
) -> int:
    """计算工作流积分消耗"""
    base_credits = workflow.base_credits
    multiplier = workflow.complexity_multiplier

    # 基于参数动态调整
    param_multiplier = 1.0

    # 图片尺寸影响
    for node_id, node_data in params.items():
        if isinstance(node_data, dict) and "inputs" in node_data:
            inputs = node_data["inputs"]

            # 检查图片尺寸参数
            if "width" in inputs and "height" in inputs:
                try:
                    width = int(inputs["width"])
                    height = int(inputs["height"])
                    pixel_count = width * height
                    param_multiplier *= max(pixel_count / (512 * 512), 0.5)
                except (ValueError, TypeError):
                    pass

            # 检查推理步数
            if "steps" in inputs:
                try:
                    steps = int(inputs["steps"])
                    param_multiplier *= max(steps / 20, 0.5)
                except (ValueError, TypeError):
                    pass

    final_credits = int(base_credits * multiplier * param_multiplier)
    return max(final_credits, 1)  # 最少1积分


# 应用启动时自动检查表
try:
    _ensure_comfyui_tables()
except Exception as e:
    print(f"🔧 ComfyUI表自动检查失败: {e}")
