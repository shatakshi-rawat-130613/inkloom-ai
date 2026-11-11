"""Initial schema baseline.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-11 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. organisations
    op.create_table(
        'organisations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=80), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # 2. users
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organisation_id', sa.Uuid(), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=True),
        sa.Column('role', sa.Enum('editor', 'reviewer', 'admin', name='user_role', native_enum=False, length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_organisation_id'), 'users', ['organisation_id'], unique=False)

    # 3. brand_profiles
    op.create_table(
        'brand_profiles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organisation_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=80), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('voice_summary', sa.Text(), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_brand_profiles_organisation_id'), 'brand_profiles', ['organisation_id'], unique=False)

    # 4. brand_guidelines
    op.create_table(
        'brand_guidelines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('brand_id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('rule_text', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('terminology', 'outcome_claim', 'factual_consistency', 'timeframe', 'tone', 'other', name='finding_category', native_enum=False, length=32), nullable=False),
        sa.Column('default_severity', sa.Enum('critical', 'high', 'medium', 'low', 'informational', name='severity', native_enum=False, length=32), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['brand_id'], ['brand_profiles.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('brand_id', 'code', name='uq_guideline_brand_code')
    )
    op.create_index(op.f('ix_brand_guidelines_brand_id'), 'brand_guidelines', ['brand_id'], unique=False)

    # 5. approved_facts
    op.create_table(
        'approved_facts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('brand_id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=300), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['brand_id'], ['brand_profiles.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('brand_id', 'code', name='uq_fact_brand_code')
    )
    op.create_index(op.f('ix_approved_facts_brand_id'), 'approved_facts', ['brand_id'], unique=False)

    # 6. approved_terms
    op.create_table(
        'approved_terms',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('brand_id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('preferred_term', sa.String(length=300), nullable=True),
        sa.Column('prohibited_term', sa.String(length=300), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('related_guideline_id', sa.Uuid(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['brand_id'], ['brand_profiles.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['related_guideline_id'], ['brand_guidelines.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('brand_id', 'code', name='uq_term_brand_code')
    )
    op.create_index(op.f('ix_approved_terms_brand_id'), 'approved_terms', ['brand_id'], unique=False)

    # 7. content_submissions
    op.create_table(
        'content_submissions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('brand_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content_type', sa.Enum('social_post', 'email', 'web_page', 'advertisement', 'product_description', 'press_release', 'other', name='content_type', native_enum=False, length=32), nullable=False),
        sa.Column('status', sa.Enum('draft', 'analyzed', 'in_review', 'approved', 'rejected', 'revisions_requested', name='submission_status', native_enum=False, length=32), nullable=False),
        sa.Column('current_version_number', sa.Integer(), nullable=False),
        sa.Column('author_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['brand_id'], ['brand_profiles.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_submissions_brand_updated', 'content_submissions', ['brand_id', 'updated_at'], unique=False)
    op.create_index(op.f('ix_content_submissions_status'), 'content_submissions', ['status'], unique=False)

    # 8. content_versions
    op.create_table(
        'content_versions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('submission_id', sa.Uuid(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('change_note', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['content_submissions.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', 'version_number', name='uq_version_submission_number')
    )
    op.create_index(op.f('ix_content_versions_submission_id'), 'content_versions', ['submission_id'], unique=False)

    # 9. analysis_runs
    op.create_table(
        'analysis_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('submission_id', sa.Uuid(), nullable=False),
        sa.Column('version_id', sa.Uuid(), nullable=False),
        sa.Column('overall_status', sa.Enum('compliant', 'needs_review', 'non_compliant', name='overall_status', native_enum=False, length=32), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('positive_observations', sa.JSON(), nullable=False),
        sa.Column('requires_human_review', sa.Boolean(), nullable=False),
        sa.Column('ai_status', sa.Enum('ok', 'unavailable', 'invalid_response', 'disabled', name='ai_status', native_enum=False, length=32), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('rule_engine_version', sa.String(length=20), nullable=False),
        sa.Column('knowledge_snapshot', sa.JSON(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['content_submissions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['version_id'], ['content_versions.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_runs_version_id'), 'analysis_runs', ['version_id'], unique=False)
    op.create_index('ix_runs_submission_created', 'analysis_runs', ['submission_id', 'created_at'], unique=False)

    # 10. compliance_issues
    op.create_table(
        'compliance_issues',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('analysis_run_id', sa.Uuid(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('source', sa.Enum('rule_engine', 'ai', name='finding_source', native_enum=False, length=32), nullable=False),
        sa.Column('category', sa.Enum('terminology', 'outcome_claim', 'factual_consistency', 'timeframe', 'tone', 'other', name='finding_category', native_enum=False, length=32), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', 'informational', name='severity', native_enum=False, length=32), nullable=False),
        sa.Column('finding_type', sa.Enum('confirmed_rule_violation', 'unsupported_claim', 'potential_issue', 'recommendation', name='finding_type', native_enum=False, length=32), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('start_offset', sa.Integer(), nullable=True),
        sa.Column('end_offset', sa.Integer(), nullable=True),
        sa.Column('guideline_id', sa.Uuid(), nullable=True),
        sa.Column('approved_fact_id', sa.Uuid(), nullable=True),
        sa.Column('approved_term_id', sa.Uuid(), nullable=True),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('suggestion', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reference_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['approved_fact_id'], ['approved_facts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['approved_term_id'], ['approved_terms.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['guideline_id'], ['brand_guidelines.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_issues_analysis_run_id'), 'compliance_issues', ['analysis_run_id'], unique=False)

    # 11. human_reviews
    op.create_table(
        'human_reviews',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('submission_id', sa.Uuid(), nullable=False),
        sa.Column('version_id', sa.Uuid(), nullable=False),
        sa.Column('analysis_run_id', sa.Uuid(), nullable=True),
        sa.Column('reviewer_id', sa.Uuid(), nullable=True),
        sa.Column('reviewer_name', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.Enum('approved', 'rejected', 'revisions_requested', name='review_decision', native_enum=False, length=32), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['submission_id'], ['content_submissions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['version_id'], ['content_versions.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reviews_submission_created', 'human_reviews', ['submission_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_human_reviews_version_id'), 'human_reviews', ['version_id'], unique=False)

    # 12. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('submission_id', sa.Uuid(), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('actor_name', sa.String(length=100), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['content_submissions.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_entity', 'audit_logs', ['entity_type', 'entity_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('human_reviews')
    op.drop_table('compliance_issues')
    op.drop_table('analysis_runs')
    op.drop_table('content_versions')
    op.drop_table('content_submissions')
    op.drop_table('approved_terms')
    op.drop_table('approved_facts')
    op.drop_table('brand_guidelines')
    op.drop_table('brand_profiles')
    op.drop_table('users')
    op.drop_table('organisations')
