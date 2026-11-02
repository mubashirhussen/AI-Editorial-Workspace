"""phase4_database_architecture

Revision ID: 3b7c9f1e8a2d
Revises: 0d95531a1a07
Create Date: 2026-11-02 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b7c9f1e8a2d'
down_revision: Union[str, Sequence[str], None] = '0d95531a1a07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # =========================================================================
    # 1. ALTER EXISTING TABLES (COLUMNS & CONSTRAINTS)
    # =========================================================================
    if 'users' in existing_tables:
        existing_cols = {c['name'] for c in inspector.get_columns('users')}
        with op.batch_alter_table('users', schema=None) as batch_op:
            if 'is_verified' not in existing_cols:
                batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('1')))
            if 'deleted_at' not in existing_cols:
                batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    if 'research_projects' in existing_tables:
        existing_cols = {c['name'] for c in inspector.get_columns('research_projects')}
        with op.batch_alter_table('research_projects', schema=None) as batch_op:
            if 'deleted_at' not in existing_cols:
                batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
                batch_op.create_index('ix_research_projects_deleted_at', ['deleted_at'], unique=False)

    if 'sources' in existing_tables:
        existing_cols = {c['name'] for c in inspector.get_columns('sources')}
        with op.batch_alter_table('sources', schema=None) as batch_op:
            if 'deleted_at' not in existing_cols:
                batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
                batch_op.create_index('ix_sources_deleted_at', ['deleted_at'], unique=False)

    if 'writing_drafts' in existing_tables:
        existing_cols = {c['name'] for c in inspector.get_columns('writing_drafts')}
        with op.batch_alter_table('writing_drafts', schema=None) as batch_op:
            if 'author_id' not in existing_cols:
                batch_op.add_column(sa.Column('author_id', sa.String(length=36), nullable=True))
                batch_op.create_foreign_key('fk_writing_drafts_author_id', 'users', ['author_id'], ['id'], ondelete='SET NULL')
                batch_op.create_index('ix_writing_drafts_author_id', ['author_id'], unique=False)
            if 'deleted_at' not in existing_cols:
                batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
                batch_op.create_index('ix_writing_drafts_deleted_at', ['deleted_at'], unique=False)

    # =========================================================================
    # 2. CREATE NEW TABLES (IF NOT ALREADY EXISTING)
    # =========================================================================

    # Table: user_sessions
    if 'user_sessions' not in existing_tables:
        op.create_table(
            'user_sessions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('token_hash', sa.String(length=255), nullable=False),
            sa.Column('ip_address', sa.String(length=50), nullable=True),
            sa.Column('user_agent', sa.String(length=255), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('user_sessions', schema=None) as batch_op:
            batch_op.create_index('ix_user_sessions_id', ['id'], unique=False)
            batch_op.create_index('ix_user_sessions_user_id', ['user_id'], unique=False)
            batch_op.create_index('ix_user_sessions_token_hash', ['token_hash'], unique=True)
            batch_op.create_index('ix_user_sessions_user_exp', ['user_id', 'expires_at'], unique=False)

    # Table: password_reset_tokens
    if 'password_reset_tokens' not in existing_tables:
        op.create_table(
            'password_reset_tokens',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('token_hash', sa.String(length=255), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_used', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('password_reset_tokens', schema=None) as batch_op:
            batch_op.create_index('ix_password_reset_tokens_id', ['id'], unique=False)
            batch_op.create_index('ix_password_reset_tokens_token_hash', ['token_hash'], unique=True)

    # Table: email_verification_tokens
    if 'email_verification_tokens' not in existing_tables:
        op.create_table(
            'email_verification_tokens',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('token_hash', sa.String(length=255), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_used', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('email_verification_tokens', schema=None) as batch_op:
            batch_op.create_index('ix_email_verification_tokens_id', ['id'], unique=False)
            batch_op.create_index('ix_email_verification_tokens_token_hash', ['token_hash'], unique=True)

    # Table: research_evidence
    if 'research_evidence' not in existing_tables:
        op.create_table(
            'research_evidence',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('project_id', sa.String(length=36), nullable=False),
            sa.Column('source_id', sa.String(length=36), nullable=False),
            sa.Column('claim_id', sa.String(length=36), nullable=True),
            sa.Column('excerpt', sa.Text(), nullable=False),
            sa.Column('fact_type', sa.String(length=50), nullable=False, server_default='DIRECT_FACT'),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='0.95'),
            sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['claim_id'], ['research_claims.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('research_evidence', schema=None) as batch_op:
            batch_op.create_index('ix_research_evidence_id', ['id'], unique=False)
            batch_op.create_index('ix_evidence_project_source', ['project_id', 'source_id'], unique=False)

    # Table: ai_provider_configs
    if 'ai_provider_configs' not in existing_tables:
        op.create_table(
            'ai_provider_configs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=True),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('model_name', sa.String(length=100), nullable=False),
            sa.Column('encrypted_api_key', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('config_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('ai_provider_configs', schema=None) as batch_op:
            batch_op.create_index('ix_ai_provider_configs_id', ['id'], unique=False)
            batch_op.create_index('ix_ai_provider_org', ['organization_id', 'provider'], unique=False)

    # Table: integration_connections
    if 'integration_connections' not in existing_tables:
        op.create_table(
            'integration_connections',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=True),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='connected'),
            sa.Column('masked_key', sa.String(length=100), nullable=True),
            sa.Column('encrypted_secret', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('integration_connections', schema=None) as batch_op:
            batch_op.create_index('ix_integration_connections_id', ['id'], unique=False)
            batch_op.create_index('ix_integration_org_provider', ['organization_id', 'provider'], unique=False)

    # Table: provider_usage_records
    if 'provider_usage_records' not in existing_tables:
        op.create_table(
            'provider_usage_records',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=True),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('operation', sa.String(length=100), nullable=False),
            sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('duration_ms', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='success'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('provider_usage_records', schema=None) as batch_op:
            batch_op.create_index('ix_provider_usage_records_id', ['id'], unique=False)
            batch_op.create_index('ix_usage_org_created', ['organization_id', 'created_at'], unique=False)

    # Table: integration_health_records
    if 'integration_health_records' not in existing_tables:
        op.create_table(
            'integration_health_records',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('response_time_ms', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('error_details', sa.Text(), nullable=True),
            sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('integration_health_records', schema=None) as batch_op:
            batch_op.create_index('ix_integration_health_records_id', ['id'], unique=False)
            batch_op.create_index('ix_integration_health_provider', ['provider'], unique=False)

    # Table: background_jobs
    if 'background_jobs' not in existing_tables:
        op.create_table(
            'background_jobs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=True),
            sa.Column('job_type', sa.String(length=100), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
            sa.Column('payload', sa.JSON(), nullable=False),
            sa.Column('result', sa.JSON(), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('background_jobs', schema=None) as batch_op:
            batch_op.create_index('ix_background_jobs_id', ['id'], unique=False)
            batch_op.create_index('ix_jobs_org_status', ['organization_id', 'status'], unique=False)

    # Table: user_activity_logs
    if 'user_activity_logs' not in existing_tables:
        op.create_table(
            'user_activity_logs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=True),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('resource_type', sa.String(length=100), nullable=False),
            sa.Column('resource_id', sa.String(length=36), nullable=True),
            sa.Column('details', sa.JSON(), nullable=False),
            sa.Column('ip_address', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('user_activity_logs', schema=None) as batch_op:
            batch_op.create_index('ix_user_activity_logs_id', ['id'], unique=False)
            batch_op.create_index('ix_activity_org_created', ['organization_id', 'created_at'], unique=False)

    # Table: audit_logs
    if 'audit_logs' not in existing_tables:
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=True),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('event_type', sa.String(length=100), nullable=False),
            sa.Column('actor_email', sa.String(length=255), nullable=True),
            sa.Column('ip_address', sa.String(length=50), nullable=True),
            sa.Column('user_agent', sa.String(length=255), nullable=True),
            sa.Column('changes_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('audit_logs', schema=None) as batch_op:
            batch_op.create_index('ix_audit_logs_id', ['id'], unique=False)
            batch_op.create_index('ix_audit_org_created', ['organization_id', 'created_at'], unique=False)

    # Table: notifications
    if 'notifications' not in existing_tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False, server_default='info'),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('link', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('notifications', schema=None) as batch_op:
            batch_op.create_index('ix_notifications_id', ['id'], unique=False)
            batch_op.create_index('ix_notif_user_read', ['user_id', 'is_read'], unique=False)

    # Table: usage_events
    if 'usage_events' not in existing_tables:
        op.create_table(
            'usage_events',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=True),
            sa.Column('metric_name', sa.String(length=100), nullable=False),
            sa.Column('metric_value', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('tags_json', sa.JSON(), nullable=False),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('usage_events', schema=None) as batch_op:
            batch_op.create_index('ix_usage_events_id', ['id'], unique=False)
            batch_op.create_index('ix_events_org_metric_time', ['organization_id', 'metric_name', 'timestamp'], unique=False)


def downgrade() -> None:
    tables_to_drop = [
        'usage_events',
        'notifications',
        'audit_logs',
        'user_activity_logs',
        'background_jobs',
        'integration_health_records',
        'provider_usage_records',
        'integration_connections',
        'ai_provider_configs',
        'research_evidence',
        'email_verification_tokens',
        'password_reset_tokens',
        'user_sessions',
    ]
    for table_name in tables_to_drop:
        op.drop_table(table_name)

    with op.batch_alter_table('writing_drafts', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('author_id')

    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')

    with op.batch_alter_table('research_projects', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('is_verified')
