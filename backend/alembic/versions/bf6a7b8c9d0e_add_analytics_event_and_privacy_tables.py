"""Phase 37 Add Analytics Event and Privacy Preference Tables

Revision ID: bf6a7b8c9d0e
Revises: ae5f6a7b8c9d
Create Date: 2026-11-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf6a7b8c9d0e'
down_revision = 'ae5f6a7b8c9d'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=True),
        sa.Column('event_name', sa.String(length=100), nullable=False),
        sa.Column('event_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('user_pseudonym', sa.String(length=64), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('workflow_type', sa.String(length=50), nullable=True),
        sa.Column('workflow_id', sa.String(length=64), nullable=True),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=False, server_default='backend'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='completed'),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('properties_json', sa.JSON(), nullable=False),
        sa.Column('dedup_hash', sa.String(length=64), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_events_id', 'analytics_events', ['id'], unique=False)
    op.create_index('ix_analytics_events_event_id', 'analytics_events', ['event_id'], unique=False)
    op.create_index('ix_analytics_events_event_name', 'analytics_events', ['event_name'], unique=False)
    op.create_index('ix_analytics_events_org_id', 'analytics_events', ['organization_id'], unique=False)
    op.create_index('ix_analytics_events_user_pseudonym', 'analytics_events', ['user_pseudonym'], unique=False)
    op.create_index('ix_analytics_events_project_id', 'analytics_events', ['project_id'], unique=False)
    op.create_index('ix_analytics_events_workflow_type', 'analytics_events', ['workflow_type'], unique=False)
    op.create_index('ix_analytics_events_workflow_id', 'analytics_events', ['workflow_id'], unique=False)
    op.create_index('ix_analytics_events_session_id', 'analytics_events', ['session_id'], unique=False)
    op.create_index('ix_analytics_events_occurred_at', 'analytics_events', ['occurred_at'], unique=False)
    op.create_index('ix_analytics_org_occurred', 'analytics_events', ['organization_id', 'occurred_at'], unique=False)
    op.create_index('ix_analytics_org_workflow', 'analytics_events', ['organization_id', 'workflow_type', 'status'], unique=False)
    op.create_index('ix_analytics_event_name_occurred', 'analytics_events', ['event_name', 'occurred_at'], unique=False)
    op.create_index('ix_analytics_dedup', 'analytics_events', ['dedup_hash'], unique=False)
    op.create_index('ix_analytics_pseudonym_time', 'analytics_events', ['user_pseudonym', 'occurred_at'], unique=False)

    # 2. Create analytics_privacy_preferences table
    op.create_table(
        'analytics_privacy_preferences',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('analytics_opt_out', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('do_not_track', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_analytics_privacy_preferences_id', 'analytics_privacy_preferences', ['id'], unique=False)
    op.create_index('ix_analytics_privacy_user', 'analytics_privacy_preferences', ['user_id'], unique=False)


def downgrade():
    op.drop_index('ix_analytics_privacy_user', table_name='analytics_privacy_preferences')
    op.drop_index('ix_analytics_privacy_preferences_id', table_name='analytics_privacy_preferences')
    op.drop_table('analytics_privacy_preferences')

    op.drop_index('ix_analytics_pseudonym_time', table_name='analytics_events')
    op.drop_index('ix_analytics_dedup', table_name='analytics_events')
    op.drop_index('ix_analytics_event_name_occurred', table_name='analytics_events')
    op.drop_index('ix_analytics_org_workflow', table_name='analytics_events')
    op.drop_index('ix_analytics_org_occurred', table_name='analytics_events')
    op.drop_index('ix_analytics_events_occurred_at', table_name='analytics_events')
    op.drop_index('ix_analytics_events_session_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_workflow_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_workflow_type', table_name='analytics_events')
    op.drop_index('ix_analytics_events_project_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_user_pseudonym', table_name='analytics_events')
    op.drop_index('ix_analytics_events_org_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_event_name', table_name='analytics_events')
    op.drop_index('ix_analytics_events_event_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_id', table_name='analytics_events')
    op.drop_table('analytics_events')
