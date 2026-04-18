"""add public_comments and comment_clusters

Revision ID: 86054fdc81e7
Revises:
Create Date: 2026-04-18 17:15:46.817174

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86054fdc81e7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('hearings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('youtube_video_id', sa.String(length=50), nullable=True))
        batch_op.create_unique_constraint('uq_hearings_youtube_video_id', ['youtube_video_id'])
        batch_op.drop_column('source_video_id')

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

    with op.batch_alter_table('hearings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_video_id', sa.String(length=64), nullable=True))
        batch_op.drop_constraint('uq_hearings_youtube_video_id', type_='unique')
        batch_op.drop_column('youtube_video_id')
