"""add price catalog and metadata columns

Revision ID: 20251111_price_catalog
Revises: 20251110_130728_add_analisi_thresholds
Create Date: 2025-11-11 19:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251111_price_catalog"
down_revision = "20251110_130728_add_analisi_thresholds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("computo", sa.Column("commessa_code", sa.String(), nullable=True))
    op.create_index("ix_computo_commessa_code", "computo", ["commessa_code"])

    op.add_column(
        "vocecomputo",
        sa.Column("commessa_id", sa.Integer(), sa.ForeignKey("commessa.id"), nullable=True),
    )
    op.add_column("vocecomputo", sa.Column("commessa_code", sa.String(), nullable=True))
    op.add_column("vocecomputo", sa.Column("global_code", sa.String(), nullable=True))
    op.add_column("vocecomputo", sa.Column("extra_metadata", sa.JSON(), nullable=True))
    op.create_index("ix_vocecomputo_commessa_code", "vocecomputo", ["commessa_code"])
    op.create_index("ix_vocecomputo_global_code", "vocecomputo", ["global_code"])

    op.create_table(
        "price_list_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("commessa_id", sa.Integer(), sa.ForeignKey("commessa.id"), nullable=False),
        sa.Column("commessa_code", sa.String(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("global_code", sa.String(), nullable=False),
        sa.Column("item_code", sa.String(), nullable=False),
        sa.Column("item_description", sa.String(), nullable=True),
        sa.Column("unit_id", sa.String(), nullable=True),
        sa.Column("unit_label", sa.String(), nullable=True),
        sa.Column("wbs6_code", sa.String(), nullable=True),
        sa.Column("wbs6_description", sa.String(), nullable=True),
        sa.Column("wbs7_code", sa.String(), nullable=True),
        sa.Column("wbs7_description", sa.String(), nullable=True),
        sa.Column("price_lists", sa.JSON(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("source_file", sa.String(), nullable=True),
        sa.Column("preventivo_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "commessa_id",
            "product_id",
            name="uq_price_list_item_commessa_product",
        ),
        sa.UniqueConstraint(
            "global_code",
            name="uq_price_list_item_global_code",
        ),
    )
    op.create_index("ix_price_list_item_commessa_code", "price_list_item", ["commessa_code"])
    op.create_index("ix_price_list_item_item_code", "price_list_item", ["item_code"])
    op.create_index("ix_price_list_item_global_code", "price_list_item", ["global_code"])

    op.execute(
        """
        UPDATE computo
        SET commessa_code = (
            SELECT codice FROM commessa WHERE commessa.id = computo.commessa_id
        )
        """
    )
    op.execute(
        """
        UPDATE vocecomputo
        SET commessa_id = (
                SELECT commessa_id FROM computo WHERE computo.id = vocecomputo.computo_id
            ),
            commessa_code = (
                SELECT commessa_code FROM computo WHERE computo.id = vocecomputo.computo_id
            ),
            global_code = CASE
                WHEN (SELECT commessa_code FROM computo WHERE computo.id = vocecomputo.computo_id) IS NOT NULL
                     AND vocecomputo.codice IS NOT NULL
                THEN (SELECT commessa_code FROM computo WHERE computo.id = vocecomputo.computo_id) || '::' || vocecomputo.codice
                ELSE NULL
            END
        """
    )


def downgrade() -> None:
    op.drop_index("ix_price_list_item_global_code", table_name="price_list_item")
    op.drop_index("ix_price_list_item_item_code", table_name="price_list_item")
    op.drop_index("ix_price_list_item_commessa_code", table_name="price_list_item")
    op.drop_table("price_list_item")

    op.drop_index("ix_vocecomputo_global_code", table_name="vocecomputo")
    op.drop_index("ix_vocecomputo_commessa_code", table_name="vocecomputo")
    op.drop_column("vocecomputo", "extra_metadata")
    op.drop_column("vocecomputo", "global_code")
    op.drop_column("vocecomputo", "commessa_code")
    op.drop_column("vocecomputo", "commessa_id")

    op.drop_index("ix_computo_commessa_code", table_name="computo")
    op.drop_column("computo", "commessa_code")
