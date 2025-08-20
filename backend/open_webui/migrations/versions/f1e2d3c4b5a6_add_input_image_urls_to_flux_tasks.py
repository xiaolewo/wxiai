"""add_input_image_urls_to_flux_tasks

Revision ID: f1e2d3c4b5a6
Revises: 22c97ff924a3
Create Date: 2025-08-19 17:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "f1e2d3c4b5a6"
down_revision: Union[str, None] = "22c97ff924a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to flux_tasks table for multi-image support
    try:
        # Add input_image_urls column for storing multiple image URLs (JSON array)
        op.add_column(
            "flux_tasks",
            sa.Column(
                "input_image_urls",
                sqlite.JSON(),
                nullable=True,
                comment="多图片URL列表（多图编辑）",
            ),
        )

        # Add image_size column for Dev version parameter support
        op.add_column(
            "flux_tasks",
            sa.Column(
                "image_size",
                sqlite.JSON(),
                nullable=True,
                comment="图片尺寸参数（Dev版本）",
            ),
        )

    except Exception as e:
        # If columns already exist, ignore the error
        print(f"Column might already exist: {e}")


def downgrade() -> None:
    # Remove the added columns
    try:
        op.drop_column("flux_tasks", "input_image_urls")
        op.drop_column("flux_tasks", "image_size")
    except Exception as e:
        print(f"Error dropping columns: {e}")
