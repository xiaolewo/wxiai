"""merge_multiple_heads

Revision ID: 67040b222ae7
Revises: a1e2f3g4h5i6, google_video_001, gpt_image_002, klz1a2b3c4d5
Create Date: 2025-08-22 16:50:25.565748

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = "67040b222ae7"
down_revision: Union[str, None] = (
    "a1e2f3g4h5i6",
    "google_video_001",
    "gpt_image_002",
    "klz1a2b3c4d5",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
