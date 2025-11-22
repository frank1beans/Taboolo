"""create WBS normalized schema

Revision ID: 20250204_wbs_schema
Revises:
Create Date: 2025-02-04 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250204_wbs_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wbs_spaziale",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("commessa_id", sa.Integer(), sa.ForeignKey("commessa.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("wbs_spaziale.id", ondelete="CASCADE"), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("importo_totale", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("commessa_id", "level", "code", name="uq_wbs_spaziale_commessa_level_code"),
    )

    op.create_table(
        "wbs6",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("commessa_id", sa.Integer(), sa.ForeignKey("commessa.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wbs_spaziale_id", sa.Integer(), sa.ForeignKey("wbs_spaziale.id", ondelete="SET NULL"), nullable=True),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("commessa_id", "code", name="uq_wbs6_commessa_code"),
    )
    op.create_index("ix_wbs6_wbs_spaziale_id", "wbs6", ["wbs_spaziale_id"])

    op.create_table(
        "wbs7",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("wbs6_id", sa.Integer(), sa.ForeignKey("wbs6.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("wbs6_id", "code", name="uq_wbs7_wbs6_code"),
    )

    op.create_table(
        "impresa",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("normalized_label", sa.String(length=255), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("normalized_label", name="uq_impresa_normalized_label"),
    )

    op.create_table(
        "voce",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("commessa_id", sa.Integer(), sa.ForeignKey("commessa.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wbs6_id", sa.Integer(), sa.ForeignKey("wbs6.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wbs7_id", sa.Integer(), sa.ForeignKey("wbs7.id", ondelete="SET NULL"), nullable=True),
        sa.Column("legacy_vocecomputo_id", sa.Integer(), sa.ForeignKey("vocecomputo.id", ondelete="SET NULL"), nullable=True),
        sa.Column("codice", sa.String(length=64), nullable=True),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("unita_misura", sa.String(length=32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("ordine", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "commessa_id",
            "wbs6_id",
            "codice",
            "ordine",
            name="uq_voce_commessa_wbs6_codice_ordine",
        ),
        sa.UniqueConstraint(
            "legacy_vocecomputo_id",
            name="uq_voce_legacy",
        ),
    )
    op.create_index("ix_voce_wbs6_id", "voce", ["wbs6_id"])

    op.create_table(
        "voce_progetto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("voce_id", sa.Integer(), sa.ForeignKey("voce.id", ondelete="CASCADE"), nullable=False),
        sa.Column("computo_id", sa.Integer(), sa.ForeignKey("computo.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantita", sa.Float(), nullable=True),
        sa.Column("prezzo_unitario", sa.Float(), nullable=True),
        sa.Column("importo", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("voce_id", name="uq_voce_progetto_voce"),
    )

    op.create_table(
        "voce_offerta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("voce_id", sa.Integer(), sa.ForeignKey("voce.id", ondelete="CASCADE"), nullable=False),
        sa.Column("computo_id", sa.Integer(), sa.ForeignKey("computo.id", ondelete="CASCADE"), nullable=False),
        sa.Column("impresa_id", sa.Integer(), sa.ForeignKey("impresa.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=True),
        sa.Column("quantita", sa.Float(), nullable=True),
        sa.Column("prezzo_unitario", sa.Float(), nullable=True),
        sa.Column("importo", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "voce_id",
            "computo_id",
            "impresa_id",
            name="uq_voce_offerta_voce_computo_impresa",
        ),
    )
    op.create_index("ix_voce_offerta_impresa", "voce_offerta", ["impresa_id"])
    op.create_index("ix_voce_offerta_computo", "voce_offerta", ["computo_id"])


def downgrade() -> None:
    op.drop_index("ix_voce_offerta_computo", table_name="voce_offerta")
    op.drop_index("ix_voce_offerta_impresa", table_name="voce_offerta")
    op.drop_table("voce_offerta")
    op.drop_table("voce_progetto")
    op.drop_index("ix_voce_wbs6_id", table_name="voce")
    op.drop_table("voce")
    op.drop_table("impresa")
    op.drop_table("wbs7")
    op.drop_index("ix_wbs6_wbs_spaziale_id", table_name="wbs6")
    op.drop_table("wbs6")
    op.drop_table("wbs_spaziale")
