"""add_missing_columns_and_service_type

Revision ID: f8a9b7c6d5e4
Revises: ef6fab585ac1
Create Date: 2025-08-18 14:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = "f8a9b7c6d5e4"
down_revision: Union[str, None] = "ef6fab585ac1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加在会话中手动修复的所有缺失列和改进"""

    # 1. 修复chat表缺失的列
    with op.batch_alter_table("chat", schema=None) as batch_op:
        # 检查列是否存在，如果不存在则添加
        connection = op.get_bind()
        inspector = sa.inspect(connection)
        existing_columns = [col["name"] for col in inspector.get_columns("chat")]

        if "pinned" not in existing_columns:
            batch_op.add_column(sa.Column("pinned", sa.Boolean(), nullable=True))
        if "meta" not in existing_columns:
            batch_op.add_column(sa.Column("meta", sa.JSON(), nullable=True))
        if "folder_id" not in existing_columns:
            batch_op.add_column(sa.Column("folder_id", sa.String(), nullable=True))

    # 2. 修复tag表缺失的列
    with op.batch_alter_table("tag", schema=None) as batch_op:
        connection = op.get_bind()
        inspector = sa.inspect(connection)
        existing_columns = [col["name"] for col in inspector.get_columns("tag")]

        if "meta" not in existing_columns:
            batch_op.add_column(sa.Column("meta", sa.JSON(), nullable=True))

    # 3. 修复model表缺失的列
    with op.batch_alter_table("model", schema=None) as batch_op:
        connection = op.get_bind()
        inspector = sa.inspect(connection)
        existing_columns = [col["name"] for col in inspector.get_columns("model")]

        if "access_control" not in existing_columns:
            batch_op.add_column(sa.Column("access_control", sa.JSON(), nullable=True))
        if "price" not in existing_columns:
            batch_op.add_column(sa.Column("price", sa.Float(), nullable=True))
        if "is_active" not in existing_columns:
            batch_op.add_column(
                sa.Column("is_active", sa.Boolean(), nullable=True, default=True)
            )

    # 4. 修复prompt表缺失的列
    with op.batch_alter_table("prompt", schema=None) as batch_op:
        connection = op.get_bind()
        inspector = sa.inspect(connection)
        existing_columns = [col["name"] for col in inspector.get_columns("prompt")]

        if "access_control" not in existing_columns:
            batch_op.add_column(sa.Column("access_control", sa.JSON(), nullable=True))

    # 5. 为视频生成服务表添加serviceType列
    video_tables = ["jimeng_tasks", "kling_tasks", "dreamwork_tasks"]

    for table_name in video_tables:
        # 检查表是否存在
        try:
            connection = op.get_bind()
            inspector = sa.inspect(connection)
            if table_name in inspector.get_table_names():
                existing_columns = [
                    col["name"] for col in inspector.get_columns(table_name)
                ]

                if "serviceType" not in existing_columns:
                    with op.batch_alter_table(table_name, schema=None) as batch_op:
                        batch_op.add_column(
                            sa.Column("serviceType", sa.String(50), nullable=True)
                        )

                    # 设置默认的serviceType值
                    service_type_map = {
                        "jimeng_tasks": "jimeng",
                        "kling_tasks": "kling",
                        "dreamwork_tasks": "dreamwork",
                    }
                    default_service = service_type_map.get(table_name, "unknown")

                    # 更新现有记录
                    op.execute(
                        f"UPDATE {table_name} SET serviceType = '{default_service}' WHERE serviceType IS NULL"
                    )
        except Exception as e:
            print(f"Warning: Could not update table {table_name}: {e}")
            continue


def downgrade() -> None:
    """回滚在会话中手动修复的所有修改"""

    # 1. 回滚chat表的修改
    with op.batch_alter_table("chat", schema=None) as batch_op:
        batch_op.drop_column("folder_id")
        batch_op.drop_column("meta")
        batch_op.drop_column("pinned")

    # 2. 回滚tag表的修改
    with op.batch_alter_table("tag", schema=None) as batch_op:
        batch_op.drop_column("meta")

    # 3. 回滚model表的修改
    with op.batch_alter_table("model", schema=None) as batch_op:
        batch_op.drop_column("is_active")
        batch_op.drop_column("price")
        batch_op.drop_column("access_control")

    # 4. 回滚prompt表的修改
    with op.batch_alter_table("prompt", schema=None) as batch_op:
        batch_op.drop_column("access_control")

    # 5. 回滚视频生成服务表的修改
    video_tables = ["jimeng_tasks", "kling_tasks", "dreamwork_tasks"]

    for table_name in video_tables:
        try:
            connection = op.get_bind()
            inspector = sa.inspect(connection)
            if table_name in inspector.get_table_names():
                with op.batch_alter_table(table_name, schema=None) as batch_op:
                    batch_op.drop_column("serviceType")
        except Exception as e:
            print(f"Warning: Could not revert table {table_name}: {e}")
            continue
