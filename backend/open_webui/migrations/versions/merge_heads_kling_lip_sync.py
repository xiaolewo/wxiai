"""merge multiple heads for kling lip sync

Revision ID: merge_heads_kling_lip_sync
Revises: 68ab2b32, 68ab2be4, e1f2g3h4i5j6, f4e8b6c2a1d9
Create Date: 2024-12-25 03:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "merge_heads_kling_lip_sync"
down_revision = ("68ab2b32", "68ab2be4", "e1f2g3h4i5j6", "f4e8b6c2a1d9")
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no schema changes needed
    # All the actual changes are in the individual migrations being merged
    pass


def downgrade():
    # This is a merge migration - no downgrade needed
    # The individual migrations handle their own downgrades
    pass
