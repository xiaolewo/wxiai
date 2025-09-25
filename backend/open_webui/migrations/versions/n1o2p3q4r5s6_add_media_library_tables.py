"""Add media library tables

Revision ID: n1o2p3q4r5s6
Revises: m6b8d9e0f1a2
Create Date: 2025-03-01 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "n1o2p3q4r5s6"
down_revision: Union[str, Sequence[str], None] = "m6b8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


VISIBILITY_USER = "user"


def upgrade() -> None:
    media_folder = op.create_table(
        "media_folder",
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column(
            "parent_id",
            sa.String(length=255),
            sa.ForeignKey("media_folder.id"),
            nullable=True,
        ),
        sa.Column(
            "visibility_scope",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text(f"'{VISIBILITY_USER}'"),
        ),
        sa.Column("owner_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=True),
        sa.Column("preset_key", sa.String(length=100), nullable=True),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_media_folder_owner_scope",
        "media_folder",
        ["owner_id", "visibility_scope"],
        unique=False,
    )

    op.create_table(
        "media_asset",
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column(
            "file_id",
            sa.String(length=255),
            sa.ForeignKey("generated_files.id"),
            nullable=False,
        ),
        sa.Column(
            "visibility_scope",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text(f"'{VISIBILITY_USER}'"),
        ),
        sa.Column("owner_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=20), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column(
            "folder_id",
            sa.String(length=255),
            sa.ForeignKey("media_folder.id"),
            nullable=True,
        ),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("created_by_task_id", sa.String(length=255), nullable=True),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_media_asset_owner_scope",
        "media_asset",
        ["owner_id", "visibility_scope"],
        unique=False,
    )
    op.create_index(
        "ix_media_asset_media_type", "media_asset", ["media_type"], unique=False
    )
    op.create_index(
        "ix_media_asset_created_at", "media_asset", ["created_at"], unique=False
    )

    op.create_table(
        "media_library_settings",
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column(
            "enable_group_sharing",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "allow_bulk_download",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("allowed_media_types", sa.JSON(), nullable=True),
        sa.Column(
            "default_visibility",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text(f"'{VISIBILITY_USER}'"),
        ),
        sa.Column("max_storage_per_user", sa.BigInteger(), nullable=True),
        sa.Column("max_storage_per_group", sa.BigInteger(), nullable=True),
        sa.Column("signed_url_ttl_seconds", sa.Integer(), nullable=True),
        sa.Column("thumbnail_strategy", sa.String(length=50), nullable=True),
        sa.Column("extra_config", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "media_asset_audit",
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column(
            "asset_id",
            sa.String(length=255),
            sa.ForeignKey("media_asset.id"),
            nullable=False,
        ),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("actor_role", sa.String(length=50), nullable=True),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_media_asset_audit_asset_id", "media_asset_audit", ["asset_id"], unique=False
    )
    op.create_index(
        "ix_media_asset_audit_created_at",
        "media_asset_audit",
        ["created_at"],
        unique=False,
    )

    conn = op.get_bind()
    existing = conn.execute(
        sa.text("SELECT id FROM media_library_settings WHERE id = :id"),
        {"id": "default"},
    ).fetchone()

    if not existing:
        conn.execute(
            sa.text(
                """
                INSERT INTO media_library_settings (
                    id,
                    enable_group_sharing,
                    allow_bulk_download,
                    allowed_media_types,
                    default_visibility,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :enable_group_sharing,
                    :allow_bulk_download,
                    NULL,
                    :default_visibility,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": "default",
                "enable_group_sharing": False,
                "allow_bulk_download": True,
                "default_visibility": VISIBILITY_USER,
            },
        )


def downgrade() -> None:
    op.drop_index("ix_media_asset_audit_created_at", table_name="media_asset_audit")
    op.drop_index("ix_media_asset_audit_asset_id", table_name="media_asset_audit")
    op.drop_table("media_asset_audit")

    op.drop_table("media_library_settings")

    op.drop_index("ix_media_asset_created_at", table_name="media_asset")
    op.drop_index("ix_media_asset_media_type", table_name="media_asset")
    op.drop_index("ix_media_asset_owner_scope", table_name="media_asset")
    op.drop_table("media_asset")

    op.drop_index("ix_media_folder_owner_scope", table_name="media_folder")
    op.drop_table("media_folder")
