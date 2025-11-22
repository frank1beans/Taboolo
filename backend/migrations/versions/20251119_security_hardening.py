"""Add refresh tokens and extend audit log for ISO hardening

Revision ID: 20251119_security
Revises: 20251118_auth_models
Create Date: 2025-11-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251119_security'
down_revision = '20251118_auth_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audit_log', sa.Column('method', sa.String(), nullable=True))
    op.add_column('audit_log', sa.Column('payload_hash', sa.String(), nullable=True))
    op.add_column('audit_log', sa.Column('outcome', sa.String(), nullable=True))

    op.create_table(
        'refresh_token',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('app_user.id'), nullable=False),
        sa.Column('token_fingerprint', sa.String(), index=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('replaced_by_id', sa.Integer(), sa.ForeignKey('refresh_token.id'), nullable=True),
    )

    op.execute("UPDATE app_user SET role='project_manager' WHERE role='manager'")
    op.execute("UPDATE app_user SET role='viewer' WHERE role='user'")


def downgrade() -> None:
    op.drop_table('refresh_token')
    op.drop_column('audit_log', 'method')
    op.drop_column('audit_log', 'payload_hash')
    op.drop_column('audit_log', 'outcome')
