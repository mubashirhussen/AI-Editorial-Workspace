"""Phase 22 Research Project Fields and Brief Edits

Revision ID: 9c4d5e6f7a8b
Revises: 8b3c4d5e6f7a
Create Date: 2026-11-12 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c4d5e6f7a8b'
down_revision = '8b3c4d5e6f7a'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Update research_projects table with enterprise metadata fields
    with op.batch_alter_table('research_projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('topic', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('research_objective', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('target_audience', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('research_scope', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('keywords', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('preferred_source_types', sa.JSON(), nullable=True))

    # 2. Update research_briefs table with is_user_edited, user_notes, version
    with op.batch_alter_table('research_briefs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_user_edited', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('user_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))


def downgrade():
    with op.batch_alter_table('research_briefs', schema=None) as batch_op:
        batch_op.drop_column('version')
        batch_op.drop_column('user_notes')
        batch_op.drop_column('is_user_edited')

    with op.batch_alter_table('research_projects', schema=None) as batch_op:
        batch_op.drop_column('preferred_source_types')
        batch_op.drop_column('keywords')
        batch_op.drop_column('research_scope')
        batch_op.drop_column('target_audience')
        batch_op.drop_column('research_objective')
        batch_op.drop_column('topic')

