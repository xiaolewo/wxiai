"""Add Seedance (新即梦) video tables

Revision ID: s2e3d4a5b6c7
Revises: m6b8d9e0f1a2
Create Date: 2025-03-10 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "s2e3d4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "m6b8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "seedance_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("base_url", sa.String(length=500)),
        sa.Column("api_key", sa.Text()),
        sa.Column("default_model", sa.String(length=100)),
        sa.Column("default_duration", sa.String(length=10)),
        sa.Column("default_resolution", sa.String(length=20)),
        sa.Column("default_ratio", sa.String(length=20)),
        sa.Column(
            "default_watermark",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "default_camera_fixed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "default_return_last_frame",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("credits_per_5s", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("credits_per_10s", sa.Integer(), nullable=False, server_default="80"),
        sa.Column(
            "max_concurrent_tasks", sa.Integer(), nullable=False, server_default="5"
        ),
        sa.Column(
            "task_timeout", sa.Integer(), nullable=False, server_default="600000"
        ),
        sa.Column(
            "query_interval", sa.Integer(), nullable=False, server_default="10000"
        ),
        sa.Column("model_credits_config", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "seedance_tasks",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("external_task_id", sa.String(length=100)),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("task_status_msg", sa.Text()),
        sa.Column("prompt", sa.Text()),
        sa.Column("model", sa.String(length=100)),
        sa.Column("duration", sa.String(length=10)),
        sa.Column("resolution", sa.String(length=20)),
        sa.Column("ratio", sa.String(length=20)),
        sa.Column("watermark", sa.Boolean()),
        sa.Column("seed", sa.Integer()),
        sa.Column("camera_fixed", sa.Boolean()),
        sa.Column("return_last_frame", sa.Boolean()),
        sa.Column("images", sa.JSON()),
        sa.Column("credits_cost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("submit_time", sa.DateTime()),
        sa.Column("start_time", sa.DateTime()),
        sa.Column("finish_time", sa.DateTime()),
        sa.Column("video_url", sa.Text()),
        sa.Column("cloud_video_url", sa.Text()),
        sa.Column("last_frame_url", sa.Text()),
        sa.Column("cloud_last_frame_url", sa.Text()),
        sa.Column("progress", sa.String(length=20), server_default="0%"),
        sa.Column("fail_reason", sa.Text()),
        sa.Column("request_data", sa.Text()),
        sa.Column("response_data", sa.Text()),
        sa.Column("properties", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    op.create_index("ix_seedance_tasks_user_id", "seedance_tasks", ["user_id"])
    op.create_index("ix_seedance_tasks_status", "seedance_tasks", ["status"])
    op.create_index(
        "ix_seedance_tasks_external_task_id",
        "seedance_tasks",
        ["external_task_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_seedance_tasks_external_task_id", table_name="seedance_tasks")
    op.drop_index("ix_seedance_tasks_status", table_name="seedance_tasks")
    op.drop_index("ix_seedance_tasks_user_id", table_name="seedance_tasks")
    op.drop_table("seedance_tasks")
    op.drop_table("seedance_config")
