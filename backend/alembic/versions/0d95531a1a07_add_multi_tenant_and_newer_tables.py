"""add_multi_tenant_and_newer_tables

Revision ID: 0d95531a1a07
Revises: fe217d474c9d
Create Date: 2026-11-01 23:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d95531a1a07'
down_revision: Union[str, Sequence[str], None] = 'fe217d474c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    # 2. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('organizations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_organizations_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_organizations_slug'), ['slug'], unique=True)

    # 3. Create organization_memberships table
    op.create_table(
        'organization_memberships',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='VIEWER'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('organization_memberships', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_organization_memberships_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_memberships_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_memberships_user_id'), ['user_id'], unique=False)
        batch_op.create_index('uq_org_user', ['organization_id', 'user_id'], unique=True)

    # 4. Create organization_invitations table
    op.create_table(
        'organization_invitations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='VIEWER'),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('invited_by_id', sa.String(length=36), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('organization_invitations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_organization_invitations_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_invitations_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_invitations_email'), ['email'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_invitations_token'), ['token'], unique=True)

    # 5. Create editorial_style_profiles table
    op.create_table(
        'editorial_style_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('publication_name', sa.String(length=255), nullable=False, server_default='This Week in AI'),
        sa.Column('tone', sa.String(length=100), nullable=False, server_default='Authoritative, analytical, objective'),
        sa.Column('target_audience', sa.String(length=255), nullable=False, server_default='Founders, builders, and operators'),
        sa.Column('max_sentence_length', sa.Integer(), nullable=False, server_default='25'),
        sa.Column('preferred_sentence_length', sa.Integer(), nullable=False, server_default='18'),
        sa.Column('max_paragraph_length', sa.Integer(), nullable=False, server_default='75'),
        sa.Column('target_flesch_score', sa.Float(), nullable=False, server_default='65.0'),
        sa.Column('preferred_terminology', sa.JSON(), nullable=False),
        sa.Column('words_to_avoid', sa.JSON(), nullable=False),
        sa.Column('headline_style', sa.String(length=100), nullable=False, server_default='Direct, analytical, hook-driven'),
        sa.Column('formatting_preferences', sa.JSON(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('editorial_style_profiles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_editorial_style_profiles_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_style_profiles_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_style_profiles_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_style_org_default', ['organization_id', 'is_default'], unique=False)

    # Seed default style profile
    import uuid
    from datetime import datetime, timezone
    style_profiles_table = sa.table(
        'editorial_style_profiles',
        sa.column('id', sa.String),
        sa.column('organization_id', sa.String),
        sa.column('name', sa.String),
        sa.column('publication_name', sa.String),
        sa.column('tone', sa.String),
        sa.column('target_audience', sa.String),
        sa.column('max_sentence_length', sa.Integer),
        sa.column('preferred_sentence_length', sa.Integer),
        sa.column('max_paragraph_length', sa.Integer),
        sa.column('target_flesch_score', sa.Float),
        sa.column('preferred_terminology', sa.JSON),
        sa.column('words_to_avoid', sa.JSON),
        sa.column('headline_style', sa.String),
        sa.column('formatting_preferences', sa.JSON),
        sa.column('is_default', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    op.bulk_insert(
        style_profiles_table,
        [{
            'id': 'default-style-profile-000000000000',
            'organization_id': None,
            'name': 'This Week in AI Standard',
            'publication_name': 'This Week in AI',
            'tone': 'Authoritative, analytical, objective',
            'target_audience': 'Founders, builders, and operators',
            'max_sentence_length': 25,
            'preferred_sentence_length': 18,
            'max_paragraph_length': 75,
            'target_flesch_score': 65.0,
            'preferred_terminology': {
                'AI chip': 'AI accelerator',
                'running the model': 'inference',
                'hallucination': 'model fabrication',
                'smart agent': 'autonomous agent',
                'super intelligence': 'AGI',
                'large model': 'frontier model'
            },
            'words_to_avoid': [
                'delve', 'game-changer', 'revolutionary', 'paradigm shift',
                'unprecedented', 'groundbreaking', 'unrivaled', 'pivotal'
            ],
            'headline_style': 'Direct, analytical, hook-driven',
            'formatting_preferences': {
                'bold_key_takeaways': True,
                'bullet_summaries': True,
                'citation_style': 'numbered_bracket'
            },
            'is_default': True,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }]
    )

    # 6. Alter research_projects table
    with op.batch_alter_table('research_projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organization_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('name', sa.String(length=255), nullable=True))
        batch_op.create_index(batch_op.f('ix_research_projects_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_projects_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_projects_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_projects_updated_at'), ['updated_at'], unique=False)
        batch_op.create_foreign_key('fk_research_projects_org', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # 7. Alter research_briefs table
    with op.batch_alter_table('research_briefs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('key_developments', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('strategic_implications', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('source_references', sa.JSON(), nullable=True))
        batch_op.create_index(batch_op.f('ix_research_briefs_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_briefs_updated_at'), ['updated_at'], unique=False)
        batch_op.create_index('ix_briefs_project_created', ['project_id', 'created_at'], unique=False)

    # 8. Alter sources table
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('original_url', sa.String(length=1024), nullable=True))
        batch_op.add_column(sa.Column('raw_content', sa.Text(), nullable=True))
        batch_op.alter_column('source_type',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)
        batch_op.create_index(batch_op.f('ix_sources_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_sources_project_created', ['project_id', 'created_at'], unique=False)

    # 9. Alter source_analyses table
    with op.batch_alter_table('source_analyses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('summary', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('key_points', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('reported_facts', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('founder_implications', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('uncertainties', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('newsletter_angles', sa.JSON(), nullable=True))
        batch_op.create_index(batch_op.f('ix_source_analyses_created_at'), ['created_at'], unique=False)

    # 10. Alter writing_drafts table
    with op.batch_alter_table('writing_drafts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('readability_score', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('style_profile_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('style_score', sa.Float(), nullable=True))
        batch_op.create_index(batch_op.f('ix_writing_drafts_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_writing_drafts_updated_at'), ['updated_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_writing_drafts_style_profile_id'), ['style_profile_id'], unique=False)
        batch_op.create_index('ix_drafts_project_created', ['project_id', 'created_at'], unique=False)
        batch_op.create_foreign_key('fk_writing_drafts_style', 'editorial_style_profiles', ['style_profile_id'], ['id'], ondelete='SET NULL')

    # 11. Alter writing_suggestions table
    with op.batch_alter_table('writing_suggestions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('suggested_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('start_offset', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('end_offset', sa.Integer(), nullable=True))
        batch_op.alter_column('suggested_rewrite',
               existing_type=sa.TEXT(),
               nullable=True)
        batch_op.create_index(batch_op.f('ix_writing_suggestions_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_suggestions_draft_status', ['draft_id', 'status'], unique=False)

    # 12. Alter editorial_outputs table
    with op.batch_alter_table('editorial_outputs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('original_content', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('ai_review_results', sa.JSON(), nullable=True))
        batch_op.create_index(batch_op.f('ix_editorial_outputs_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_outputs_updated_at'), ['updated_at'], unique=False)
        batch_op.create_index('ix_editorial_project_created', ['project_id', 'created_at'], unique=False)

    # 13. Create editorial_reviews table
    op.create_table(
        'editorial_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('editorial_id', sa.String(length=36), nullable=False),
        sa.Column('reviewer_name', sa.String(length=100), nullable=False),
        sa.Column('review_status', sa.String(length=50), nullable=False, server_default='HUMAN_REVIEW_PENDING'),
        sa.Column('overall_feedback', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['editorial_id'], ['editorial_outputs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('editorial_reviews', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_editorial_reviews_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_reviews_editorial_id'), ['editorial_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_reviews_review_status'), ['review_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_reviews_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_reviews_updated_at'), ['updated_at'], unique=False)
        batch_op.create_index('ix_editorial_review_created', ['editorial_id', 'created_at'], unique=False)

    # 14. Create editorial_comments table
    op.create_table(
        'editorial_comments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('review_id', sa.String(length=36), nullable=False),
        sa.Column('section_reference', sa.String(length=100), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('suggested_revision', sa.Text(), nullable=True),
        sa.Column('resolution_status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['review_id'], ['editorial_reviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('editorial_comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_editorial_comments_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_comments_review_id'), ['review_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_comments_resolution_status'), ['resolution_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_comments_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_editorial_comments_review', ['review_id', 'created_at'], unique=False)

    # 15. Create research_entities table
    op.create_table(
        'research_entities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=True),
        sa.Column('supporting_excerpt', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('extraction_method', sa.String(length=50), nullable=False, server_default='NER_RULES'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('research_entities', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_entities_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_entities_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_entities_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_entities_normalized_name'), ['normalized_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_entities_entity_type'), ['entity_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_entities_source_id'), ['source_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_entities_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_entities_project_type', ['project_id', 'entity_type'], unique=False)

    # 16. Create research_claims table
    op.create_table(
        'research_claims',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=True),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('supporting_excerpt', sa.Text(), nullable=False),
        sa.Column('evidence_classification', sa.String(length=50), nullable=False),
        sa.Column('entity_references', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('publication_date', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('research_claims', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_claims_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_claims_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_claims_source_id'), ['source_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_claims_evidence_classification'), ['evidence_classification'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_claims_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_claims_project_classification', ['project_id', 'evidence_classification'], unique=False)

    # 17. Create research_relationships table
    op.create_table(
        'research_relationships',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('source_entity_name', sa.String(length=255), nullable=False),
        sa.Column('target_entity_name', sa.String(length=255), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=True),
        sa.Column('supporting_evidence', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('research_relationships', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_relationships_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_relationships_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_relationships_source_entity_name'), ['source_entity_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_relationships_target_entity_name'), ['target_entity_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_relationships_relationship_type'), ['relationship_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_relationships_source_id'), ['source_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_relationships_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_relationships_project_type', ['project_id', 'relationship_type'], unique=False)

    # 18. Create research_contradictions table
    op.create_table(
        'research_contradictions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('claim_a_id', sa.String(length=36), nullable=True),
        sa.Column('claim_b_id', sa.String(length=36), nullable=True),
        sa.Column('source_a_id', sa.String(length=36), nullable=True),
        sa.Column('source_b_id', sa.String(length=36), nullable=True),
        sa.Column('claim_a_text', sa.Text(), nullable=False),
        sa.Column('claim_b_text', sa.Text(), nullable=False),
        sa.Column('disagreement_nature', sa.String(length=100), nullable=False),
        sa.Column('possible_explanations', sa.JSON(), nullable=False),
        sa.Column('unresolved_questions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('research_contradictions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_contradictions_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_contradictions_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_contradictions_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_contradictions_project', ['project_id'], unique=False)

    # 19. Create research_trends table
    op.create_table(
        'research_trends',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('theme', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('supporting_source_ids', sa.JSON(), nullable=False),
        sa.Column('evidence_summary', sa.Text(), nullable=False),
        sa.Column('is_prediction', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('research_trends', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_trends_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_trends_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_trends_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_trends_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_trends_project_cat', ['project_id', 'category'], unique=False)

    # 20. Create editorial_versions table
    op.create_table(
        'editorial_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('content_snapshot', sa.Text(), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('change_type', sa.String(length=50), nullable=False, server_default='MANUAL_EDIT'),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('editorial_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_editorial_versions_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_versions_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_versions_document_type'), ['document_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_versions_document_id'), ['document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_versions_created_by'), ['created_by'], unique=False)
        batch_op.create_index(batch_op.f('ix_editorial_versions_created_at'), ['created_at'], unique=False)
        batch_op.create_index('ix_editorial_versions_doc', ['document_type', 'document_id', 'version_number'], unique=False)
        batch_op.create_index('ix_editorial_versions_created', ['document_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('editorial_versions')
    op.drop_table('research_trends')
    op.drop_table('research_contradictions')
    op.drop_table('research_relationships')
    op.drop_table('research_claims')
    op.drop_table('research_entities')
    op.drop_table('editorial_comments')
    op.drop_table('editorial_reviews')
    op.drop_table('editorial_style_profiles')
    op.drop_table('organization_invitations')
    op.drop_table('organization_memberships')
    op.drop_table('organizations')
    op.drop_table('users')
