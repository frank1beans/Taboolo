"""add table for price list offers

Revision ID: 20251117_price_list_offer
Revises: 20251116_import_config_wbs_columns
Create Date: 2025-11-17 21:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251117_price_list_offer"
down_revision = "20251116_import_config_wbs_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_list_offer",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("price_list_item_id", sa.Integer(), sa.ForeignKey("price_list_item.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commessa_id", sa.Integer(), sa.ForeignKey("commessa.id"), nullable=False),
        sa.Column("computo_id", sa.Integer(), sa.ForeignKey("computo.id"), nullable=False),
        sa.Column("impresa_id", sa.Integer(), sa.ForeignKey("impresa.id"), nullable=True),
        sa.Column("impresa_label", sa.String(), nullable=True),
        sa.Column("round_number", sa.Integer(), nullable=True),
        sa.Column("prezzo_unitario", sa.Float(), nullable=False),
        sa.Column("quantita", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "price_list_item_id",
            "computo_id",
            name="uq_price_list_offer_item_computo",
        ),
    )
    op.create_index(
        "ix_price_list_offer_commessa_id", "price_list_offer", ["commessa_id"]
    )
    op.create_index(
        "ix_price_list_offer_computo_id", "price_list_offer", ["computo_id"]
    )
    op.create_index(
        "ix_price_list_offer_price_list_item_id",
        "price_list_offer",
        ["price_list_item_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_price_list_offer_price_list_item_id", table_name="price_list_offer"
    )
    op.drop_index("ix_price_list_offer_computo_id", table_name="price_list_offer")
    op.drop_index("ix_price_list_offer_commessa_id", table_name="price_list_offer")
    op.drop_table("price_list_offer")
