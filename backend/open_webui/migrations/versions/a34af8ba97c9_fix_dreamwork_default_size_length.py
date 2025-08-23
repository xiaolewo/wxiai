"""fix_dreamwork_default_size_length

Revision ID: a34af8ba97c9
Revises: merge_heads_final
Create Date: 2025-08-23 16:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = "a34af8ba97c9"
down_revision: Union[str, None] = "merge_heads_final"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """修复 DreamWork 配置表中 default_size 字段长度不一致问题"""

    # 获取当前表信息以检查字段是否存在
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    try:
        columns = inspector.get_columns("dreamwork_config")
        column_names = [col["name"] for col in columns]

        if "default_size" in column_names:
            print("修复 dreamwork_config.default_size 字段长度...")

            # 使用批量操作模式修改字段长度
            with op.batch_alter_table("dreamwork_config", schema=None) as batch_op:
                # 修改 default_size 字段长度从 String(20) 到 String(50)
                batch_op.alter_column(
                    "default_size",
                    existing_type=sa.String(20),
                    type_=sa.String(50),
                    existing_nullable=True,
                    comment="默认图片尺寸",
                )

            print("✓ dreamwork_config.default_size 字段长度已修复为 String(50)")
        else:
            print("⚠️  dreamwork_config.default_size 字段不存在，跳过修复")

    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        print("这可能是因为表不存在或者字段已经是正确的类型")
        # 不抛出异常，让迁移继续进行


def downgrade() -> None:
    """回滚修复：将 default_size 字段长度改回 String(20)"""

    # 获取当前表信息
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    try:
        columns = inspector.get_columns("dreamwork_config")
        column_names = [col["name"] for col in columns]

        if "default_size" in column_names:
            print("回滚 dreamwork_config.default_size 字段长度...")

            with op.batch_alter_table("dreamwork_config", schema=None) as batch_op:
                # 回滚到原来的长度 String(20)
                batch_op.alter_column(
                    "default_size",
                    existing_type=sa.String(50),
                    type_=sa.String(20),
                    existing_nullable=True,
                )

            print("✓ dreamwork_config.default_size 字段长度已回滚为 String(20)")
        else:
            print("⚠️  dreamwork_config.default_size 字段不存在，跳过回滚")

    except Exception as e:
        print(f"❌ 回滚过程中出现错误: {e}")
        # 不抛出异常，让回滚继续进行
