"""add_performance_and_composite_indexes

Revision ID: 5e9a2f1b4c3d
Revises: 4c8d1e2f3a4b
Create Date: 2026-11-05 16:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5e9a2f1b4c3d'
down_revision: Union[str, Sequence[str], None] = '4c8d1e2f3a4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES_TO_ADD = [
    ('integration_health_records', 'ix_integration_health_records_provider', ['provider'], False),
    ('integration_health_records', 'ix_integration_health_records_checked_at', ['checked_at'], False),
    ('ai_provider_configs', 'ix_ai_provider_configs_provider', ['provider'], False),
    ('ai_provider_configs', 'ix_ai_provider_configs_organization_id', ['organization_id'], False),
    ('audit_logs', 'ix_audit_logs_event_type', ['event_type'], False),
    ('audit_logs', 'ix_audit_logs_organization_id', ['organization_id'], False),
    ('audit_logs', 'ix_audit_logs_created_at', ['created_at'], False),
    ('background_jobs', 'ix_background_jobs_status', ['status'], False),
    ('background_jobs', 'ix_background_jobs_organization_id', ['organization_id'], False),
    ('background_jobs', 'ix_background_jobs_job_type', ['job_type'], False),
    ('background_jobs', 'ix_background_jobs_created_at', ['created_at'], False),
    ('editorial_style_profiles', 'ix_editorial_style_profiles_organization_id', ['organization_id'], False),
    ('editorial_style_profiles', 'ix_editorial_style_profiles_created_at', ['created_at'], False),
    ('editorial_versions', 'ix_editorial_versions_document_type', ['document_type'], False),
    ('editorial_versions', 'ix_editorial_versions_document_id', ['document_id'], False),
    ('editorial_versions', 'ix_editorial_versions_created_at', ['created_at'], False),
    ('integration_connections', 'ix_integration_connections_organization_id', ['organization_id'], False),
    ('integration_connections', 'ix_integration_connections_provider', ['provider'], False),
    ('notifications', 'ix_notifications_created_at', ['created_at'], False),
    ('notifications', 'ix_notifications_user_id', ['user_id'], False),
    ('notifications', 'ix_notifications_is_read', ['is_read'], False),
    ('organization_invitations', 'ix_organization_invitations_email', ['email'], False),
    ('organization_memberships', 'ix_organization_memberships_organization_id', ['organization_id'], False),
    ('organization_memberships', 'ix_organization_memberships_user_id', ['user_id'], False),
    ('provider_usage_records', 'ix_provider_usage_records_provider', ['provider'], False),
    ('provider_usage_records', 'ix_provider_usage_records_organization_id', ['organization_id'], False),
    ('provider_usage_records', 'ix_provider_usage_records_operation', ['operation'], False),
    ('provider_usage_records', 'ix_provider_usage_records_created_at', ['created_at'], False),
    ('research_projects', 'ix_research_projects_created_at', ['created_at'], False),
    ('research_projects', 'ix_research_projects_name', ['name'], False),
    ('research_projects', 'ix_research_projects_organization_id', ['organization_id'], False),
    ('research_projects', 'ix_research_projects_updated_at', ['updated_at'], False),
    ('usage_events', 'ix_usage_events_metric_name', ['metric_name'], False),
    ('usage_events', 'ix_usage_events_organization_id', ['organization_id'], False),
    ('usage_events', 'ix_usage_events_timestamp', ['timestamp'], False),
    ('user_activity_logs', 'ix_user_activity_logs_resource_id', ['resource_id'], False),
    ('user_activity_logs', 'ix_user_activity_logs_action', ['action'], False),
    ('user_activity_logs', 'ix_user_activity_logs_organization_id', ['organization_id'], False),
    ('user_activity_logs', 'ix_user_activity_logs_created_at', ['created_at'], False),
    ('user_activity_logs', 'ix_user_activity_logs_resource_type', ['resource_type'], False),
    ('research_briefs', 'ix_research_briefs_created_at', ['created_at'], False),
    ('research_briefs', 'ix_briefs_project_created', ['project_id', 'created_at'], False),
    ('research_briefs', 'ix_research_briefs_updated_at', ['updated_at'], False),
    ('research_contradictions', 'ix_research_contradictions_project_id', ['project_id'], False),
    ('research_contradictions', 'ix_research_contradictions_created_at', ['created_at'], False),
    ('research_trends', 'ix_research_trends_project_id', ['project_id'], False),
    ('research_trends', 'ix_research_trends_category', ['category'], False),
    ('research_trends', 'ix_research_trends_created_at', ['created_at'], False),
    ('sources', 'ix_sources_project_created', ['project_id', 'created_at'], False),
    ('sources', 'ix_sources_created_at', ['created_at'], False),
    ('writing_drafts', 'ix_writing_drafts_style_profile_id', ['style_profile_id'], False),
    ('writing_drafts', 'ix_writing_drafts_updated_at', ['updated_at'], False),
    ('writing_drafts', 'ix_drafts_project_created', ['project_id', 'created_at'], False),
    ('writing_drafts', 'ix_writing_drafts_created_at', ['created_at'], False),
    ('editorial_outputs', 'ix_editorial_project_created', ['project_id', 'created_at'], False),
    ('editorial_outputs', 'ix_editorial_outputs_created_at', ['created_at'], False),
    ('editorial_outputs', 'ix_editorial_outputs_updated_at', ['updated_at'], False),
    ('research_claims', 'ix_research_claims_created_at', ['created_at'], False),
    ('research_claims', 'ix_research_claims_evidence_classification', ['evidence_classification'], False),
    ('research_claims', 'ix_research_claims_project_id', ['project_id'], False),
    ('research_entities', 'ix_research_entities_normalized_name', ['normalized_name'], False),
    ('research_entities', 'ix_research_entities_name', ['name'], False),
    ('research_entities', 'ix_research_entities_project_id', ['project_id'], False),
    ('research_entities', 'ix_research_entities_entity_type', ['entity_type'], False),
    ('research_entities', 'ix_research_entities_created_at', ['created_at'], False),
    ('research_relationships', 'ix_research_relationships_target_entity_name', ['target_entity_name'], False),
    ('research_relationships', 'ix_research_relationships_project_id', ['project_id'], False),
    ('research_relationships', 'ix_research_relationships_relationship_type', ['relationship_type'], False),
    ('research_relationships', 'ix_research_relationships_created_at', ['created_at'], False),
    ('research_relationships', 'ix_research_relationships_source_entity_name', ['source_entity_name'], False),
    ('source_analyses', 'ix_source_analyses_created_at', ['created_at'], False),
    ('writing_suggestions', 'ix_suggestions_draft_status', ['draft_id', 'status'], False),
    ('writing_suggestions', 'ix_writing_suggestions_created_at', ['created_at'], False),
    ('research_evidence', 'ix_research_evidence_created_at', ['created_at'], False),
    ('research_evidence', 'ix_research_evidence_project_id', ['project_id'], False),
    ('research_evidence', 'ix_research_evidence_source_id', ['source_id'], False),
]

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. Enforce unique index on users.email
    if "users" in existing_tables:
        indexes = inspector.get_indexes("users")
        email_idx = next((i for i in indexes if i["name"] == "ix_users_email"), None)
        if email_idx and not email_idx.get("unique", False):
            with op.batch_alter_table("users", schema=None) as batch_op:
                batch_op.drop_index("ix_users_email")
                batch_op.create_index("ix_users_email", ["email"], unique=True)
        elif not email_idx:
            with op.batch_alter_table("users", schema=None) as batch_op:
                batch_op.create_index("ix_users_email", ["email"], unique=True)

    # 2. Add performance & composite indexes
    for table_name, index_name, columns, is_unique in INDEXES_TO_ADD:
        if table_name in existing_tables:
            existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
            if index_name not in existing_indexes:
                with op.batch_alter_table(table_name, schema=None) as batch_op:
                    batch_op.create_index(index_name, columns, unique=is_unique)

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Revert performance & composite indexes
    for table_name, index_name, _, _ in INDEXES_TO_ADD:
        if table_name in existing_tables:
            existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
            if index_name in existing_indexes:
                with op.batch_alter_table(table_name, schema=None) as batch_op:
                    batch_op.drop_index(index_name)

    # Revert users.email index to non-unique
    if "users" in existing_tables:
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.drop_index("ix_users_email")
            batch_op.create_index("ix_users_email", ["email"], unique=False)
