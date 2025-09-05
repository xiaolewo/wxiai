"""final merge all branches - cloud storage fix

Revision ID: z9x8c7v6b5n4
Revises: 33de2e0ea2f5, abc123def456, m9n0p1q2r4s5, k7l8m9n0p1q2, e5f6g7h8i9j0
Create Date: 2025-09-02 18:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "z9x8c7v6b5n4"
down_revision: Union[str, None] = (
    "33de2e0ea2f5",  # 当前数据库版本 (add_midjourney_tables)
    "abc123def456",  # 云存储字段迁移
    "m9n0p1q2r4s5",  # kling video extend support
    "k7l8m9n0p1q2",  # remove google images response format
    "e5f6g7h8i9j0",  # enable comfyui by default
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Final merge - ensure all cloud storage fields exist"""

    # 使用动态检查方式，确保所有字段都存在
    import sqlalchemy as sa
    from alembic import context

    connection = context.get_context().bind
    inspector = sa.inspect(connection)

    # 确保所有任务表都有云存储字段
    cloud_storage_fields = [
        ("mj_tasks", "cloud_image_url", sa.Text()),
        ("dreamwork_tasks", "cloud_image_url", sa.Text()),
        ("kling_tasks", "cloud_video_url", sa.Text()),
        ("jimeng_tasks", "cloud_video_url", sa.Text()),
        ("flux_tasks", "input_image_urls", sa.JSON()),
        ("flux_tasks", "image_size", sa.JSON()),
    ]

    for table_name, field_name, field_type in cloud_storage_fields:
        try:
            if inspector.has_table(table_name):
                columns = [c["name"] for c in inspector.get_columns(table_name)]
                if field_name not in columns:
                    op.add_column(
                        table_name, sa.Column(field_name, field_type, nullable=True)
                    )
                    print(f"Added {table_name}.{field_name}")
        except Exception as e:
            print(f"Field {table_name}.{field_name} might already exist: {e}")

    # 确保云存储配置表存在
    if not inspector.has_table("cloud_storage_config"):
        op.create_table(
            "cloud_storage_config",
            sa.Column("id", sa.String(255), nullable=False),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
            sa.Column("secret_id", sa.Text(), nullable=True),
            sa.Column("secret_key", sa.Text(), nullable=True),
            sa.Column("region", sa.String(50), nullable=True),
            sa.Column("bucket", sa.String(255), nullable=True),
            sa.Column("domain", sa.Text(), nullable=True),
            sa.Column("auto_upload", sa.Boolean(), nullable=False, default=True),
            sa.Column("allowed_types", sa.JSON(), nullable=True),
            sa.Column(
                "max_file_size", sa.BigInteger(), nullable=False, default=104857600
            ),
            sa.Column(
                "base_path", sa.String(255), nullable=False, default="generated/"
            ),
            sa.Column("image_path", sa.String(255), nullable=False, default="images/"),
            sa.Column("video_path", sa.String(255), nullable=False, default="videos/"),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
        )

        # 插入默认配置
        op.execute(
            """
            INSERT INTO cloud_storage_config 
            (id, provider, enabled, secret_id, secret_key, region, bucket, domain, 
             auto_upload, allowed_types, max_file_size, base_path, image_path, video_path) 
            VALUES 
            ('default', 'tencent-cos', 0, '', '', 'ap-beijing', '', '', 
             1, '["image/*", "video/*"]', 104857600, 'generated/', 'images/', 'videos/')
        """
        )

    # 确保生成文件记录表存在
    if not inspector.has_table("generated_files"):
        op.create_table(
            "generated_files",
            sa.Column("id", sa.String(255), nullable=False),
            sa.Column("user_id", sa.String(255), nullable=False),
            sa.Column("filename", sa.String(255), nullable=False),
            sa.Column("original_filename", sa.String(255), nullable=True),
            sa.Column("file_type", sa.String(20), nullable=False),
            sa.Column("mime_type", sa.String(100), nullable=True),
            sa.Column("file_size", sa.BigInteger(), nullable=True),
            sa.Column(
                "storage_provider", sa.String(50), nullable=False, default="local"
            ),
            sa.Column("local_path", sa.Text(), nullable=True),
            sa.Column("cloud_url", sa.Text(), nullable=True),
            sa.Column("cloud_path", sa.Text(), nullable=True),
            sa.Column("source_type", sa.String(50), nullable=False),
            sa.Column("source_task_id", sa.String(255), nullable=True),
            sa.Column("file_metadata", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, default="pending"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
        )

        # 创建索引
        op.create_index("idx_generated_files_user_id", "generated_files", ["user_id"])
        op.create_index(
            "idx_generated_files_source",
            "generated_files",
            ["source_type", "source_task_id"],
        )
        op.create_index(
            "idx_generated_files_created", "generated_files", ["created_at"]
        )


def downgrade() -> None:
    """Downgrade - remove cloud storage features"""

    # 删除云存储字段
    cloud_storage_fields = [
        ("mj_tasks", "cloud_image_url"),
        ("dreamwork_tasks", "cloud_image_url"),
        ("kling_tasks", "cloud_video_url"),
        ("jimeng_tasks", "cloud_video_url"),
        ("flux_tasks", "input_image_urls"),
        ("flux_tasks", "image_size"),
    ]

    for table_name, field_name in cloud_storage_fields:
        try:
            op.drop_column(table_name, field_name)
        except Exception:
            pass

    # 删除云存储相关表
    try:
        op.drop_table("generated_files")
    except Exception:
        pass

    try:
        op.drop_table("cloud_storage_config")
    except Exception:
        pass
