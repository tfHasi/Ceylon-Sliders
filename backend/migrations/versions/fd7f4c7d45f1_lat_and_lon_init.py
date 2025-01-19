"""lat and lon init.

Revision ID: fd7f4c7d45f1
Revises: 19c238dd7704
Create Date: 2025-01-20 01:20:58.601149

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd7f4c7d45f1'
down_revision = '19c238dd7704'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('surf_spot', schema=None) as batch_op:
        batch_op.add_column(sa.Column('latitude', sa.String(length=100), nullable=False))
        batch_op.add_column(sa.Column('longitude', sa.String(length=100), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('surf_spot', schema=None) as batch_op:
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')

    # ### end Alembic commands ###
