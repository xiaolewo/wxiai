"""merge all heads final

Revision ID: g3h4i5j6k7l8
Revises: 68ab2b32, 68ab2be4, f2g3h4i5j6k7, f4e8b6c2a1d9
Create Date: 2025-08-26 12:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "g3h4i5j6k7l8"
down_revision: Union[str, None] = (
    "68ab2b32",
    "68ab2be4",
    "f2g3h4i5j6k7",
    "f4e8b6c2a1d9",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge all heads - no schema changes needed as all features are already deployed"""
    pass


def downgrade() -> None:
    """Downgrade merge - no changes needed"""
    pass
