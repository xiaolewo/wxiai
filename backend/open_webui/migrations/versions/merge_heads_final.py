"""merge multiple heads final

Revision ID: merge_heads_final
Revises: 24e8f9a7b1c2, abc123def456
Create Date: 2025-01-14 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "merge_heads_final"
down_revision: Union[str, None] = ("24e8f9a7b1c2", "abc123def456")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge multiple heads - no changes needed"""
    pass


def downgrade() -> None:
    """Downgrade merge - no changes needed"""
    pass
