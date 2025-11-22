"""add wbs visibility table

Revision ID: 20250208_wbs_visibility
Revises: 20250207_wbs_import
Create Date: 2025-02-08 09:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250208_wbs_visibility"
down_revision = "20250207_wbs_import"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wbs_visibility",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "commessa_id",
            sa.Integer(),
            sa.ForeignKey("commessa.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "commessa_id",
            "kind",
            "node_id",
            name="uq_wbs_visibility_commessa_node",
        ),
    )
    op.create_index("ix_wbs_visibility_commessa_id", "wbs_visibility", ["commessa_id"])


def downgrade() -> None:
    op.drop_index("ix_wbs_visibility_commessa_id", table_name="wbs_visibility")
    op.drop_table("wbs_visibility")
