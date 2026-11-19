"""create jobs table

Revision ID: 67b685a54d89
Revises: 
Create Date: 2026-10-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '67b685a54d89'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company', sa.String(length=100), nullable=False),
        sa.Column('position', sa.String(length=150), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='Заинтересован'),
        sa.Column('notes', sa.Text(), nullable=False, server_default=''),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('jobs')