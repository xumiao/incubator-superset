"""add computational level to lambda

Revision ID: e527d9001345
Revises: e809b7eb2bcc
Create Date: 2018-12-13 19:52:56.453443

"""

# revision identifiers, used by Alembic.
revision = 'e527d9001345'
down_revision = 'e809b7eb2bcc'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    level = postgresql.ENUM('COMPUTABLE', 'QUERYABLE', 'LEARNABLE', name='level', create_type=False)
    level.create(op.get_bind())
    op.add_column('lambdas', sa.Column('level', level, nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lambdas', 'level')
    op.execute("DROP TYPE level;")
    # ### end Alembic commands ###