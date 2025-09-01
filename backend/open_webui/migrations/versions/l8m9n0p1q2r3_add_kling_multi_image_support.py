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
down_revision: Union[str, None] = "6fc1adfb106d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加可灵多图参考支持字段 - 兼容性迁移"""

    # 检查字段是否已存在，避免重复添加
    import sqlalchemy as sa
    from alembic import context

    connection = context.get_context().bind
    inspector = sa.inspect(connection)

    # 检查 kling_tasks 表的字段
    kling_tasks_columns = [c["name"] for c in inspector.get_columns("kling_tasks")]

    if "generation_mode" not in kling_tasks_columns:
        op.add_column(
            "kling_tasks",
            sa.Column(
                "generation_mode",
                sa.String(length=20),
                nullable=False,
                default="single_image",
            ),
        )

    if "input_images" not in kling_tasks_columns:
        op.add_column(
            "kling_tasks", sa.Column("input_images", sa.JSON(), nullable=True)
        )

    if "image_count" not in kling_tasks_columns:
        op.add_column(
            "kling_tasks",
            sa.Column("image_count", sa.Integer(), nullable=False, default=0),
        )

    # 检查索引是否存在
    indexes = inspector.get_indexes("kling_tasks")
    index_names = [idx["name"] for idx in indexes]

    if (
        "ix_kling_tasks_generation_mode" not in index_names
        and "idx_kling_tasks_generation_mode" not in index_names
    ):
        try:
            op.create_index(
                "idx_kling_tasks_generation_mode",
                "kling_tasks",
                ["generation_mode"],
                unique=False,
            )
        except Exception:
            pass


def downgrade() -> None:
    """删除可灵多图参考支持字段 - 兼容性回滚"""

    import sqlalchemy as sa
    from alembic import context

    connection = context.get_context().bind
    inspector = sa.inspect(connection)

    # 安全地删除索引
    try:
        indexes = inspector.get_indexes("kling_tasks")
        index_names = [idx["name"] for idx in indexes]

        if "ix_kling_tasks_generation_mode" in index_names:
            op.drop_index("ix_kling_tasks_generation_mode", table_name="kling_tasks")
        if "idx_kling_tasks_generation_mode" in index_names:
            op.drop_index("idx_kling_tasks_generation_mode", table_name="kling_tasks")
    except Exception:
        pass

    # 安全地删除字段
    try:
        kling_tasks_columns = [c["name"] for c in inspector.get_columns("kling_tasks")]

        if "image_count" in kling_tasks_columns:
            op.drop_column("kling_tasks", "image_count")
        if "input_images" in kling_tasks_columns:
            op.drop_column("kling_tasks", "input_images")
        if "generation_mode" in kling_tasks_columns:
            op.drop_column("kling_tasks", "generation_mode")
    except Exception:
        pass
