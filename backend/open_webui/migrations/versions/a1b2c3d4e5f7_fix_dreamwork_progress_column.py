"""fix_dreamwork_progress_column

Revision ID: a1b2c3d4e5f7
Revises: f8a9b7c6d5e4
Create Date: 2025-08-18 17:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, None] = "f8a9b7c6d5e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """确保dreamwork_tasks表有progress列"""

    # 检查dreamwork_tasks表是否存在以及progress列是否存在
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "dreamwork_tasks" in inspector.get_table_names():
        existing_columns = [
            col["name"] for col in inspector.get_columns("dreamwork_tasks")
        ]

        if "progress" not in existing_columns:
            print("Adding progress column to dreamwork_tasks table...")
            with op.batch_alter_table("dreamwork_tasks", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column("progress", sa.String(20), nullable=True, default="0%")
                )

            # 为现有记录设置默认进度
            op.execute(
                "UPDATE dreamwork_tasks SET progress = '0%' WHERE progress IS NULL"
            )
            print("Progress column added successfully to dreamwork_tasks table")
        else:
            print("Progress column already exists in dreamwork_tasks table")
    else:
        print("dreamwork_tasks table does not exist, skipping progress column addition")


def downgrade() -> None:
    """移除dreamwork_tasks表的progress列"""

    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "dreamwork_tasks" in inspector.get_table_names():
        existing_columns = [
            col["name"] for col in inspector.get_columns("dreamwork_tasks")
        ]

        if "progress" in existing_columns:
            with op.batch_alter_table("dreamwork_tasks", schema=None) as batch_op:
                batch_op.drop_column("progress")
