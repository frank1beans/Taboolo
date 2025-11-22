"""Add semantic model settings columns.

Revision ID: 20250218_nlp_settings
Revises: 20251117_price_list_offer
Create Date: 2025-02-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20250218_nlp_settings"
down_revision: Union[str, None] = "20251117_price_list_offer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "settings",
        sa.Column(
            "nlp_model_id",
            sa.String(),
            nullable=False,
            server_default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        ),
    )
    op.add_column(
        "settings",
        sa.Column("nlp_batch_size", sa.Integer(), nullable=False, server_default="32"),
    )
    op.add_column(
        "settings",
        sa.Column("nlp_max_length", sa.Integer(), nullable=False, server_default="256"),
    )
    op.add_column(
        "settings",
        sa.Column("nlp_embeddings_model_id", sa.String(), nullable=True),
    )

    # Allinea il modello embedding corrente al modello selezionato per evitare falsi positivi
    op.execute(
        "UPDATE settings SET nlp_embeddings_model_id = nlp_model_id WHERE nlp_embeddings_model_id IS NULL"
    )

    # Rimuove i server_default per lasciare la gestione a livello applicativo
    with op.batch_alter_table("settings") as batch_op:
        batch_op.alter_column("nlp_model_id", server_default=None)
        batch_op.alter_column("nlp_batch_size", server_default=None)
        batch_op.alter_column("nlp_max_length", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("settings") as batch_op:
        batch_op.drop_column("nlp_embeddings_model_id")
        batch_op.drop_column("nlp_max_length")
        batch_op.drop_column("nlp_batch_size")
        batch_op.drop_column("nlp_model_id")
