"""add banana tables

Revision ID: l1m2n3o4p5q6
Revises: k1l2m3n4o5p6_add_jimeng4_tables
Create Date: 2025-09-19 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "l1m2n3o4p5q6"
down_revision: Union[str, None] = "k1l2m3n4o5p6_add_jimeng4_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "banana_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("base_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("api_key", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "default_model",
            sa.String(length=200),
            nullable=False,
            server_default="nano-banana",
        ),
        sa.Column(
            "default_output_format",
            sa.String(length=50),
            nullable=False,
            server_default="url",
        ),
        sa.Column(
            "default_aspect_ratio",
            sa.String(length=20),
            nullable=False,
            server_default="1:1",
        ),
        sa.Column(
            "credits_per_generation", sa.Integer(), nullable=False, server_default="10"
        ),
        sa.Column(
            "credits_per_edit", sa.Integer(), nullable=False, server_default="10"
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
        "banana_tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("aspect_ratio", sa.String(length=20), nullable=True),
        sa.Column(
            "response_format",
            sa.String(length=20),
            nullable=False,
            server_default="url",
        ),
        sa.Column("request_image_urls", sa.JSON(), nullable=True),
        sa.Column("response_urls", sa.JSON(), nullable=True),
        sa.Column("cloud_image_urls", sa.JSON(), nullable=True),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("usage", sa.JSON(), nullable=True),
        sa.Column("credits_cost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="submitted"
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
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_banana_tasks_user_created", "banana_tasks", ["user_id", "created_at"]
    )
    op.create_index("ix_banana_tasks_status", "banana_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_banana_tasks_status", table_name="banana_tasks")
    op.drop_index("idx_banana_tasks_user_created", table_name="banana_tasks")
    op.drop_table("banana_tasks")
    op.drop_table("banana_config")
