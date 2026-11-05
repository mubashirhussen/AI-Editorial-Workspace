"""add_missing_fk_indexes

Revision ID: 4c8d1e2f3a4b
Revises: 3b7c9f1e8a2d
Create Date: 2026-11-05 16:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4c8d1e2f3a4b'
down_revision: Union[str, Sequence[str], None] = '3b7c9f1e8a2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES_TO_ADD = [
    ("audit_logs", "ix_audit_logs_user_id", ["user_id"]),
    ("editorial_versions", "ix_editorial_versions_created_by", ["created_by"]),
    ("editorial_versions", "ix_editorial_versions_organization_id", ["organization_id"]),
    ("email_verification_tokens", "ix_email_verification_tokens_user_id", ["user_id"]),
    ("notifications", "ix_notifications_organization_id", ["organization_id"]),
    ("organization_invitations", "ix_organization_invitations_invited_by_id", ["invited_by_id"]),
    ("organization_invitations", "ix_organization_invitations_organization_id", ["organization_id"]),
    ("password_reset_tokens", "ix_password_reset_tokens_user_id", ["user_id"]),
    ("provider_usage_records", "ix_provider_usage_records_user_id", ["user_id"]),
    ("research_claims", "ix_research_claims_source_id", ["source_id"]),
    ("research_entities", "ix_research_entities_source_id", ["source_id"]),
    ("research_evidence", "ix_research_evidence_claim_id", ["claim_id"]),
    ("research_relationships", "ix_research_relationships_source_id", ["source_id"]),
    ("user_activity_logs", "ix_user_activity_logs_user_id", ["user_id"]),
]

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name, index_name, columns in INDEXES_TO_ADD:
        if table_name in existing_tables:
            existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
            if index_name not in existing_indexes:
                with op.batch_alter_table(table_name, schema=None) as batch_op:
                    batch_op.create_index(index_name, columns, unique=False)

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name, index_name, _ in INDEXES_TO_ADD:
        if table_name in existing_tables:
            existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
            if index_name in existing_indexes:
                with op.batch_alter_table(table_name, schema=None) as batch_op:
                    batch_op.drop_index(index_name)
