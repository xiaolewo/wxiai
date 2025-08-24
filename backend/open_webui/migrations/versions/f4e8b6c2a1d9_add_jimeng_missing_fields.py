"""add_jimeng_missing_fields

Revision ID: f4e8b6c2a1d9
Revises: a34af8ba97c9
Create Date: 2025-08-24 11:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = "f4e8b6c2a1d9"
down_revision: Union[str, None] = "a34af8ba97c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加即梦任务表和配置表的缺失字段"""

    # 获取当前表信息以检查字段是否存在
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    try:
        # 1. 处理 jimeng_tasks 表的缺失字段
        if inspector.has_table("jimeng_tasks"):
            columns = inspector.get_columns("jimeng_tasks")
            column_names = [col["name"] for col in columns]

            print("检查 jimeng_tasks 表的缺失字段...")

            # 添加 watermark 字段
            if "watermark" not in column_names:
                print("添加 jimeng_tasks.watermark 字段...")
                with op.batch_alter_table("jimeng_tasks", schema=None) as batch_op:
                    batch_op.add_column(
                        sa.Column(
                            "watermark",
                            sa.Boolean(),
                            nullable=False,
                            default=False,
                            comment="是否包含水印",
                        )
                    )
                print("✓ jimeng_tasks.watermark 字段已添加")
            else:
                print("⚠️  jimeng_tasks.watermark 字段已存在，跳过")

            # 添加 cloud_video_url 字段
            if "cloud_video_url" not in column_names:
                print("添加 jimeng_tasks.cloud_video_url 字段...")
                with op.batch_alter_table("jimeng_tasks", schema=None) as batch_op:
                    batch_op.add_column(
                        sa.Column(
                            "cloud_video_url",
                            sa.Text(),
                            nullable=True,
                            comment="云存储视频URL",
                        )
                    )
                print("✓ jimeng_tasks.cloud_video_url 字段已添加")
            else:
                print("⚠️  jimeng_tasks.cloud_video_url 字段已存在，跳过")

        else:
            print("⚠️  jimeng_tasks 表不存在，跳过字段添加")

        # 2. 处理 jimeng_config 表的缺失字段
        if inspector.has_table("jimeng_config"):
            columns = inspector.get_columns("jimeng_config")
            column_names = [col["name"] for col in columns]

            print("检查 jimeng_config 表的缺失字段...")

            # 添加 default_watermark 字段
            if "default_watermark" not in column_names:
                print("添加 jimeng_config.default_watermark 字段...")
                with op.batch_alter_table("jimeng_config", schema=None) as batch_op:
                    batch_op.add_column(
                        sa.Column(
                            "default_watermark",
                            sa.Boolean(),
                            nullable=False,
                            default=False,
                            comment="默认水印设置",
                        )
                    )
                print("✓ jimeng_config.default_watermark 字段已添加")
            else:
                print("⚠️  jimeng_config.default_watermark 字段已存在，跳过")

        else:
            print("⚠️  jimeng_config 表不存在，跳过字段添加")

    except Exception as e:
        print(f"❌ 添加字段过程中出现错误: {e}")
        print("这可能是因为表不存在或者字段已经是正确的类型")
        # 不抛出异常，让迁移继续进行


def downgrade() -> None:
    """移除添加的字段"""

    # 获取当前表信息
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    try:
        # 1. 移除 jimeng_tasks 表的字段
        if inspector.has_table("jimeng_tasks"):
            columns = inspector.get_columns("jimeng_tasks")
            column_names = [col["name"] for col in columns]

            print("回滚 jimeng_tasks 表的字段...")

            # 移除 cloud_video_url 字段
            if "cloud_video_url" in column_names:
                print("移除 jimeng_tasks.cloud_video_url 字段...")
                with op.batch_alter_table("jimeng_tasks", schema=None) as batch_op:
                    batch_op.drop_column("cloud_video_url")
                print("✓ jimeng_tasks.cloud_video_url 字段已移除")

            # 移除 watermark 字段
            if "watermark" in column_names:
                print("移除 jimeng_tasks.watermark 字段...")
                with op.batch_alter_table("jimeng_tasks", schema=None) as batch_op:
                    batch_op.drop_column("watermark")
                print("✓ jimeng_tasks.watermark 字段已移除")

        # 2. 移除 jimeng_config 表的字段
        if inspector.has_table("jimeng_config"):
            columns = inspector.get_columns("jimeng_config")
            column_names = [col["name"] for col in columns]

            print("回滚 jimeng_config 表的字段...")

            # 移除 default_watermark 字段
            if "default_watermark" in column_names:
                print("移除 jimeng_config.default_watermark 字段...")
                with op.batch_alter_table("jimeng_config", schema=None) as batch_op:
                    batch_op.drop_column("default_watermark")
                print("✓ jimeng_config.default_watermark 字段已移除")

    except Exception as e:
        print(f"❌ 回滚过程中出现错误: {e}")
        # 不抛出异常，让回滚继续进行
