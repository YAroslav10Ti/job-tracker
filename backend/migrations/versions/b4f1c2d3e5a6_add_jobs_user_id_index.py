"""add index on jobs.user_id

Revision ID: b4f1c2d3e5a6
Revises: 8d1a1b79af4a
Create Date: 2026-11-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b4f1c2d3e5a6"
down_revision: Union[str, Sequence[str], None] = "8d1a1b79af4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_jobs_user_id", table_name="jobs")
