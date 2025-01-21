"""Update SurfSpot model

Revision ID: b64424f183ae
Revises: b7f6e62cc15f
Create Date: 2025-01-22 01:34:43.784945

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b64424f183ae'
down_revision = 'b7f6e62cc15f'
branch_labels = None
depends_on = None

def upgrade():
    # Alter latitude column
    with op.batch_alter_table('surf_spot', schema=None) as batch_op:
        batch_op.alter_column(
            'latitude',
            existing_type=sa.VARCHAR(length=100),
            type_=sa.Float(),
            existing_nullable=False,
            postgresql_using='latitude::double precision'
        )
        batch_op.alter_column(
            'longitude',
            existing_type=sa.VARCHAR(length=100),
            type_=sa.Float(),
            existing_nullable=False,
            postgresql_using='longitude::double precision'
        )

def downgrade():
    # Revert latitude column
    with op.batch_alter_table('surf_spot', schema=None) as batch_op:
        batch_op.alter_column(
            'latitude',
            existing_type=sa.Float(),
            type_=sa.VARCHAR(length=100),
            existing_nullable=False,
            postgresql_using='latitude::text'
        )
        batch_op.alter_column(
            'longitude',
            existing_type=sa.Float(),
            type_=sa.VARCHAR(length=100),
            existing_nullable=False,
            postgresql_using='longitude::text'
        )
