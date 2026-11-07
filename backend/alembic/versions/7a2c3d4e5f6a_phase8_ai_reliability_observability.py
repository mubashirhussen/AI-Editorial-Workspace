"""Phase 8 AI Reliability, Observability & Cost Tracking

Revision ID: 7a2c3d4e5f6a
Revises: 6f1b2a3c4d5e
Create Date: 2026-11-07 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a2c3d4e5f6a'
down_revision = '6f1b2a3c4d5e'
branch_labels = None
depends_on = None


def upgrade():
    # Add prompt_version and estimated_cost_usd columns to provider_usage_records
    with op.batch_alter_table('provider_usage_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prompt_version', sa.String(length=50), nullable=True, server_default='v1.0.0'))
        batch_op.add_column(sa.Column('estimated_cost_usd', sa.Float(), nullable=False, server_default='0.0'))


def downgrade():
    with op.batch_alter_table('provider_usage_records', schema=None) as batch_op:
        batch_op.drop_column('estimated_cost_usd')
        batch_op.drop_column('prompt_version')
