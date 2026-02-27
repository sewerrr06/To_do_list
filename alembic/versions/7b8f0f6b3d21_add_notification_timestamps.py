"""add notification timestamps

Revision ID: 7b8f0f6b3d21
Revises: 1c94c2948a76
Create Date: 2026-02-27 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b8f0f6b3d21"
down_revision: Union[str, Sequence[str], None] = "1c94c2948a76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("completed_notified_at", sa.DateTime(), nullable=True))
    op.add_column("tasks", sa.Column("overdue_notified_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "overdue_notified_at")
    op.drop_column("tasks", "completed_notified_at")
