"""Add impresa_id to computo and enforce uniqueness per round

Revision ID: 20251121_add_impresa_to_computo
Revises: 20251120_performance_indexes
Create Date: 2025-11-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251121_add_impresa_to_computo"
down_revision: Union[str, None] = "20251120_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aggiunge impresa_id su computo (ritorni) e crea un indice unico per evitare duplicati per round
    op.add_column("computo", sa.Column("impresa_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_computo_impresa",
        "computo",
        "impresa",
        ["impresa_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Unique opzionale: commessa_id + impresa_id + round_number (ammessi NULL -> gestito a livello applicativo)
    op.create_unique_constraint(
        "uq_computo_commessa_impresa_round",
        "computo",
        ["commessa_id", "impresa_id", "round_number"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_computo_commessa_impresa_round", "computo", type_="unique")
    op.drop_constraint("fk_computo_impresa", "computo", type_="foreignkey")
    op.drop_column("computo", "impresa_id")
