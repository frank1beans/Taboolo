"""add analisi thresholds columns

Revision ID: 20251110_130728_add_analisi_thresholds
Revises: 20250208_wbs_visibility
Create Date: 2025-11-10 13:07:28.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251110_130728_add_analisi_thresholds"
down_revision = "20250208_wbs_visibility"
branch_labels = None
depends_on = None


DEFAULT_MEDIA = 25.0
DEFAULT_ALTA = 50.0


def upgrade() -> None:
    with op.batch_alter_table("settings") as batch_op:
        batch_op.add_column(
            sa.Column("criticita_media_percent", sa.Float(), nullable=False, server_default=str(DEFAULT_MEDIA))
        )
        batch_op.add_column(
            sa.Column("criticita_alta_percent", sa.Float(), nullable=False, server_default=str(DEFAULT_ALTA))
        )
    with op.batch_alter_table("settings") as batch_op:
        batch_op.alter_column("criticita_media_percent", server_default=None)
        batch_op.alter_column("criticita_alta_percent", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("settings") as batch_op:
        batch_op.drop_column("criticita_alta_percent")
        batch_op.drop_column("criticita_media_percent")
