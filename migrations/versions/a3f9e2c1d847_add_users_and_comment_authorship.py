"""add users and comment authorship

Revision ID: a3f9e2c1d847
Revises: 86054fdc81e7
Create Date: 2026-04-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3f9e2c1d847'
down_revision = '86054fdc81e7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='citizen'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.add_column('public_comments', sa.Column('author_id', sa.Integer(), nullable=True))
    op.add_column('public_comments', sa.Column('author_name', sa.String(length=100), nullable=True))
    op.create_foreign_key(
        'fk_public_comments_author_id',
        'public_comments', 'users',
        ['author_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_public_comments_author_id', 'public_comments', ['author_id'])


def downgrade():
    op.drop_index('ix_public_comments_author_id', table_name='public_comments')
    op.drop_constraint('fk_public_comments_author_id', 'public_comments', type_='foreignkey')
    op.drop_column('public_comments', 'author_name')
    op.drop_column('public_comments', 'author_id')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
