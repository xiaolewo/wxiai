"""add veo tables

Revision ID: i5j6k7l8m9n0
Revises: h4i5j6k7l8m9
Create Date: 2025-08-28 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = "i5j6k7l8m9n0"
down_revision: Union[str, None] = "h4i5j6k7l8m9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建Veo视频生成相关表"""

    # 创建Veo配置表
    op.create_table(
        "veo_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "base_url",
            sa.String(length=500),
            nullable=False,
            default="https://api.veoai.com",
        ),
        sa.Column("api_key", sa.Text(), nullable=True),
        
        # 模型积分配置 - JSON格式支持灵活配置
        sa.Column("model_credits_config", sa.JSON(), nullable=True),
        
        # 默认参数配置
        sa.Column("default_model", sa.String(length=50), nullable=False, default="veo3"),
        sa.Column("default_enhance_prompt", sa.Boolean(), nullable=False, default=True),
        
        # 系统配置
        sa.Column("max_concurrent_tasks", sa.Integer(), nullable=False, default=3),
        sa.Column("task_timeout", sa.Integer(), nullable=False, default=900000),
        sa.Column("query_interval", sa.Integer(), nullable=False, default=15000),
        
        # 时间戳字段
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_veo_config_id"),
        "veo_config",
        ["id"],
        unique=False,
    )

    # 插入默认配置
    op.execute("""
        INSERT INTO veo_config (
            enabled, base_url, default_model, default_enhance_prompt,
            max_concurrent_tasks, task_timeout, query_interval,
            model_credits_config
        ) VALUES (
            0, 'https://api.veoai.com', 'veo3', 1,
            3, 900000, 15000,
            '{"veo3": 100, "veo3-fast": 80, "veo3-pro": 150, "veo3-pro-frames": 200, "veo2": 90, "veo2-fast": 70, "veo2-fast-frames": 120, "veo2-fast-components": 160, "veo2-pro": 140}'
        )
    """)

    # 创建Veo任务表
    op.create_table(
        "veo_tasks",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, default="submitted"),
        
        # 输入参数
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=False),
        sa.Column("enhance_prompt", sa.Boolean(), nullable=False, default=True),
        sa.Column("input_images", sa.JSON(), nullable=True),  # 原始图片URL数组
        
        # 云存储相关
        sa.Column("cloud_input_images", sa.JSON(), nullable=True),  # 云端图片URL数组
        sa.Column("result_video_url", sa.Text(), nullable=True),    # 原始视频URL
        sa.Column("cloud_video_url", sa.Text(), nullable=True),     # 云端视频URL
        
        # 任务状态
        sa.Column("external_task_id", sa.String(length=100), nullable=True),
        sa.Column("progress", sa.String(length=10), nullable=True, default="0%"),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        
        # 积分消耗
        sa.Column("credits_cost", sa.Integer(), nullable=True),
        
        # 扩展属性
        sa.Column("properties", sa.JSON(), nullable=True),
        
        # 时间戳
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("finish_time", sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint("id"),
    )
    
    # 创建任务表索引
    op.create_index(
        op.f("ix_veo_tasks_id"),
        "veo_tasks",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_veo_tasks_user_id"),
        "veo_tasks",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_veo_tasks_status"),
        "veo_tasks",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_veo_tasks_created_at"),
        "veo_tasks",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_veo_tasks_external_task_id"),
        "veo_tasks",
        ["external_task_id"],
        unique=False,
    )

    # 创建Veo积分记录表
    op.create_table(
        "veo_credits",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("task_id", sa.String(length=50), nullable=False),
        
        # 积分变化
        sa.Column("credit_amount", sa.Integer(), nullable=False),
        sa.Column("credits_before", sa.Integer(), nullable=True),
        sa.Column("credits_after", sa.Integer(), nullable=True),
        
        # 操作信息
        sa.Column(
            "operation_type",
            sa.String(length=20),
            nullable=False,
            default="deduct",
        ),
        sa.Column("model_name", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        
        # 时间戳
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        
        sa.PrimaryKeyConstraint("id"),
    )
    
    # 创建积分记录表索引
    op.create_index(
        op.f("ix_veo_credits_id"),
        "veo_credits",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_veo_credits_user_id"),
        "veo_credits",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_veo_credits_task_id"),
        "veo_credits",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_veo_credits_created_at"),
        "veo_credits",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """删除Veo视频生成相关表"""

    # 删除Veo积分记录表
    op.drop_index(
        op.f("ix_veo_credits_created_at"),
        table_name="veo_credits",
    )
    op.drop_index(
        op.f("ix_veo_credits_task_id"),
        table_name="veo_credits",
    )
    op.drop_index(
        op.f("ix_veo_credits_user_id"),
        table_name="veo_credits",
    )
    op.drop_index(
        op.f("ix_veo_credits_id"),
        table_name="veo_credits",
    )
    op.drop_table("veo_credits")

    # 删除Veo任务表
    op.drop_index(
        op.f("ix_veo_tasks_external_task_id"),
        table_name="veo_tasks",
    )
    op.drop_index(
        op.f("ix_veo_tasks_created_at"),
        table_name="veo_tasks",
    )
    op.drop_index(
        op.f("ix_veo_tasks_status"),
        table_name="veo_tasks",
    )
    op.drop_index(
        op.f("ix_veo_tasks_user_id"),
        table_name="veo_tasks",
    )
    op.drop_index(
        op.f("ix_veo_tasks_id"), 
        table_name="veo_tasks"
    )
    op.drop_table("veo_tasks")

    # 删除Veo配置表
    op.drop_index(
        op.f("ix_veo_config_id"), 
        table_name="veo_config"
    )
    op.drop_table("veo_config")