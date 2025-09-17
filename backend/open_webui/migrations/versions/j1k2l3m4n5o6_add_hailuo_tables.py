"""add hailuo tables

Revision ID: j1k2l3m4n5o6
Revises: i5j6k7l8m9n0
Create Date: 2025-09-17 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "j1k2l3m4n5o6"
down_revision: Union[str, None] = "i5j6k7l8m9n0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # hailuo_config
    op.create_table(
        "hailuo_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "base_url",
            sa.String(length=500),
            nullable=False,
            server_default="https://api.minimaxi.com",
        ),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column(
            "default_model",
            sa.String(length=64),
            nullable=False,
            server_default="MiniMax-Hailuo-02",
        ),
        sa.Column("default_duration", sa.Integer(), nullable=False, server_default="6"),
        sa.Column(
            "default_resolution",
            sa.String(length=16),
            nullable=False,
            server_default="768P",
        ),
        sa.Column(
            "prompt_optimizer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("model_credits_config", sa.JSON(), nullable=True),
        sa.Column(
            "max_concurrent_tasks", sa.Integer(), nullable=False, server_default="3"
        ),
        sa.Column(
            "task_timeout_ms", sa.Integer(), nullable=False, server_default="900000"
        ),
        sa.Column(
            "query_interval_ms", sa.Integer(), nullable=False, server_default="10000"
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # insert default row
    op.execute(
        """
        INSERT INTO hailuo_config (
            id, enabled, base_url, default_model, default_duration, default_resolution,
            prompt_optimizer, max_concurrent_tasks, task_timeout_ms, query_interval_ms
        ) VALUES (1, 0, 'https://api.minimaxi.com', 'MiniMax-Hailuo-02', 6, '768P', 1, 3, 900000, 10000)
        """
    )

    # hailuo_tasks
    op.create_table(
        "hailuo_tasks",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("resolution", sa.String(length=16), nullable=False),
        sa.Column(
            "prompt_optimizer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("first_frame_url", sa.Text(), nullable=True),
        sa.Column("last_frame_url", sa.Text(), nullable=True),
        sa.Column("cloud_input_images", sa.JSON(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="submitted"
        ),
        sa.Column("progress", sa.String(length=10), nullable=True, server_default="0%"),
        sa.Column("external_task_id", sa.String(length=100), nullable=True),
        sa.Column("file_id", sa.String(length=100), nullable=True),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("result_video_url", sa.Text(), nullable=True),
        sa.Column("cloud_video_url", sa.Text(), nullable=True),
        sa.Column("credits_cost", sa.Integer(), nullable=True),
        sa.Column("properties", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("finish_time", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_hailuo_tasks_user_id", "hailuo_tasks", ["user_id"])
    op.create_index("ix_hailuo_tasks_status", "hailuo_tasks", ["status"])
    op.create_index("ix_hailuo_tasks_created_at", "hailuo_tasks", ["created_at"])
    op.create_index(
        "ix_hailuo_tasks_external_task_id", "hailuo_tasks", ["external_task_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_hailuo_tasks_external_task_id", table_name="hailuo_tasks")
    op.drop_index("ix_hailuo_tasks_created_at", table_name="hailuo_tasks")
    op.drop_index("ix_hailuo_tasks_status", table_name="hailuo_tasks")
    op.drop_index("ix_hailuo_tasks_user_id", table_name="hailuo_tasks")
    op.drop_table("hailuo_tasks")
    op.drop_table("hailuo_config")
