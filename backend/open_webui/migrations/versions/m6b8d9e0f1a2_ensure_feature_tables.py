"""Ensure key feature tables and columns exist

Revision ID: m6b8d9e0f1a2
Revises: ('7e5b5dc7342b', '97c08d196e3d', 'a0e430ed5341', 'a1b2c3d4e5f6', 'a1b2c3d4e5f7', 'a1b2c3d4e5f8', 'a34af8ba97c9', 'a7dd10d9b220', 'a959f8a63245', 'abc123def456', 'b8f3a2c9d1e0', 'c0fbf31ca0db', 'ca81bd47c050', 'd31026856c01', 'd7462fa176a0', 'e1f2g3h4i5j6', 'ef6fab585ac1', 'f1e2d3c4b5a6', 'f2g3h4i5j6k7', 'f4e8b6c2a1d9', 'f8a9b7c6d5e4', 'g3h4i5j6k7l8', 'h4i5j6k7l8m9', 'i5j6k7l8m9n0', 'j1k2l3m4n5o6', 'k1l2m3n4o5p6', 'l1m2n3o4p5q6', 'merge_heads_final', 'merge_heads_kling_lip_sync', '1f045f7aebc5', '22c97ff924a3', '24e8f9a7b1c2', '33de2e0ea2f5', '3781e22d8b01', '6fc1adfb106d', '70c7b727736e', '1403e6d80d1d')
Create Date: 2025-02-28 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

from open_webui.migrations.util import get_existing_tables

# revision identifiers, used by Alembic.
revision: str = "m6b8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = (
    "7e5b5dc7342b",
    "97c08d196e3d",
    "a0e430ed5341",
    "a1b2c3d4e5f6",
    "a1b2c3d4e5f7",
    "a1b2c3d4e5f8",
    "a34af8ba97c9",
    "a7dd10d9b220",
    "a959f8a63245",
    "abc123def456",
    "b8f3a2c9d1e0",
    "c0fbf31ca0db",
    "ca81bd47c050",
    "d31026856c01",
    "d7462fa176a0",
    "e1f2g3h4i5j6",
    "ef6fab585ac1",
    "f1e2d3c4b5a6",
    "f2g3h4i5j6k7",
    "f4e8b6c2a1d9",
    "f8a9b7c6d5e4",
    "g3h4i5j6k7l8",
    "h4i5j6k7l8m9",
    "i5j6k7l8m9n0",
    "j1k2l3m4n5o6",
    "k1l2m3n4o5p6",
    "l1m2n3o4p5q6",
    "merge_heads_final",
    "merge_heads_kling_lip_sync",
    "1f045f7aebc5",
    "22c97ff924a3",
    "24e8f9a7b1c2",
    "33de2e0ea2f5",
    "3781e22d8b01",
    "6fc1adfb106d",
    "70c7b727736e",
    "1403e6d80d1d",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = get_existing_tables()

    def refresh_inspector():
        nonlocal inspector
        inspector = inspect(bind)

    # Helper utilities
    def has_column(table: str, column: str) -> bool:
        return any(col["name"] == column for col in inspector.get_columns(table))

    def ensure_index(table: str, name: str, columns: list[str]):
        indexes = inspector.get_indexes(table)
        if not any(idx.get("name") == name for idx in indexes):
            op.create_index(name, table, columns)

    # -------------------------
    # config table
    # -------------------------
    if "config" not in existing_tables:
        op.create_table(
            "config",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("data", sa.JSON(), nullable=False),
            sa.Column(
                "version", sa.Integer, nullable=False, server_default=sa.text("0")
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=True,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        refresh_inspector()
        existing_tables.add("config")

    # -------------------------
    # Midjourney tables
    # -------------------------
    if "mj_config" not in existing_tables:
        op.create_table(
            "mj_config",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column("base_url", sa.Text()),
            sa.Column("api_key", sa.Text()),
            sa.Column("modes", sa.JSON()),
            sa.Column("default_mode", sa.String(50), server_default="fast"),
            sa.Column(
                "max_concurrent_tasks", sa.Integer(), server_default=sa.text("5")
            ),
            sa.Column("task_timeout", sa.Integer(), server_default=sa.text("300000")),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=True,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        refresh_inspector()
        existing_tables.add("mj_config")

    if "mj_tasks" not in existing_tables:
        op.create_table(
            "mj_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("action", sa.String(50)),
            sa.Column("status", sa.String(50), server_default="SUBMITTED"),
            sa.Column("prompt", sa.Text()),
            sa.Column("prompt_en", sa.Text()),
            sa.Column("description", sa.Text()),
            sa.Column("mode", sa.String(50), server_default="fast"),
            sa.Column("credits_cost", sa.Integer(), server_default=sa.text("0")),
            sa.Column("submit_time", sa.DateTime()),
            sa.Column("start_time", sa.DateTime()),
            sa.Column("finish_time", sa.DateTime()),
            sa.Column("progress", sa.String(20), server_default="0%"),
            sa.Column("image_url", sa.Text()),
            sa.Column("cloud_image_url", sa.Text()),
            sa.Column("fail_reason", sa.Text()),
            sa.Column("properties", sa.JSON()),
            sa.Column("buttons", sa.JSON()),
            sa.Column("parent_task_id", sa.String(50)),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        refresh_inspector()
        existing_tables.add("mj_tasks")
    else:
        # ensure supplemental columns exist
        for column, column_type in [
            ("cloud_image_url", sa.Text()),
            ("progress", sa.String(20)),
            ("buttons", sa.JSON()),
            ("properties", sa.JSON()),
        ]:
            if not has_column("mj_tasks", column):
                op.add_column("mj_tasks", sa.Column(column, column_type))
                refresh_inspector()

    ensure_index("mj_tasks", "idx_mj_tasks_user_created", ["user_id", "created_at"])
    ensure_index("mj_tasks", "idx_mj_tasks_status_updated", ["status", "updated_at"])
    ensure_index("mj_tasks", "ix_mj_tasks_user_id", ["user_id"])

    if "mj_credits" not in existing_tables:
        op.create_table(
            "mj_credits",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("amount", sa.Integer()),
            sa.Column("balance", sa.Integer()),
            sa.Column("reason", sa.String(200)),
            sa.Column("task_id", sa.String(50)),
            sa.Column("created_at", sa.DateTime()),
        )
        refresh_inspector()
        existing_tables.add("mj_credits")
    else:
        if not has_column("mj_credits", "created_at"):
            op.add_column("mj_credits", sa.Column("created_at", sa.DateTime()))
            refresh_inspector()
    ensure_index("mj_credits", "idx_mj_credits_user_created", ["user_id", "created_at"])
    ensure_index("mj_credits", "ix_mj_credits_user_id", ["user_id"])

    # -------------------------
    # DreamWork tables
    # -------------------------
    if "dreamwork_config" not in existing_tables:
        op.create_table(
            "dreamwork_config",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column("base_url", sa.String(500)),
            sa.Column("api_key", sa.Text()),
            sa.Column(
                "text_to_image_model",
                sa.String(100),
                server_default="doubao-seedream-3-0-t2i-250415",
            ),
            sa.Column(
                "image_to_image_model",
                sa.String(100),
                server_default="doubao-seededit-3-0-i2i-250628",
            ),
            sa.Column("default_size", sa.String(20), server_default="1024x1024"),
            sa.Column(
                "default_guidance_scale", sa.Float(), server_default=sa.text("2.5")
            ),
            sa.Column("watermark_enabled", sa.Boolean(), server_default=sa.text("1")),
            sa.Column(
                "credits_per_generation", sa.Integer(), server_default=sa.text("10")
            ),
            sa.Column(
                "max_concurrent_tasks", sa.Integer(), server_default=sa.text("5")
            ),
            sa.Column("task_timeout", sa.Integer(), server_default=sa.text("300000")),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=True,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        refresh_inspector()
        existing_tables.add("dreamwork_config")

    if "dreamwork_tasks" not in existing_tables:
        op.create_table(
            "dreamwork_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("action", sa.String(50)),
            sa.Column("status", sa.String(50), server_default="SUBMITTED"),
            sa.Column("prompt", sa.Text()),
            sa.Column("model", sa.String(100)),
            sa.Column("size", sa.String(50), server_default="1024x1024"),
            sa.Column("guidance_scale", sa.Float()),
            sa.Column("seed", sa.Integer()),
            sa.Column("watermark", sa.Boolean(), server_default=sa.text("1")),
            sa.Column("credits_cost", sa.Integer(), server_default=sa.text("0")),
            sa.Column("submit_time", sa.DateTime()),
            sa.Column("start_time", sa.DateTime()),
            sa.Column("finish_time", sa.DateTime()),
            sa.Column("progress", sa.String(20), server_default="0%"),
            sa.Column("image_url", sa.Text()),
            sa.Column("cloud_image_url", sa.Text()),
            sa.Column("fail_reason", sa.Text()),
            sa.Column("input_image", sa.Text()),
            sa.Column("properties", sa.JSON()),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        refresh_inspector()
        existing_tables.add("dreamwork_tasks")
    else:
        if not has_column("dreamwork_tasks", "cloud_image_url"):
            op.add_column("dreamwork_tasks", sa.Column("cloud_image_url", sa.Text()))
            refresh_inspector()
        if not has_column("dreamwork_tasks", "progress"):
            op.add_column("dreamwork_tasks", sa.Column("progress", sa.String(20)))
            refresh_inspector()

    ensure_index(
        "dreamwork_tasks", "idx_dreamwork_user_created", ["user_id", "created_at"]
    )
    ensure_index(
        "dreamwork_tasks", "idx_dreamwork_status_updated", ["status", "updated_at"]
    )

    if "dreamwork_credits" not in existing_tables:
        op.create_table(
            "dreamwork_credits",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("amount", sa.Integer()),
            sa.Column("balance", sa.Integer()),
            sa.Column("reason", sa.String(200)),
            sa.Column("task_id", sa.String(50)),
            sa.Column("created_at", sa.DateTime()),
        )
        refresh_inspector()
        existing_tables.add("dreamwork_credits")
    else:
        if not has_column("dreamwork_credits", "created_at"):
            op.add_column("dreamwork_credits", sa.Column("created_at", sa.DateTime()))
            refresh_inspector()
    ensure_index("dreamwork_credits", "idx_dreamwork_credits_user_id", ["user_id"])

    # -------------------------
    # Flux tables
    # -------------------------
    if "flux_config" not in existing_tables:
        op.create_table(
            "flux_config",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("api_key", sa.Text(), nullable=False),
            sa.Column(
                "base_url",
                sa.String(500),
                nullable=False,
                server_default="https://queue.fal.run",
            ),
            sa.Column(
                "enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")
            ),
            sa.Column(
                "timeout", sa.Integer(), nullable=False, server_default=sa.text("300")
            ),
            sa.Column(
                "max_concurrent_tasks",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("5"),
            ),
            sa.Column(
                "default_model",
                sa.String(100),
                nullable=False,
                server_default="fal-ai/flux-1/dev",
            ),
            sa.Column("model_credits", sa.JSON()),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        refresh_inspector()
        existing_tables.add("flux_config")
    else:
        if not has_column("flux_config", "model_credits"):
            op.add_column("flux_config", sa.Column("model_credits", sa.JSON()))
            refresh_inspector()

    if "flux_tasks" not in existing_tables:
        op.create_table(
            "flux_tasks",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("user_id", sa.String(255), nullable=False),
            sa.Column("request_id", sa.String(255), nullable=False),
            sa.Column("model", sa.String(100), nullable=False),
            sa.Column("task_type", sa.String(20), nullable=False),
            sa.Column(
                "status", sa.String(20), nullable=False, server_default="PENDING"
            ),
            sa.Column("prompt", sa.Text()),
            sa.Column("input_image_url", sa.Text()),
            sa.Column("input_image_urls", sa.JSON()),
            sa.Column("uploaded_image_url", sa.Text()),
            sa.Column("num_images", sa.Integer(), server_default=sa.text("1")),
            sa.Column("aspect_ratio", sa.String(20), server_default="1:1"),
            sa.Column("image_size", sa.JSON()),
            sa.Column("guidance_scale", sa.Float(), server_default=sa.text("3.5")),
            sa.Column(
                "num_inference_steps", sa.Integer(), server_default=sa.text("28")
            ),
            sa.Column("seed", sa.Integer()),
            sa.Column("safety_tolerance", sa.Integer(), server_default=sa.text("2")),
            sa.Column("strength", sa.Float(), server_default=sa.text("0.95")),
            sa.Column("sync_mode", sa.Boolean(), server_default=sa.text("0")),
            sa.Column("output_format", sa.String(10), server_default="jpeg"),
            sa.Column(
                "enable_safety_checker", sa.Boolean(), server_default=sa.text("1")
            ),
            sa.Column("image_url", sa.Text()),
            sa.Column("cloud_image_url", sa.Text()),
            sa.Column("generation_time", sa.Float()),
            sa.Column("queue_position", sa.Integer()),
            sa.Column("error_message", sa.Text()),
            sa.Column("retry_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("flux_response", sa.JSON()),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
            sa.Column("completed_at", sa.DateTime()),
        )
        refresh_inspector()
        existing_tables.add("flux_tasks")
    else:
        for column, column_type in [
            ("input_image_urls", sa.JSON()),
            ("image_size", sa.JSON()),
            ("cloud_image_url", sa.Text()),
        ]:
            if not has_column("flux_tasks", column):
                op.add_column("flux_tasks", sa.Column(column, column_type))
                refresh_inspector()

    ensure_index("flux_tasks", "idx_flux_tasks_user_status", ["user_id", "status"])
    ensure_index("flux_tasks", "idx_flux_tasks_model_status", ["model", "status"])
    ensure_index("flux_tasks", "idx_flux_tasks_user_id", ["user_id"])
    ensure_index("flux_tasks", "idx_flux_tasks_status", ["status"])
    ensure_index("flux_tasks", "idx_flux_tasks_request_id", ["request_id"])
    ensure_index("flux_tasks", "idx_flux_tasks_created_at", ["created_at"])

    if "flux_credits" not in existing_tables:
        op.create_table(
            "flux_credits",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("user_id", sa.String(255), nullable=False),
            sa.Column(
                "credits_balance",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "total_used", sa.Integer(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        refresh_inspector()
        existing_tables.add("flux_credits")
    ensure_index("flux_credits", "idx_flux_credits_user_id", ["user_id"])


def downgrade() -> None:
    # The downgrade removes structures created by this migration only if
    # they were introduced here. Columns and tables that may pre-exist in
    # earlier revisions are left untouched to avoid data loss.

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    def safe_drop_index(table: str, name: str):
        indexes = inspector.get_indexes(table)
        if any(idx.get("name") == name for idx in indexes):
            op.drop_index(name, table_name=table)

    # Flux credits
    if "flux_credits" in existing_tables:
        safe_drop_index("flux_credits", "idx_flux_credits_user_id")
        op.drop_table("flux_credits")
        existing_tables.remove("flux_credits")

    # Flux tasks additions
    if "flux_tasks" in existing_tables:
        safe_drop_index("flux_tasks", "idx_flux_tasks_created_at")
        safe_drop_index("flux_tasks", "idx_flux_tasks_request_id")
        safe_drop_index("flux_tasks", "idx_flux_tasks_status")
        safe_drop_index("flux_tasks", "idx_flux_tasks_user_id")
        safe_drop_index("flux_tasks", "idx_flux_tasks_model_status")
        safe_drop_index("flux_tasks", "idx_flux_tasks_user_status")
        # We cannot safely drop columns without data loss; keep them in place.

    if "flux_config" in existing_tables:
        columns = {col["name"] for col in inspector.get_columns("flux_config")}
        if "model_credits" in columns:
            op.drop_column("flux_config", "model_credits")

    # Dreamwork credits
    if "dreamwork_credits" in existing_tables:
        safe_drop_index("dreamwork_credits", "idx_dreamwork_credits_user_id")
        op.drop_table("dreamwork_credits")
        existing_tables.remove("dreamwork_credits")

    if "dreamwork_tasks" in existing_tables:
        safe_drop_index("dreamwork_tasks", "idx_dreamwork_status_updated")
        safe_drop_index("dreamwork_tasks", "idx_dreamwork_user_created")
        # Columns retained to avoid data loss

    if "dreamwork_config" in existing_tables:
        op.drop_table("dreamwork_config")
        existing_tables.remove("dreamwork_config")

    # Midjourney credits
    if "mj_credits" in existing_tables:
        safe_drop_index("mj_credits", "ix_mj_credits_user_id")
        safe_drop_index("mj_credits", "idx_mj_credits_user_created")
        op.drop_table("mj_credits")
        existing_tables.remove("mj_credits")

    if "mj_tasks" in existing_tables:
        safe_drop_index("mj_tasks", "ix_mj_tasks_user_id")
        safe_drop_index("mj_tasks", "idx_mj_tasks_status_updated")
        safe_drop_index("mj_tasks", "idx_mj_tasks_user_created")
        # Columns retained to avoid data loss

    if "mj_config" in existing_tables:
        op.drop_table("mj_config")
        existing_tables.remove("mj_config")

    if "config" in existing_tables:
        op.drop_table("config")
        existing_tables.remove("config")
