"""Add quantity column reference to import configurations

Revision ID: 20251114_import_config_quantity_column
Revises: 20251111_price_catalog
Create Date: 2025-11-14 15:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251114_import_config_quantity_column"
down_revision = "20251111_price_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "import_config",
        sa.Column("quantity_column", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("import_config", "quantity_column")
