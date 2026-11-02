"""Создание таблицы

Revision ID: 67b685a54d89
Revises: 
Create Date: 2026-10-23 00:00:52.282834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67b685a54d89'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company", sa.String(length=100), nullable=False),
        sa.Column("position", sa.String(length=150), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="jobs_pkey"),
    )
    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS jobs_id_seq OWNED BY jobs.id"
    )
    op.execute(
        "ALTER TABLE jobs ALTER COLUMN id "
        "SET DEFAULT nextval('jobs_id_seq'::regclass)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("jobs")
    op.execute("DROP SEQUENCE IF EXISTS jobs_id_seq")
