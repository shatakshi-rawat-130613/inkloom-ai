"""Add password_hash, brand_assets and document_extractions tables.

Revision ID: 002_add_auth_and_visual_assets
Revises: 001_initial_schema
Create Date: 2026-11-11 11:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002_add_auth_and_visual_assets'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    user_cols = [c['name'] for c in inspector.get_columns('users')]

    # 1. Add password_hash and is_active to users table if not present
    if 'password_hash' not in user_cols:
        op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    if 'is_active' not in user_cols:
        op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))

    tables = inspector.get_table_names()

    # 2. Create brand_assets table if not present
    if 'brand_assets' not in tables:
        op.create_table(
            'brand_assets',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('brand_id', sa.Uuid(), nullable=False),
            sa.Column('asset_type', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=True),
            sa.Column('content_type', sa.String(length=100), nullable=True),
            sa.Column('file_data', sa.Text(), nullable=True),
            sa.Column('asset_metadata', sa.JSON(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['brand_id'], ['brand_profiles.id'], ondelete='RESTRICT'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_brand_assets_brand_id'), 'brand_assets', ['brand_id'], unique=False)

    # 3. Create document_extractions table if not present
    if 'document_extractions' not in tables:
        op.create_table(
            'document_extractions',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('submission_id', sa.Uuid(), nullable=True),
            sa.Column('file_name', sa.String(length=255), nullable=False),
            sa.Column('file_type', sa.String(length=50), nullable=False),
            sa.Column('file_size_bytes', sa.Integer(), nullable=False),
            sa.Column('extraction_source', sa.String(length=50), nullable=False),
            sa.Column('extracted_text', sa.Text(), nullable=False),
            sa.Column('extraction_status', sa.String(length=50), nullable=False),
            sa.Column('extraction_metadata', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['submission_id'], ['content_submissions.id'], ondelete='RESTRICT'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_document_extractions_submission_id'), 'document_extractions', ['submission_id'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'document_extractions' in tables:
        op.drop_table('document_extractions')
    if 'brand_assets' in tables:
        op.drop_table('brand_assets')

    user_cols = [c['name'] for c in inspector.get_columns('users')]
    if 'is_active' in user_cols:
        op.drop_column('users', 'is_active')
    if 'password_hash' in user_cols:
        op.drop_column('users', 'password_hash')
