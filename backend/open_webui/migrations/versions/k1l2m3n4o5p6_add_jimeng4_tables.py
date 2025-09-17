"""add jimeng4 tables

Revision ID: k1l2m3n4o5p6
Revises: g3h4i5j6k7l8_merge_all_heads_final
Create Date: 2025-01-05 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "k1l2m3n4o5p6"
down_revision: Union[str, None] = "g3h4i5j6k7l8_merge_all_heads_final"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jimeng4_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("base_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("api_key", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "default_model",
            sa.String(length=200),
            nullable=False,
            server_default="doubao-seedream-4-0-250828",
        ),
        sa.Column(
            "default_size", sa.String(length=50), nullable=False, server_default="2K"
        ),
        sa.Column(
            "default_watermark", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "default_sequential_mode",
            sa.String(length=50),
            nullable=False,
            server_default="auto",
        ),
        sa.Column("default_n", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "credits_per_image", sa.Integer(), nullable=False, server_default="30"
        ),
        sa.Column(
            "max_concurrent_tasks", sa.Integer(), nullable=False, server_default="5"
        ),
        sa.Column(
            "task_timeout", sa.Integer(), nullable=False, server_default="300000"
        ),
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

    op.create_table(
        "jimeng4_tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="submitted"
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("size", sa.String(length=50), nullable=False),
        sa.Column("sequential_mode", sa.String(length=50), nullable=True),
        sa.Column("n", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("request_image_urls", sa.JSON(), nullable=True),
        sa.Column("response_format", sa.String(length=50), nullable=True),
        sa.Column("stream", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("watermark", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("response_urls", sa.JSON(), nullable=True),
        sa.Column("cloud_image_urls", sa.JSON(), nullable=True),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("usage", sa.JSON(), nullable=True),
        sa.Column("credits_cost", sa.Integer(), nullable=False, server_default="0"),
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
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_jimeng4_tasks_user_created",
        "jimeng4_tasks",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_jimeng4_tasks_status",
        "jimeng4_tasks",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_jimeng4_tasks_status", table_name="jimeng4_tasks")
    op.drop_index("idx_jimeng4_tasks_user_created", table_name="jimeng4_tasks")
    op.drop_table("jimeng4_tasks")
    op.drop_table("jimeng4_config")
