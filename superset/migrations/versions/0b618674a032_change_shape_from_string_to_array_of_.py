"""change shape from string to array of integers

Revision ID: 0b618674a032
Revises: e295bfa9c8ae
Create Date: 2018-08-08 06:48:25.276835

"""

# revision identifiers, used by Alembic.
from sqlalchemy.dialects import postgresql

revision = '0b618674a032'
down_revision = 'e295bfa9c8ae'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('lambdas', 'shape', type_=postgresql.ARRAY(sa.Integer), nullable=True,
                    postgresql_using='shape::integer[]')


def downgrade():
    #  we shouldn't go back to string representation
    op.alter_column('lambdas', 'shape', sa.String(length=128), nullable=True,
                    postgresql_using='shape::varchar[128]')
