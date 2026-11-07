"""phase7_writing_assistant_intelligence

Revision ID: 6f1b2a3c4d5e
Revises: 5e9a2f1b4c3d
Create Date: 2026-11-06 16:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '6f1b2a3c4d5e'
down_revision: Union[str, Sequence[str], None] = '5e9a2f1b4c3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_cols = [c['name'] for c in inspector.get_columns('writing_drafts')]

    # Add columns to writing_drafts with batch mode for SQLite compatibility
    with op.batch_alter_table('writing_drafts', schema=None) as batch_op:
        if 'organization_id' not in existing_cols:
            batch_op.add_column(sa.Column('organization_id', sa.String(length=36), nullable=True))
            batch_op.create_foreign_key(
                'fk_writing_drafts_organization_id',
                'organizations',
                ['organization_id'],
                ['id'],
                ondelete='CASCADE'
            )
            batch_op.create_index('ix_drafts_org_created', ['organization_id', 'created_at'], unique=False)

        if 'brief_id' not in existing_cols:
            batch_op.add_column(sa.Column('brief_id', sa.String(length=36), nullable=True))
            batch_op.create_foreign_key(
                'fk_writing_drafts_brief_id',
                'research_briefs',
                ['brief_id'],
                ['id'],
                ondelete='SET NULL'
            )

        if 'content_type' not in existing_cols:
            batch_op.add_column(sa.Column('content_type', sa.String(length=50), nullable=False, server_default='editorial_analysis'))

        if 'target_audience' not in existing_cols:
            batch_op.add_column(sa.Column('target_audience', sa.String(length=100), nullable=True, server_default='Founders, builders, and operators'))

        if 'tone' not in existing_cols:
            batch_op.add_column(sa.Column('tone', sa.String(length=100), nullable=True, server_default='Authoritative, analytical, objective'))

        if 'desired_length' not in existing_cols:
            batch_op.add_column(sa.Column('desired_length', sa.Integer(), nullable=True, server_default='800'))

        if 'research_grounding_score' not in existing_cols:
            batch_op.add_column(sa.Column('research_grounding_score', sa.Float(), nullable=True))

        if 'unsupported_claims_count' not in existing_cols:
            batch_op.add_column(sa.Column('unsupported_claims_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    with op.batch_alter_table('writing_drafts', schema=None) as batch_op:
        batch_op.drop_index('ix_drafts_org_created')
        batch_op.drop_constraint('fk_writing_drafts_brief_id', type_='foreignkey')
        batch_op.drop_constraint('fk_writing_drafts_organization_id', type_='foreignkey')
        batch_op.drop_column('unsupported_claims_count')
        batch_op.drop_column('research_grounding_score')
        batch_op.drop_column('desired_length')
        batch_op.drop_column('tone')
        batch_op.drop_column('target_audience')
        batch_op.drop_column('content_type')
        batch_op.drop_column('brief_id')
        batch_op.drop_column('organization_id')

