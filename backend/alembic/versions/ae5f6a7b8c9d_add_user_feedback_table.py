"""Phase 36 Add User Feedback Table

Revision ID: ae5f6a7b8c9d
Revises: 9c4d5e6f7a8b
Create Date: 2026-11-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae5f6a7b8c9d'
down_revision = '9c4d5e6f7a8b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_feedbacks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('module_reference', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='NEW'),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user_feedbacks', schema=None) as batch_op:
        batch_op.create_index('ix_user_feedbacks_id', ['id'], unique=False)
        batch_op.create_index('ix_feedback_org_status', ['organization_id', 'status'], unique=False)
        batch_op.create_index('ix_feedback_user_created', ['user_id', 'created_at'], unique=False)
        batch_op.create_index('ix_feedback_category', ['category'], unique=False)


def downgrade():
    with op.batch_alter_table('user_feedbacks', schema=None) as batch_op:
        batch_op.drop_index('ix_feedback_category')
        batch_op.drop_index('ix_feedback_user_created')
        batch_op.drop_index('ix_feedback_org_status')
        batch_op.drop_index('ix_user_feedbacks_id')
    op.drop_table('user_feedbacks')
