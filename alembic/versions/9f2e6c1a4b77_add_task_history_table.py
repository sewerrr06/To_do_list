"""add task history table

Revision ID: 9f2e6c1a4b77
Revises: 7b8f0f6b3d21
Create Date: 2026-02-27 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f2e6c1a4b77"
down_revision: Union[str, Sequence[str], None] = "7b8f0f6b3d21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "CREATED",
                "UPDATED",
                "STATUS_CHANGED",
                "DELETED",
                "NOTIFIED_COMPLETED",
                "NOTIFIED_OVERDUE",
                name="taskeventtype",
            ),
            nullable=False,
        ),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("changed_fields", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_history_id"), "task_history", ["id"], unique=False)
    op.create_index(op.f("ix_task_history_task_id"), "task_history", ["task_id"], unique=False)
    op.create_index(op.f("ix_task_history_event_type"), "task_history", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_history_event_type"), table_name="task_history")
    op.drop_index(op.f("ix_task_history_task_id"), table_name="task_history")
    op.drop_index(op.f("ix_task_history_id"), table_name="task_history")
    op.drop_table("task_history")
    sa.Enum(name="taskeventtype").drop(op.get_bind(), checkfirst=True)
