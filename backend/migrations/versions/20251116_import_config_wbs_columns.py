"""Add WBS6 column mapping to import configurations

Revision ID: 20251116_import_config_wbs_columns
Revises: 20251114_import_config_quantity_column
Create Date: 2025-11-16 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251116_import_config_wbs_columns"
down_revision = "20251114_import_config_quantity_column"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "import_config",
        sa.Column("wbs6_code_column", sa.String(), nullable=True),
    )
    op.add_column(
        "import_config",
        sa.Column("wbs6_description_column", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("import_config", "wbs6_description_column")
    op.drop_column("import_config", "wbs6_code_column")
