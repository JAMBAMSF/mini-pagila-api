"""Create streaming_subscription

Revision ID: 0002_streaming_subscription
Revises: 0001_add_streaming_available
Create Date: 2024-09-01 00:05:00
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_streaming_subscription"
down_revision = "0001_add_streaming_available"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "streaming_subscription",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.SmallInteger(), sa.ForeignKey("customer.customer_id"), nullable=False),
        sa.Column("plan_name", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("streaming_subscription")
