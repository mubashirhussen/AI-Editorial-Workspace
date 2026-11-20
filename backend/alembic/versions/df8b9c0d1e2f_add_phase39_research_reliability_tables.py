"""Phase 39 Add AI Research Reliability & Citation Verification Tables

Revision ID: df8b9c0d1e2f
Revises: cf7a8b9c0d1e
Create Date: 2026-11-20 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df8b9c0d1e2f'
down_revision = 'cf7a8b9c0d1e'
branch_labels = None
depends_on = None


def upgrade():
    # 1. source_credibility_assessments
    op.create_table(
        'source_credibility_assessments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('credibility_tier', sa.String(length=50), nullable=False, server_default='UNKNOWN'),
        sa.Column('publisher_type', sa.String(length=100), nullable=True),
        sa.Column('publisher_name', sa.String(length=255), nullable=True),
        sa.Column('author_name', sa.String(length=255), nullable=True),
        sa.Column('publication_date', sa.String(length=100), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('freshness_status', sa.String(length=50), nullable=False, server_default='CURRENT'),
        sa.Column('freshness_criteria', sa.Text(), nullable=True),
        sa.Column('accessibility_status', sa.String(length=50), nullable=False, server_default='ACCESSIBLE'),
        sa.Column('is_primary_source', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('methodological_transparency', sa.String(length=50), nullable=False, server_default='STANDARD'),
        sa.Column('criteria_breakdown_json', sa.JSON(), nullable=False),
        sa.Column('limitations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id')
    )
    op.create_index('ix_credibility_assessments_id', 'source_credibility_assessments', ['id'], unique=False)
    op.create_index('ix_credibility_source_proj', 'source_credibility_assessments', ['source_id', 'project_id'], unique=False)
    op.create_index('ix_credibility_tier', 'source_credibility_assessments', ['credibility_tier'], unique=False)

    # 2. citation_validations
    op.create_table(
        'citation_validations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('brief_id', sa.String(length=36), nullable=True),
        sa.Column('source_id', sa.String(length=36), nullable=True),
        sa.Column('claim_id', sa.String(length=36), nullable=True),
        sa.Column('citation_text', sa.Text(), nullable=False),
        sa.Column('citation_url', sa.String(length=1024), nullable=True),
        sa.Column('citation_number', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='UNVERIFIED'),
        sa.Column('validation_details_json', sa.JSON(), nullable=False),
        sa.Column('is_fabricated', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['brief_id'], ['research_briefs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['claim_id'], ['research_claims.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_citation_validations_id', 'citation_validations', ['id'], unique=False)
    op.create_index('ix_citation_proj_status', 'citation_validations', ['project_id', 'status'], unique=False)
    op.create_index('ix_citation_brief', 'citation_validations', ['brief_id'], unique=False)
    op.create_index('ix_citation_source', 'citation_validations', ['source_id'], unique=False)

    # 3. research_quality_reports
    op.create_table(
        'research_quality_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('brief_id', sa.String(length=36), nullable=True),
        sa.Column('total_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('claims_requiring_evidence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('supported_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('partially_supported_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unsupported_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('contradicted_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unverified_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('not_applicable_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('evidence_coverage_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('citation_health_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('source_diversity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('overall_quality_grade', sa.String(length=10), nullable=False, server_default='B'),
        sa.Column('source_quality_summary_json', sa.JSON(), nullable=False),
        sa.Column('corroboration_summary_json', sa.JSON(), nullable=False),
        sa.Column('contradictions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('limitations_summary', sa.Text(), nullable=True),
        sa.Column('audit_findings_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['brief_id'], ['research_briefs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_research_quality_reports_id', 'research_quality_reports', ['id'], unique=False)
    op.create_index('ix_quality_report_proj_brief', 'research_quality_reports', ['project_id', 'brief_id'], unique=False)

    # 4. research_revisions
    op.create_table(
        'research_revisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('brief_id', sa.String(length=36), nullable=False),
        sa.Column('section_key', sa.String(length=100), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('regenerated_text', sa.Text(), nullable=False),
        sa.Column('diff_summary', sa.Text(), nullable=True),
        sa.Column('supporting_evidence_ids_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['brief_id'], ['research_briefs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_research_revisions_id', 'research_revisions', ['id'], unique=False)
    op.create_index('ix_revisions_brief_section', 'research_revisions', ['brief_id', 'section_key'], unique=False)


def downgrade():
    op.drop_table('research_revisions')
    op.drop_table('research_quality_reports')
    op.drop_table('citation_validations')
    op.drop_table('source_credibility_assessments')
