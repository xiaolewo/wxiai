"""add_flux_tables

Revision ID: 22c97ff924a3
Revises: a1b2c3d4e5f8
Create Date: 2025-08-19 11:53:55.331269

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "22c97ff924a3"
down_revision: Union[str, None] = "a1b2c3d4e5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Create Flux tables ###

    # Create flux_config table
    op.create_table(
        "flux_config",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=False, comment="Fal.ai API密钥"),
        sa.Column(
            "base_url",
            sa.String(length=500),
            nullable=False,
            default="https://queue.fal.run",
            comment="API基础URL",
        ),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, default=True, comment="启用状态"
        ),
        sa.Column(
            "timeout",
            sa.Integer(),
            nullable=False,
            default=300,
            comment="请求超时时间（秒）",
        ),
        sa.Column(
            "max_concurrent_tasks",
            sa.Integer(),
            nullable=False,
            default=5,
            comment="最大并发任务数",
        ),
        sa.Column(
            "default_model",
            sa.String(length=100),
            nullable=False,
            default="fal-ai/flux-1/dev",
            comment="默认模型",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create flux_tasks table
    op.create_table(
        "flux_tasks",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False, comment="用户ID"),
        sa.Column(
            "request_id", sa.String(length=255), nullable=False, comment="Fal.ai请求ID"
        ),
        sa.Column("model", sa.String(length=100), nullable=False, comment="使用的模型"),
        sa.Column(
            "task_type",
            sa.String(length=20),
            nullable=False,
            comment="任务类型: text_to_image, image_to_image",
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            default="PENDING",
            comment="任务状态",
        ),
        sa.Column("prompt", sa.Text(), comment="文本提示词"),
        sa.Column("input_image_url", sa.Text(), comment="输入图片URL（图生图）"),
        sa.Column("uploaded_image_url", sa.Text(), comment="用户上传后的云存储URL"),
        sa.Column("num_images", sa.Integer(), default=1, comment="生成图片数量"),
        sa.Column(
            "aspect_ratio", sa.String(length=20), default="1:1", comment="宽高比"
        ),
        sa.Column("guidance_scale", sa.Float(), default=3.5, comment="引导系数"),
        sa.Column("num_inference_steps", sa.Integer(), default=28, comment="推理步数"),
        sa.Column("seed", sa.Integer(), comment="随机种子"),
        sa.Column(
            "safety_tolerance", sa.String(length=10), default="2", comment="安全容忍度"
        ),
        sa.Column("strength", sa.Float(), default=0.95, comment="图生图强度"),
        sa.Column("sync_mode", sa.Boolean(), default=False, comment="同步模式"),
        sa.Column(
            "output_format", sa.String(length=10), default="jpeg", comment="输出格式"
        ),
        sa.Column(
            "enable_safety_checker", sa.Boolean(), default=True, comment="启用安全检查"
        ),
        sa.Column("image_url", sa.Text(), comment="生成的图片URL"),
        sa.Column("cloud_image_url", sa.Text(), comment="云存储图片URL"),
        sa.Column("generation_time", sa.Float(), comment="生成耗时（秒）"),
        sa.Column("queue_position", sa.Integer(), comment="队列位置"),
        sa.Column("error_message", sa.Text(), comment="错误信息"),
        sa.Column("retry_count", sa.Integer(), default=0, comment="重试次数"),
        sa.Column("flux_response", sa.JSON(), comment="Flux API原始响应"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="更新时间",
        ),
        sa.Column("completed_at", sa.DateTime(), comment="完成时间"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create flux_credits table
    op.create_table(
        "flux_credits",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False, comment="用户ID"),
        sa.Column(
            "credits_balance",
            sa.Integer(),
            nullable=False,
            default=0,
            comment="剩余积分",
        ),
        sa.Column(
            "total_used", sa.Integer(), nullable=False, default=0, comment="已使用积分"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for flux_tasks
    op.create_index("idx_flux_tasks_user_status", "flux_tasks", ["user_id", "status"])
    op.create_index("idx_flux_tasks_model_status", "flux_tasks", ["model", "status"])
    op.create_index("idx_flux_tasks_user_id", "flux_tasks", ["user_id"])
    op.create_index("idx_flux_tasks_status", "flux_tasks", ["status"])
    op.create_index("idx_flux_tasks_request_id", "flux_tasks", ["request_id"])
    op.create_index("idx_flux_tasks_created_at", "flux_tasks", ["created_at"])

    # Create indexes for flux_credits
    op.create_index("idx_flux_credits_user_id", "flux_credits", ["user_id"])

    # ### end Flux tables creation ###


def downgrade() -> None:
    # ### Drop Flux tables and indexes ###

    # Drop indexes first
    op.drop_index("idx_flux_credits_user_id", table_name="flux_credits")
    op.drop_index("idx_flux_tasks_created_at", table_name="flux_tasks")
    op.drop_index("idx_flux_tasks_request_id", table_name="flux_tasks")
    op.drop_index("idx_flux_tasks_status", table_name="flux_tasks")
    op.drop_index("idx_flux_tasks_user_id", table_name="flux_tasks")
    op.drop_index("idx_flux_tasks_model_status", table_name="flux_tasks")
    op.drop_index("idx_flux_tasks_user_status", table_name="flux_tasks")

    # Drop tables
    op.drop_table("flux_credits")
    op.drop_table("flux_tasks")
    op.drop_table("flux_config")

    # ### end Flux tables removal ###
