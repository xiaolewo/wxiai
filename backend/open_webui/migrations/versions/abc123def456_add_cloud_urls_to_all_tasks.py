"""add cloud storage urls to all task tables

Revision ID: abc123def456
Revises: f1e2d3c4b5a6
Create Date: 2025-08-19 19:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "abc123def456"
down_revision: Union[str, None] = "f1e2d3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cloud storage URL columns to task tables"""

    # 添加Midjourney任务表的云存储字段
    try:
        op.add_column(
            "mj_tasks", sa.Column("cloud_image_url", sa.Text(), nullable=True)
        )
    except Exception:
        pass  # 字段可能已存在

    # 添加DreamWork任务表的云存储字段
    try:
        op.add_column(
            "dreamwork_tasks", sa.Column("cloud_image_url", sa.Text(), nullable=True)
        )
    except Exception:
        pass  # 字段可能已存在

    # 添加Kling任务表的云存储字段
    try:
        op.add_column(
            "kling_tasks", sa.Column("cloud_video_url", sa.Text(), nullable=True)
        )
    except Exception:
        pass  # 字段可能已存在

    # 添加Jimeng任务表的云存储字段
    try:
        op.add_column(
            "jimeng_tasks", sa.Column("cloud_video_url", sa.Text(), nullable=True)
        )
    except Exception:
        pass  # 字段可能已存在


def downgrade() -> None:
    """Remove cloud storage URL columns from task tables"""

    # 删除添加的云存储字段
    try:
        op.drop_column("mj_tasks", "cloud_image_url")
    except Exception:
        pass

    try:
        op.drop_column("dreamwork_tasks", "cloud_image_url")
    except Exception:
        pass

    try:
        op.drop_column("kling_tasks", "cloud_video_url")
    except Exception:
        pass

    try:
        op.drop_column("jimeng_tasks", "cloud_video_url")
    except Exception:
        pass
