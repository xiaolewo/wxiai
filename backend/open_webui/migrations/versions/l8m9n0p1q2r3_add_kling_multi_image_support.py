"""add kling multi image support

Revision ID: l8m9n0p1q2r3
Revises: k7l8m9n0p1q2
Create Date: 2025-08-31 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "l8m9n0p1q2r3"
down_revision: Union[str, None] = "k7l8m9n0p1q2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加可灵多图参考支持字段"""

    # 添加生成模式字段
    op.add_column(
        "kling_tasks",
        sa.Column(
            "generation_mode",
            sa.String(length=20),
            nullable=False,
            default="single_image",
        ),
    )

    # 添加多图输入数据字段
    op.add_column("kling_tasks", sa.Column("input_images", sa.JSON(), nullable=True))

    # 添加图片数量字段
    op.add_column(
        "kling_tasks", sa.Column("image_count", sa.Integer(), nullable=False, default=0)
    )

    # 创建生成模式索引
    op.create_index(
        op.f("ix_kling_tasks_generation_mode"),
        "kling_tasks",
        ["generation_mode"],
        unique=False,
    )


def downgrade() -> None:
    """删除可灵多图参考支持字段"""

    # 删除生成模式索引
    op.drop_index(op.f("ix_kling_tasks_generation_mode"), table_name="kling_tasks")

    # 删除添加的字段
    op.drop_column("kling_tasks", "image_count")
    op.drop_column("kling_tasks", "input_images")
    op.drop_column("kling_tasks", "generation_mode")
