"""add google images tables

Revision ID: j6k7l8m9n0p1
Revises: i5j6k7l8m9n0
Create Date: 2025-08-29 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = "j6k7l8m9n0p1"
down_revision: Union[str, None] = "i5j6k7l8m9n0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建谷歌生图相关表"""

    # 创建谷歌生图配置表
    op.create_table(
        "google_images_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("api_key", sa.Text(), nullable=True),
        # 模型配置
        sa.Column(
            "default_model", sa.String(length=50), nullable=False, default="nano-banana"
        ),
        sa.Column("max_images_per_request", sa.Integer(), nullable=False, default=10),
        sa.Column("timeout", sa.Integer(), nullable=False, default=60),
        # 积分配置
        sa.Column("credits_per_generation", sa.Integer(), nullable=False, default=20),
        sa.Column("credits_per_image", sa.Integer(), nullable=False, default=5),
        # 扩展配置
        sa.Column("additional_config", sa.JSON(), nullable=True),
        # 时间戳字段
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_google_images_config_id"),
        "google_images_config",
        ["id"],
        unique=False,
    )

    # 插入默认配置
    op.execute(
        """
        INSERT INTO google_images_config (
            enabled, default_model, max_images_per_request,
            timeout, credits_per_generation, credits_per_image
        ) VALUES (
            0, 'nano-banana', 10, 60, 20, 5
        )
    """
    )

    # 创建谷歌生图任务表
    op.create_table(
        "google_images_tasks",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, default="submitted"),
        # 请求参数
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=False, default="nano-banana"),
        sa.Column("size", sa.String(length=20), nullable=True),
        sa.Column("quality", sa.String(length=20), nullable=True),
        sa.Column("style", sa.String(length=20), nullable=True),
        # 图片数据
        sa.Column("input_images", sa.JSON(), nullable=True),  # 原始输入图片
        sa.Column("cloud_input_images", sa.JSON(), nullable=True),  # 云端输入图片URL
        sa.Column("result_images", sa.JSON(), nullable=True),  # 原始结果图片
        sa.Column("cloud_result_images", sa.JSON(), nullable=True),  # 云端结果图片URL
        # 任务状态
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
        op.f("ix_google_images_tasks_id"),
        "google_images_tasks",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_google_images_tasks_user_id"),
        "google_images_tasks",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_google_images_tasks_status"),
        "google_images_tasks",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_google_images_tasks_created_at"),
        "google_images_tasks",
        ["created_at"],
        unique=False,
    )

    # 创建谷歌生图积分记录表
    op.create_table(
        "google_images_credits",
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
        op.f("ix_google_images_credits_id"),
        "google_images_credits",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_google_images_credits_user_id"),
        "google_images_credits",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_google_images_credits_task_id"),
        "google_images_credits",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_google_images_credits_created_at"),
        "google_images_credits",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """删除谷歌生图相关表"""

    # 删除谷歌生图积分记录表
    op.drop_index(
        op.f("ix_google_images_credits_created_at"),
        table_name="google_images_credits",
    )
    op.drop_index(
        op.f("ix_google_images_credits_task_id"),
        table_name="google_images_credits",
    )
    op.drop_index(
        op.f("ix_google_images_credits_user_id"),
        table_name="google_images_credits",
    )
    op.drop_index(
        op.f("ix_google_images_credits_id"),
        table_name="google_images_credits",
    )
    op.drop_table("google_images_credits")

    # 删除谷歌生图任务表
    op.drop_index(
        op.f("ix_google_images_tasks_created_at"),
        table_name="google_images_tasks",
    )
    op.drop_index(
        op.f("ix_google_images_tasks_status"),
        table_name="google_images_tasks",
    )
    op.drop_index(
        op.f("ix_google_images_tasks_user_id"),
        table_name="google_images_tasks",
    )
    op.drop_index(op.f("ix_google_images_tasks_id"), table_name="google_images_tasks")
    op.drop_table("google_images_tasks")

    # 删除谷歌生图配置表
    op.drop_index(op.f("ix_google_images_config_id"), table_name="google_images_config")
    op.drop_table("google_images_config")
