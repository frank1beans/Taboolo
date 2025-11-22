"""Add performance indexes for query optimization

Revision ID: 20251120_perf_idx
Revises: 20251119_security
Create Date: 2025-11-20 10:00:00.000000

This migration adds missing indexes on frequently filtered columns
to improve query performance, especially for:
- Insights/Analisi queries
- Semantic search
- Price list lookups
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251120_perf_idx"
# Merge di tutti i branch esistenti
down_revision = (
    "20251119_security",
    "20251117_voce_price_list_link",
    "20250218_drop_import_config_wbs_columns",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # VoceComputo indexes - critical for insights queries
    op.create_index(
        "ix_vocecomputo_commessa_id",
        "vocecomputo",
        ["commessa_id"]
    )
    op.create_index(
        "ix_vocecomputo_computo_id",
        "vocecomputo",
        ["computo_id"]
    )
    # Composite index for queries filtering both
    op.create_index(
        "ix_vocecomputo_commessa_computo",
        "vocecomputo",
        ["commessa_id", "computo_id"]
    )

    # PriceListItem index - critical for semantic search
    op.create_index(
        "ix_price_list_item_commessa_id",
        "price_list_item",
        ["commessa_id"]
    )

    # Voce (normalized) indexes - used in insights for legacy mapping
    op.create_index(
        "ix_voce_commessa_id",
        "voce",
        ["commessa_id"]
    )
    op.create_index(
        "ix_voce_legacy_vocecomputo_id",
        "voce",
        ["legacy_vocecomputo_id"]
    )


def downgrade() -> None:
    # Voce indexes
    op.drop_index("ix_voce_legacy_vocecomputo_id", table_name="voce")
    op.drop_index("ix_voce_commessa_id", table_name="voce")

    # PriceListItem index
    op.drop_index("ix_price_list_item_commessa_id", table_name="price_list_item")

    # VoceComputo indexes
    op.drop_index("ix_vocecomputo_commessa_computo", table_name="vocecomputo")
    op.drop_index("ix_vocecomputo_computo_id", table_name="vocecomputo")
    op.drop_index("ix_vocecomputo_commessa_id", table_name="vocecomputo")
