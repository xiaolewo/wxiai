"""
创建Midjourney相关数据表
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


def upgrade():
    # 创建 mj_config 表
    op.create_table(
        "mj_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=True, default=False),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("modes", sa.JSON(), nullable=True),
        sa.Column("default_mode", sa.String(50), nullable=True, default="fast"),
        sa.Column("max_concurrent_tasks", sa.Integer(), nullable=True, default=5),
        sa.Column("task_timeout", sa.Integer(), nullable=True, default=300000),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建 mj_tasks 表
    op.create_table(
        "mj_tasks",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=True),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=True, default="SUBMITTED"),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("prompt_en", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mode", sa.String(50), nullable=True, default="fast"),
        sa.Column("credits_cost", sa.Integer(), nullable=True, default=0),
        sa.Column("submit_time", sa.DateTime(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("finish_time", sa.DateTime(), nullable=True),
        sa.Column("progress", sa.String(20), nullable=True, default="0%"),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("properties", sa.JSON(), nullable=True),
        sa.Column("buttons", sa.JSON(), nullable=True),
        sa.Column("parent_task_id", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建索引
    op.create_index("idx_user_created", "mj_tasks", ["user_id", "created_at"])
    op.create_index("idx_status_updated", "mj_tasks", ["status", "updated_at"])
    op.create_index("ix_mj_tasks_user_id", "mj_tasks", ["user_id"])

    # 创建 mj_credits 表
    op.create_table(
        "mj_credits",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=True),
        sa.Column("balance", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("task_id", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建积分表索引
    op.create_index("idx_user_created_credits", "mj_credits", ["user_id", "created_at"])
    op.create_index("ix_mj_credits_user_id", "mj_credits", ["user_id"])


def downgrade():
    # 删除表
    op.drop_table("mj_credits")
    op.drop_table("mj_tasks")
    op.drop_table("mj_config")
