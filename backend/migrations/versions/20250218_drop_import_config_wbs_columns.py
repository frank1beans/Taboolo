"""Remove WBS6 columns from import_config.

Revision ID: 20250218_drop_import_config_wbs_columns
Revises: 20250218_nlp_settings
Create Date: 2025-02-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20250218_drop_import_config_wbs_columns"
down_revision: Union[str, None] = "20250218_nlp_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("import_config") as batch_op:
        batch_op.drop_column("wbs6_code_column")
        batch_op.drop_column("wbs6_description_column")


def downgrade() -> None:
    with op.batch_alter_table("import_config") as batch_op:
        batch_op.add_column(sa.Column("wbs6_code_column", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("wbs6_description_column", sa.String(), nullable=True))
