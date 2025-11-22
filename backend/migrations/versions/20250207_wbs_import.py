"""add commessa stato and wbs7 commessa link

Revision ID: 20250207_wbs_import
Revises: 20250204_wbs_schema
Create Date: 2025-02-07 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250207_wbs_import"
down_revision = "20250204_wbs_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    commessa_columns = {column["name"] for column in inspector.get_columns("commessa")}
    if "stato" not in commessa_columns:
        op.add_column(
            "commessa",
            sa.Column(
                "stato",
                sa.String(length=32),
                nullable=False,
                server_default="setup",
            ),
        )
        op.alter_column("commessa", "stato", server_default=None)
    else:
        op.execute("UPDATE commessa SET stato = 'setup' WHERE stato IS NULL OR stato = ''")

    wbs7_columns = {column["name"] for column in inspector.get_columns("wbs7")}
    if "commessa_id" not in wbs7_columns:
        op.add_column(
            "wbs7",
            sa.Column(
                "commessa_id",
                sa.Integer(),
                nullable=True,
            ),
        )
    op.execute(
        """
        UPDATE wbs7
        SET commessa_id = (
            SELECT commessa_id
            FROM wbs6
            WHERE wbs6.id = wbs7.wbs6_id
        )
        WHERE commessa_id IS NULL
        """
    )
    fk_names = {fk["name"] for fk in inspector.get_foreign_keys("wbs7")}
    with op.batch_alter_table("wbs7") as batch_op:
        batch_op.alter_column("commessa_id", existing_type=sa.Integer(), nullable=False)
        if "fk_wbs7_commessa" not in fk_names:
            batch_op.create_foreign_key(
                "fk_wbs7_commessa",
                "commessa",
                ["commessa_id"],
                ["id"],
                ondelete="CASCADE",
            )

    index_names = {idx["name"] for idx in inspector.get_indexes("wbs7")}
    if "ix_wbs7_commessa_id" not in index_names:
        op.create_index("ix_wbs7_commessa_id", "wbs7", ["commessa_id"])


def downgrade() -> None:
    op.drop_index("ix_wbs7_commessa_id", table_name="wbs7")
    op.drop_constraint("fk_wbs7_commessa", "wbs7", type_="foreignkey")
    with op.batch_alter_table("wbs7") as batch_op:
        batch_op.drop_column("commessa_id")
    op.drop_column("commessa", "stato")
