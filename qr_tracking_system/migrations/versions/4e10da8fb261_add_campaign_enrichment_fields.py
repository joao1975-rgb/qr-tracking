"""add_campaign_enrichment_fields

Revision ID: 4e10da8fb261
Revises: dd7c927a1062
Create Date: 2026-03-21 21:04:24.110308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e10da8fb261'
down_revision: Union[str, Sequence[str], None] = 'dd7c927a1062'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
