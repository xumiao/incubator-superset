"""adding signature to lambda

Revision ID: e140fc9266a0
Revises: 0b618674a032
Create Date: 2018-08-09 05:33:33.970660

"""

# revision identifiers, used by Alembic.
revision = 'e140fc9266a0'
down_revision = '0b618674a032'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lambdas', sa.Column('signature', sa.String(length=1024), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lambdas', 'signature')
    # ### end Alembic commands ###
