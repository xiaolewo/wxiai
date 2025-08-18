"""Merge multiple heads

Revision ID: 1f045f7aebc5
Revises: a1b2c3d4e5f6, b8f3a2c9d1e0
Create Date: 2025-08-18 03:25:13.190496

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = "1f045f7aebc5"
down_revision: Union[str, None] = ("a1b2c3d4e5f6", "b8f3a2c9d1e0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
