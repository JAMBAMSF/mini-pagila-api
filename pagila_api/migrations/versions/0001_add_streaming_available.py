"""Add streaming_available to film

Revision ID: 0001_add_streaming_available
Revises: 
Create Date: 2024-09-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_add_streaming_available"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "film",
        sa.Column("streaming_available", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("film", "streaming_available")
