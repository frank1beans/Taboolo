"""add matching_report column to computo

Revision ID: 20251117_matching_report
Revises: 20251117_price_list_offer
Create Date: 2025-11-17 22:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251117_matching_report"
down_revision = "20251117_price_list_offer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "computo",
        sa.Column("matching_report", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("computo", "matching_report")
