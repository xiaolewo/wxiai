"""add jimeng inpainting tables

Revision ID: f2g3h4i5j6k7
Revises: e1f2g3h4i5j6
Create Date: 2025-08-25 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = "f2g3h4i5j6k7"
down_revision: Union[str, None] = "e1f2g3h4i5j6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建即梦涂抹消除相关表"""

    # 创建即梦涂抹消除配置表
    op.create_table(
        "jimeng_inpainting_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "base_url",
            sa.String(length=500),
            nullable=False,
            default="https://visual.volcengineapi.com",
        ),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("credits_cost", sa.Integer(), nullable=False, default=30),
        sa.Column("default_steps", sa.Integer(), nullable=False, default=30),
        sa.Column("default_strength", sa.Float(), nullable=False, default=0.8),
        sa.Column("default_scale", sa.Float(), nullable=False, default=7.0),
        sa.Column("default_quality", sa.String(length=10), nullable=False, default="M"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 插入默认配置
    op.execute(
        "INSERT INTO jimeng_inpainting_config (enabled, base_url, credits_cost, default_steps, default_strength, default_scale, default_quality) VALUES (0, 'https://visual.volcengineapi.com', 30, 30, 0.8, 7.0, 'M')"
    )

    # 创建即梦涂抹消除任务表
    op.create_table(
        "jimeng_inpainting_tasks",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, default="submitted"),
        sa.Column("progress", sa.String(length=10), nullable=False, default="0%"),
        # 输入参数
        sa.Column("original_image_url", sa.Text(), nullable=False),
        sa.Column("mask_image_url", sa.Text(), nullable=False),
        sa.Column("steps", sa.Integer(), nullable=False, default=30),
        sa.Column("strength", sa.Float(), nullable=False, default=0.8),
        sa.Column("scale", sa.Float(), nullable=False, default=7.0),
        sa.Column("seed", sa.Integer(), nullable=False, default=0),
        sa.Column("dilate_size", sa.Integer(), nullable=False, default=15),
        sa.Column("quality", sa.String(length=10), nullable=False, default="M"),
        # 结果数据
        sa.Column("result_image_url", sa.Text(), nullable=True),
        sa.Column("cloud_image_url", sa.Text(), nullable=True),
        # 任务状态
        sa.Column("credits_cost", sa.Integer(), nullable=False, default=30),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("properties", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finish_time", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建索引
    op.create_index(
        "idx_jimeng_inpainting_user_id", "jimeng_inpainting_tasks", ["user_id"]
    )
    op.create_index(
        "idx_jimeng_inpainting_status", "jimeng_inpainting_tasks", ["status"]
    )
    op.create_index(
        "idx_jimeng_inpainting_created", "jimeng_inpainting_tasks", ["created_at"]
    )

    # 创建即梦涂抹消除积分记录表
    op.create_table(
        "jimeng_inpainting_credits",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("task_id", sa.String(length=50), nullable=False),
        sa.Column("credit_amount", sa.Integer(), nullable=False),
        sa.Column("operation_type", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建积分记录索引
    op.create_index(
        "idx_jimeng_inpainting_credit_user", "jimeng_inpainting_credits", ["user_id"]
    )
    op.create_index(
        "idx_jimeng_inpainting_credit_task", "jimeng_inpainting_credits", ["task_id"]
    )


def downgrade() -> None:
    """删除即梦涂抹消除相关表"""

    # 删除索引
    op.drop_index(
        "idx_jimeng_inpainting_credit_task", table_name="jimeng_inpainting_credits"
    )
    op.drop_index(
        "idx_jimeng_inpainting_credit_user", table_name="jimeng_inpainting_credits"
    )
    op.drop_index("idx_jimeng_inpainting_created", table_name="jimeng_inpainting_tasks")
    op.drop_index("idx_jimeng_inpainting_status", table_name="jimeng_inpainting_tasks")
    op.drop_index("idx_jimeng_inpainting_user_id", table_name="jimeng_inpainting_tasks")

    # 删除表
    op.drop_table("jimeng_inpainting_credits")
    op.drop_table("jimeng_inpainting_tasks")
    op.drop_table("jimeng_inpainting_config")
