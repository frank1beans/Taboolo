"""add price_list_item link to voce

Revision ID: 20251117_voce_price_list_link
Revises: 20251117_matching_report
Create Date: 2025-11-17 22:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251117_voce_price_list_link"
down_revision = "20251117_matching_report"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "voce",
        sa.Column("price_list_item_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_voce_price_list_item",
        "voce",
        "price_list_item",
        ["price_list_item_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_voce_price_list_item", "voce", type_="foreignkey")
    op.drop_column("voce", "price_list_item_id")
