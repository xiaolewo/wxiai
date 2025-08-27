"""add jimeng outpainting tables

Revision ID: h4i5j6k7l8m9
Revises: g3h4i5j6k7l8
Create Date: 2025-08-26 23:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = "h4i5j6k7l8m9"
down_revision: Union[str, None] = "g3h4i5j6k7l8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建即梦智能扩图相关表"""

    # 创建即梦智能扩图配置表
    op.create_table(
        "jimeng_outpainting_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "base_url",
            sa.String(length=500),
            nullable=False,
            default="https://visual.volcengineapi.com",
        ),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("credits_cost", sa.Integer(), nullable=False, default=25),
        # 默认参数配置
        sa.Column("default_steps", sa.Integer(), nullable=False, default=30),
        sa.Column("default_strength", sa.Float(), nullable=False, default=0.8),
        sa.Column("default_scale", sa.Float(), nullable=False, default=7.0),
        sa.Column("default_quality", sa.String(length=10), nullable=False, default="M"),
        sa.Column("default_max_width", sa.Integer(), nullable=False, default=1920),
        sa.Column("default_max_height", sa.Integer(), nullable=False, default=1920),
        # 时间戳字段
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_jimeng_outpainting_config_id"),
        "jimeng_outpainting_config",
        ["id"],
        unique=False,
    )

    # 创建即梦智能扩图任务表
    op.create_table(
        "jimeng_outpainting_tasks",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        # 输入参数
        sa.Column("original_image_url", sa.Text(), nullable=False),
        sa.Column("mask_image_url", sa.Text(), nullable=True),
        sa.Column(
            "expansion_mode", sa.String(length=20), nullable=False, default="equal"
        ),
        sa.Column("custom_prompt", sa.Text(), nullable=True),
        # 扩展参数
        sa.Column("top", sa.Float(), nullable=True, default=0.1),
        sa.Column("bottom", sa.Float(), nullable=True, default=0.1),
        sa.Column("left", sa.Float(), nullable=True, default=0.1),
        sa.Column("right", sa.Float(), nullable=True, default=0.1),
        # 生成参数
        sa.Column("steps", sa.Integer(), nullable=True, default=30),
        sa.Column("strength", sa.Float(), nullable=True, default=0.8),
        sa.Column("scale", sa.Float(), nullable=True, default=7.0),
        sa.Column("seed", sa.Integer(), nullable=True, default=0),
        sa.Column("quality", sa.String(length=10), nullable=True, default="M"),
        sa.Column("max_width", sa.Integer(), nullable=True, default=1920),
        sa.Column("max_height", sa.Integer(), nullable=True, default=1920),
        # 任务状态
        sa.Column("status", sa.String(length=20), nullable=False, default="submitted"),
        sa.Column("progress", sa.String(length=10), nullable=True, default="0%"),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        # 结果
        sa.Column("result_image_url", sa.Text(), nullable=True),
        sa.Column("cloud_image_url", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        # 积分消耗
        sa.Column("credits_cost", sa.Integer(), nullable=True, default=25),
        # 时间戳
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_jimeng_outpainting_tasks_id"),
        "jimeng_outpainting_tasks",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jimeng_outpainting_tasks_user_id"),
        "jimeng_outpainting_tasks",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jimeng_outpainting_tasks_status"),
        "jimeng_outpainting_tasks",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jimeng_outpainting_tasks_created_at"),
        "jimeng_outpainting_tasks",
        ["created_at"],
        unique=False,
    )

    # 创建即梦智能扩图积分记录表
    op.create_table(
        "jimeng_outpainting_credits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("task_id", sa.String(length=50), nullable=False),
        # 积分变化
        sa.Column("credits_used", sa.Integer(), nullable=False),
        sa.Column("credits_before", sa.Integer(), nullable=False),
        sa.Column("credits_after", sa.Integer(), nullable=False),
        # 操作信息
        sa.Column(
            "operation_type",
            sa.String(length=20),
            nullable=False,
            default="outpainting",
        ),
        sa.Column("description", sa.Text(), nullable=True),
        # 时间戳
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_jimeng_outpainting_credits_id"),
        "jimeng_outpainting_credits",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jimeng_outpainting_credits_user_id"),
        "jimeng_outpainting_credits",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jimeng_outpainting_credits_task_id"),
        "jimeng_outpainting_credits",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jimeng_outpainting_credits_created_at"),
        "jimeng_outpainting_credits",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """删除即梦智能扩图相关表"""

    # 删除即梦智能扩图积分记录表
    op.drop_index(
        op.f("ix_jimeng_outpainting_credits_created_at"),
        table_name="jimeng_outpainting_credits",
    )
    op.drop_index(
        op.f("ix_jimeng_outpainting_credits_task_id"),
        table_name="jimeng_outpainting_credits",
    )
    op.drop_index(
        op.f("ix_jimeng_outpainting_credits_user_id"),
        table_name="jimeng_outpainting_credits",
    )
    op.drop_index(
        op.f("ix_jimeng_outpainting_credits_id"),
        table_name="jimeng_outpainting_credits",
    )
    op.drop_table("jimeng_outpainting_credits")

    # 删除即梦智能扩图任务表
    op.drop_index(
        op.f("ix_jimeng_outpainting_tasks_created_at"),
        table_name="jimeng_outpainting_tasks",
    )
    op.drop_index(
        op.f("ix_jimeng_outpainting_tasks_status"),
        table_name="jimeng_outpainting_tasks",
    )
    op.drop_index(
        op.f("ix_jimeng_outpainting_tasks_user_id"),
        table_name="jimeng_outpainting_tasks",
    )
    op.drop_index(
        op.f("ix_jimeng_outpainting_tasks_id"), table_name="jimeng_outpainting_tasks"
    )
    op.drop_table("jimeng_outpainting_tasks")

    # 删除即梦智能扩图配置表
    op.drop_index(
        op.f("ix_jimeng_outpainting_config_id"), table_name="jimeng_outpainting_config"
    )
    op.drop_table("jimeng_outpainting_config")
