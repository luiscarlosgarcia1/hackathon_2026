"""initial schema

Revision ID: 86054fdc81e7
Revises:
Create Date: 2026-04-18 17:15:46.817174

"""
from alembic import op
import sqlalchemy as sa


revision = '86054fdc81e7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hearings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('agenda', sa.Text(), nullable=True),
        sa.Column('youtube_video_id', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('youtube_video_id', name='uq_hearings_youtube_video_id'),
        if_not_exists=True,
    )

    op.create_table(
        'hearing_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hearing_id', sa.Integer(), sa.ForeignKey('hearings.id'), nullable=False),
        sa.Column('issue_description', sa.Text(), nullable=True),
        sa.Column('stakeholders', sa.Text(), nullable=True),
        sa.Column('key_arguments', sa.Text(), nullable=True),
        sa.Column('community_impact', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hearing_id'),
        if_not_exists=True,
    )

    op.create_table(
        'government_decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hearing_id', sa.Integer(), sa.ForeignKey('hearings.id'), nullable=False),
        sa.Column('decision_text', sa.Text(), nullable=False),
        sa.Column('decision_date', sa.Date(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hearing_id'),
        if_not_exists=True,
    )

    op.create_table(
        'accountability_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hearing_id', sa.Integer(), sa.ForeignKey('hearings.id'), nullable=False),
        sa.Column('alignment', sa.String(length=20), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hearing_id'),
        if_not_exists=True,
    )

    op.create_table(
        'comment_clusters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hearing_id', sa.Integer(), sa.ForeignKey('hearings.id'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )

    op.create_table(
        'public_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hearing_id', sa.Integer(), sa.ForeignKey('hearings.id'), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('cluster_id', sa.Integer(), sa.ForeignKey('comment_clusters.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )


def downgrade():
    op.drop_table('public_comments')
    op.drop_table('comment_clusters')
    op.drop_table('accountability_summaries')
    op.drop_table('government_decisions')
    op.drop_table('hearing_summaries')
    op.drop_table('hearings')
