"""Phase 38 Add Product Intelligence Tables

Revision ID: cf7a8b9c0d1e
Revises: bf6a7b8c9d0e
Create Date: 2026-11-20 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf7a8b9c0d1e'
down_revision = 'bf6a7b8c9d0e'
branch_labels = None
depends_on = None


def upgrade():
    # 1. product_intelligence_insights
    op.create_table(
        'product_intelligence_insights',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('detected_pattern', sa.String(length=255), nullable=False),
        sa.Column('evidence_json', sa.JSON(), nullable=False),
        sa.Column('metrics_json', sa.JSON(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intel_insights_id', 'product_intelligence_insights', ['id'], unique=False)
    op.create_index('ix_intel_insight_org_cat', 'product_intelligence_insights', ['organization_id', 'category'], unique=False)
    op.create_index('ix_intel_insight_org_status', 'product_intelligence_insights', ['organization_id', 'status'], unique=False)
    op.create_index('ix_intel_insight_created', 'product_intelligence_insights', ['created_at'], unique=False)

    # 2. product_intelligence_recommendations
    op.create_table(
        'product_intelligence_recommendations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('insight_id', sa.String(length=36), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('proposed_action', sa.Text(), nullable=False),
        sa.Column('expected_benefit', sa.Text(), nullable=False),
        sa.Column('estimated_effort', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('risk_level', sa.String(length=20), nullable=False, server_default='LOW'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='READY'),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('implementation_notes', sa.Text(), nullable=True),
        sa.Column('is_automated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['insight_id'], ['product_intelligence_insights.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intel_recommendations_id', 'product_intelligence_recommendations', ['id'], unique=False)
    op.create_index('ix_intel_rec_org_priority', 'product_intelligence_recommendations', ['organization_id', 'priority'], unique=False)
    op.create_index('ix_intel_rec_org_status', 'product_intelligence_recommendations', ['organization_id', 'status'], unique=False)
    op.create_index('ix_intel_rec_category', 'product_intelligence_recommendations', ['category'], unique=False)
    op.create_index('ix_intel_rec_created', 'product_intelligence_recommendations', ['created_at'], unique=False)

    # 3. product_intelligence_actions
    op.create_table(
        'product_intelligence_actions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recommendation_id', sa.String(length=36), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('action_payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('executed_by', sa.String(length=255), nullable=True),
        sa.Column('audit_trail_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recommendation_id'], ['product_intelligence_recommendations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intel_actions_id', 'product_intelligence_actions', ['id'], unique=False)
    op.create_index('ix_intel_action_org_rec', 'product_intelligence_actions', ['organization_id', 'recommendation_id'], unique=False)
    op.create_index('ix_intel_action_status', 'product_intelligence_actions', ['status'], unique=False)

    # 4. recommendation_impact_evaluations
    op.create_table(
        'recommendation_impact_evaluations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recommendation_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('baseline_metrics_json', sa.JSON(), nullable=False),
        sa.Column('current_metrics_json', sa.JSON(), nullable=False),
        sa.Column('metric_delta_json', sa.JSON(), nullable=False),
        sa.Column('evaluation_status', sa.String(length=30), nullable=False, server_default='NOT_EVALUATED'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recommendation_id'], ['product_intelligence_recommendations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rec_impact_id', 'recommendation_impact_evaluations', ['id'], unique=False)
    op.create_index('ix_rec_eval_rec', 'recommendation_impact_evaluations', ['recommendation_id'], unique=False)
    op.create_index('ix_rec_eval_org_status', 'recommendation_impact_evaluations', ['organization_id', 'evaluation_status'], unique=False)

    # 5. recommendation_feedback
    op.create_table(
        'recommendation_feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recommendation_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recommendation_id'], ['product_intelligence_recommendations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rec_feedback_id', 'recommendation_feedback', ['id'], unique=False)
    op.create_index('ix_rec_feedback_rec_user', 'recommendation_feedback', ['recommendation_id', 'user_id'], unique=False)


def downgrade():
    op.drop_table('recommendation_feedback')
    op.drop_table('recommendation_impact_evaluations')
    op.drop_table('product_intelligence_actions')
    op.drop_table('product_intelligence_recommendations')
    op.drop_table('product_intelligence_insights')
