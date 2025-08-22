"""add_google_video_tables

Revision ID: google_video_001
Revises: merge_heads_final
Create Date: 2025-08-20 20:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = "google_video_001"
down_revision: Union[str, None] = "merge_heads_final"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级：创建谷歌视频相关表"""

    # 1. 创建 google_video_config 表
    op.create_table(
        "google_video_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=True, default=False),
        sa.Column("base_url", sa.String(500), nullable=True, default=""),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("default_text_model", sa.String(100), nullable=True, default="veo3"),
        sa.Column(
            "default_image_model",
            sa.String(100),
            nullable=True,
            default="veo3-pro-frames",
        ),
        sa.Column("default_enhance_prompt", sa.Boolean(), nullable=True, default=False),
        sa.Column("model_credits_config", sa.JSON(), nullable=True),
        sa.Column("max_concurrent_tasks", sa.Integer(), nullable=True, default=3),
        sa.Column("task_timeout", sa.Integer(), nullable=True, default=600000),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. 创建 google_video_tasks 表
    op.create_table(
        "google_video_tasks",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=False),
        sa.Column("external_task_id", sa.String(100), nullable=True),
        sa.Column("task_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(50), nullable=True, default="SUBMITTED"),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("enhance_prompt", sa.Boolean(), nullable=True, default=False),
        sa.Column("input_images", sa.JSON(), nullable=True),
        sa.Column("uploaded_images", sa.JSON(), nullable=True),
        sa.Column("submit_time", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.Integer(), nullable=True),
        sa.Column("finish_time", sa.Integer(), nullable=True),
        sa.Column("progress", sa.String(20), nullable=True, default="0%"),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("cloud_video_url", sa.Text(), nullable=True),
        sa.Column("video_duration", sa.Float(), nullable=True),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("credits_cost", sa.Integer(), nullable=True, default=0),
        sa.Column("request_data", sa.Text(), nullable=True),
        sa.Column("response_data", sa.Text(), nullable=True),
        sa.Column(
            "cloud_upload_status", sa.String(20), nullable=True, default="pending"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. 创建 google_video_credits 表
    op.create_table(
        "google_video_credits",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("task_id", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. 创建索引优化查询性能
    op.create_index("idx_google_video_tasks_user_id", "google_video_tasks", ["user_id"])
    op.create_index("idx_google_video_tasks_status", "google_video_tasks", ["status"])
    op.create_index(
        "idx_google_video_tasks_external_id", "google_video_tasks", ["external_task_id"]
    )
    op.create_index(
        "idx_google_video_credits_user_id", "google_video_credits", ["user_id"]
    )

    print("✅ 谷歌视频数据表创建成功！")


def downgrade() -> None:
    """降级：删除谷歌视频相关表（生产环境不建议执行）"""

    # 删除索引
    op.drop_index("idx_google_video_credits_user_id", "google_video_credits")
    op.drop_index("idx_google_video_tasks_external_id", "google_video_tasks")
    op.drop_index("idx_google_video_tasks_status", "google_video_tasks")
    op.drop_index("idx_google_video_tasks_user_id", "google_video_tasks")

    # 删除表
    op.drop_table("google_video_credits")
    op.drop_table("google_video_tasks")
    op.drop_table("google_video_config")

    print("⚠️ 谷歌视频数据表已删除")
