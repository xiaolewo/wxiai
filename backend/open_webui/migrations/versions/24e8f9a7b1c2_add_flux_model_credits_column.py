"""add_flux_model_credits_column

Revision ID: 24e8f9a7b1c2
Revises: f1e2d3c4b5a6
Create Date: 2025-08-20 15:50:00.000000

"""

from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "24e8f9a7b1c2"
down_revision: Union[str, None] = "f1e2d3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Add model_credits column to flux_config table ###

    # Add the model_credits column as TEXT (JSON)
    op.add_column(
        "flux_config",
        sa.Column("model_credits", sa.TEXT(), nullable=True, comment="各模型积分配置"),
    )

    # Set default model credits for existing records
    default_credits_json = json.dumps(
        {
            "fal-ai/flux-1/schnell": 5,
            "fal-ai/flux-1/dev": 10,
            "fal-ai/flux-1/dev/image-to-image": 10,
            "fal-ai/flux-pro": 20,
            "fal-ai/flux-pro/kontext": 25,
            "fal-ai/flux-pro/kontext/multi": 30,
            "fal-ai/flux-pro/max": 35,
        }
    )

    # Update existing records with default values
    op.execute(
        f"""
        UPDATE flux_config 
        SET model_credits = '{default_credits_json}' 
        WHERE model_credits IS NULL
    """
    )

    # ### end add model_credits column ###


def downgrade() -> None:
    # ### Remove model_credits column ###
    op.drop_column("flux_config", "model_credits")
    # ### end remove model_credits column ###
