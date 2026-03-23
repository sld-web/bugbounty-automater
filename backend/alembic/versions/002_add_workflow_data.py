"""Add workflow_data to programs

Revision ID: 002_add_workflow_data
Revises: 001_initial
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa


revision = '002_add_workflow_data'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('programs', sa.Column('workflow_data', sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column('programs', 'workflow_data')
