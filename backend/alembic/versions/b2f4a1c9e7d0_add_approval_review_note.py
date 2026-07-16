"""add review_note to approval queue items

Revision ID: b2f4a1c9e7d0
Revises: d1888b94f5b1
Create Date: 2026-07-16 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f4a1c9e7d0'
down_revision: Union[str, None] = 'd1888b94f5b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('approval_queue_items', sa.Column('review_note', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('approval_queue_items', 'review_note')
