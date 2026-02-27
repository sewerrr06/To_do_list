"""Add email

Revision ID: 1c94c2948a76
Revises: 22153d830663
Create Date: 2026-02-27 10:55:50.491512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1c94c2948a76'
down_revision: Union[str, Sequence[str], None] = '22153d830663'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tasks', sa.Column('notification_email', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tasks', 'notification_email')
