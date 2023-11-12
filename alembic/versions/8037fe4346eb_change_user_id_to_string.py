"""change user id to string

Revision ID: 8037fe4346eb
Revises: d53f89a90559
Create Date: 2023-11-07 00:17:46.709185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8037fe4346eb'
down_revision: Union[str, None] = 'd53f89a90559'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'disputes', ['id'])
    op.alter_column('users', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=20),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'id',
               existing_type=sa.String(length=20),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.drop_constraint(None, 'disputes', type_='unique')
    # ### end Alembic commands ###