"""add kling video extend support

Revision ID: m9n0p1q2r4s5
Revises: l8m9n0p1q2r3
Create Date: 2025-08-31 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "m9n0p1q2r4s5"
down_revision: Union[str, None] = "l8m9n0p1q2r3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加可灵视频延长功能支持字段 - 兼容性迁移"""

    # 检查字段是否已存在，避免重复添加
    import sqlalchemy as sa
    from alembic import context

    connection = context.get_context().bind
    inspector = sa.inspect(connection)

    # 检查 kling_config 表的 credits_per_extend 字段
    kling_config_columns = [c["name"] for c in inspector.get_columns("kling_config")]
    if "credits_per_extend" not in kling_config_columns:
        op.add_column(
            "kling_config",
            sa.Column("credits_per_extend", sa.Integer(), nullable=True, default=30),
        )

    # 检查 kling_tasks 表的延长相关字段
    kling_tasks_columns = [c["name"] for c in inspector.get_columns("kling_tasks")]

    if "parent_task_id" not in kling_tasks_columns:
        op.add_column(
            "kling_tasks",
            sa.Column("parent_task_id", sa.String(length=50), nullable=True),
        )

    if "is_extended" not in kling_tasks_columns:
        op.add_column(
            "kling_tasks",
            sa.Column("is_extended", sa.Boolean(), nullable=False, default=False),
        )

    if "original_duration" not in kling_tasks_columns:
        op.add_column(
            "kling_tasks",
            sa.Column("original_duration", sa.String(length=10), nullable=True),
        )

    if "extend_count" not in kling_tasks_columns:
        op.add_column(
            "kling_tasks",
            sa.Column("extend_count", sa.Integer(), nullable=False, default=0),
        )

    if "cloud_video_url" not in kling_tasks_columns:
        op.add_column(
            "kling_tasks", sa.Column("cloud_video_url", sa.Text(), nullable=True)
        )

    # 检查外键约束是否存在
    foreign_keys = inspector.get_foreign_keys("kling_tasks")
    fk_exists = any(
        fk["name"] == "fk_kling_tasks_parent_task_id" for fk in foreign_keys
    )

    if not fk_exists:
        try:
            op.create_foreign_key(
                "fk_kling_tasks_parent_task_id",
                "kling_tasks",
                "kling_tasks",
                ["parent_task_id"],
                ["id"],
                ondelete="SET NULL",
            )
        except Exception:
            # 如果外键创建失败，忽略（可能已存在）
            pass

    # 检查索引是否存在
    indexes = inspector.get_indexes("kling_tasks")
    index_names = [idx["name"] for idx in indexes]

    if "idx_kling_tasks_parent_task_id" not in index_names:
        try:
            op.create_index(
                "idx_kling_tasks_parent_task_id", "kling_tasks", ["parent_task_id"]
            )
        except Exception:
            pass

    if "idx_kling_tasks_is_extended" not in index_names:
        try:
            op.create_index(
                "idx_kling_tasks_is_extended", "kling_tasks", ["is_extended"]
            )
        except Exception:
            pass

    if "idx_kling_tasks_user_extended" not in index_names:
        try:
            op.create_index(
                "idx_kling_tasks_user_extended",
                "kling_tasks",
                ["user_id", "is_extended", "created_at"],
            )
        except Exception:
            pass


def downgrade() -> None:
    """回滚视频延长功能字段 - 兼容性回滚"""

    import sqlalchemy as sa
    from alembic import context

    connection = context.get_context().bind
    inspector = sa.inspect(connection)

    # 安全地删除索引
    try:
        indexes = inspector.get_indexes("kling_tasks")
        index_names = [idx["name"] for idx in indexes]

        if "idx_kling_tasks_user_extended" in index_names:
            op.drop_index("idx_kling_tasks_user_extended", table_name="kling_tasks")
        if "idx_kling_tasks_is_extended" in index_names:
            op.drop_index("idx_kling_tasks_is_extended", table_name="kling_tasks")
        if "idx_kling_tasks_parent_task_id" in index_names:
            op.drop_index("idx_kling_tasks_parent_task_id", table_name="kling_tasks")
    except Exception:
        pass

    # 安全地删除外键约束
    try:
        foreign_keys = inspector.get_foreign_keys("kling_tasks")
        fk_exists = any(
            fk["name"] == "fk_kling_tasks_parent_task_id" for fk in foreign_keys
        )
        if fk_exists:
            op.drop_constraint(
                "fk_kling_tasks_parent_task_id", "kling_tasks", type_="foreignkey"
            )
    except Exception:
        pass

    # 安全地删除字段
    try:
        kling_tasks_columns = [c["name"] for c in inspector.get_columns("kling_tasks")]

        if "cloud_video_url" in kling_tasks_columns:
            op.drop_column("kling_tasks", "cloud_video_url")
        if "extend_count" in kling_tasks_columns:
            op.drop_column("kling_tasks", "extend_count")
        if "original_duration" in kling_tasks_columns:
            op.drop_column("kling_tasks", "original_duration")
        if "is_extended" in kling_tasks_columns:
            op.drop_column("kling_tasks", "is_extended")
        if "parent_task_id" in kling_tasks_columns:
            op.drop_column("kling_tasks", "parent_task_id")
    except Exception:
        pass

    try:
        kling_config_columns = [
            c["name"] for c in inspector.get_columns("kling_config")
        ]
        if "credits_per_extend" in kling_config_columns:
            op.drop_column("kling_config", "credits_per_extend")
    except Exception:
        pass
