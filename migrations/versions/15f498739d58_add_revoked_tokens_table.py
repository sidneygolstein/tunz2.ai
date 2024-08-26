"""Add revoked tokens table

Revision ID: 15f498739d58
Revises: 9ebcbb0ac61c
Create Date: 2024-08-24 13:48:55.915134

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15f498739d58'
down_revision = '9ebcbb0ac61c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('revoked_token',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('jti', sa.String(length=120), nullable=False),
    sa.Column('revoked_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('jti')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('revoked_token')
    # ### end Alembic commands ###