"""add kling lip sync tables

Revision ID: e1f2g3h4i5j6
Revises: merge_heads_final
Create Date: 2025-08-25 17:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = "e1f2g3h4i5j6"
down_revision: Union[str, None] = "merge_heads_final"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建可灵对口型相关表"""

    # 创建可灵对口型配置表
    op.create_table(
        "kling_lip_sync_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "base_url",
            sa.String(length=500),
            nullable=False,
            default="https://api.kling.com",
        ),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column(
            "default_voice_id",
            sa.String(length=50),
            nullable=False,
            default="genshin_vindi2",
        ),
        sa.Column(
            "default_voice_language", sa.String(length=10), nullable=False, default="zh"
        ),
        sa.Column("default_voice_speed", sa.Float(), nullable=False, default=1.0),
        sa.Column("credits_cost", sa.Integer(), nullable=False, default=50),
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
        "INSERT INTO kling_lip_sync_config (enabled, base_url, default_voice_id, default_voice_language, default_voice_speed, credits_cost) VALUES (0, 'https://api.kling.com', 'genshin_vindi2', 'zh', 1.0, 50)"
    )

    # 创建可灵对口型任务表
    op.create_table(
        "kling_lip_sync_tasks",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, default="submitted"),
        sa.Column("task_status_msg", sa.Text(), nullable=True),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("video_input", sa.Text(), nullable=False),
        sa.Column("input_type", sa.String(length=20), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("voice_id", sa.String(length=50), nullable=True),
        sa.Column("voice_language", sa.String(length=10), nullable=True),
        sa.Column("voice_speed", sa.Float(), nullable=True),
        sa.Column("audio_file", sa.Text(), nullable=True),
        sa.Column("audio_type", sa.String(length=10), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("video_duration", sa.String(length=10), nullable=True),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("credits_cost", sa.Integer(), nullable=False, default=50),
        sa.Column(
            "submit_time",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finish_time", sa.DateTime(), nullable=True),
        sa.Column("progress", sa.String(length=10), nullable=False, default="0%"),
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
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建索引
    op.create_index("idx_kling_lip_sync_user_id", "kling_lip_sync_tasks", ["user_id"])
    op.create_index("idx_kling_lip_sync_status", "kling_lip_sync_tasks", ["status"])
    op.create_index(
        "idx_kling_lip_sync_created", "kling_lip_sync_tasks", ["created_at"]
    )

    # 创建可灵对口型积分记录表
    op.create_table(
        "kling_lip_sync_credits",
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
        "idx_kling_lip_sync_credit_user", "kling_lip_sync_credits", ["user_id"]
    )
    op.create_index(
        "idx_kling_lip_sync_credit_task", "kling_lip_sync_credits", ["task_id"]
    )


def downgrade() -> None:
    """删除可灵对口型相关表"""

    # 删除索引
    op.drop_index("idx_kling_lip_sync_credit_task", table_name="kling_lip_sync_credits")
    op.drop_index("idx_kling_lip_sync_credit_user", table_name="kling_lip_sync_credits")
    op.drop_index("idx_kling_lip_sync_created", table_name="kling_lip_sync_tasks")
    op.drop_index("idx_kling_lip_sync_status", table_name="kling_lip_sync_tasks")
    op.drop_index("idx_kling_lip_sync_user_id", table_name="kling_lip_sync_tasks")

    # 删除表
    op.drop_table("kling_lip_sync_credits")
    op.drop_table("kling_lip_sync_tasks")
    op.drop_table("kling_lip_sync_config")
