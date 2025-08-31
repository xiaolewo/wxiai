"""remove google images response format

Revision ID: k7l8m9n0p1q2
Revises: j6k7l8m9n0p1
Create Date: 2025-08-30 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "k7l8m9n0p1q2"
down_revision: Union[str, None] = "j6k7l8m9n0p1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """删除谷歌生图表中的响应格式字段"""

    # 检查并删除配置表中的 default_response_format 字段（如果存在）
    try:
        op.drop_column("google_images_config", "default_response_format")
    except Exception:
        # 如果字段不存在，忽略错误
        pass

    # 检查并删除任务表中的 response_format 字段（如果存在）
    try:
        op.drop_column("google_images_tasks", "response_format")
    except Exception:
        # 如果字段不存在，忽略错误
        pass


def downgrade() -> None:
    """恢复响应格式字段"""

    # 恢复配置表中的 default_response_format 字段
    op.add_column(
        "google_images_config",
        sa.Column(
            "default_response_format",
            sa.String(length=20),
            nullable=False,
            default="url",
        ),
    )

    # 恢复任务表中的 response_format 字段
    op.add_column(
        "google_images_tasks",
        sa.Column(
            "response_format", sa.String(length=20), nullable=False, default="url"
        ),
    )
