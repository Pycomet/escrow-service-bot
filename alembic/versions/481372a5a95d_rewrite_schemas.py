"""rewrite schemas

Revision ID: 481372a5a95d
Revises: 8037fe4346eb
Create Date: 2023-11-12 00:20:55.539019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '481372a5a95d'
down_revision: Union[str, None] = '8037fe4346eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chats',
    sa.Column('id', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=20), nullable=True),
    sa.Column('admin_id', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('agent')
    op.drop_table('affiliates')
    op.add_column('disputes', sa.Column('user_id', sa.String(length=20), nullable=True))
    op.add_column('disputes', sa.Column('is_resolved', sa.Boolean(), nullable=True))
    op.add_column('disputes', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.alter_column('disputes', 'trade_id',
               existing_type=sa.VARCHAR(length=16),
               type_=sa.String(length=20),
               existing_nullable=True)
    op.alter_column('disputes', 'complaint',
               existing_type=sa.VARCHAR(length=162),
               type_=sa.String(length=50),
               existing_nullable=True)
    op.drop_constraint('disputes_id_key', 'disputes', type_='unique')
    op.drop_constraint('disputes_trade_id_fkey', 'disputes', type_='foreignkey')
    op.create_foreign_key(None, 'disputes', 'users', ['user_id'], ['id'])
    op.create_foreign_key(None, 'disputes', 'trades', ['trade_id'], ['id'])
    op.drop_column('disputes', 'user')
    op.drop_column('disputes', 'created_on')
    op.add_column('trades', sa.Column('seller_id', sa.String(length=20), nullable=True))
    op.add_column('trades', sa.Column('buyer_id', sa.String(length=20), nullable=True))
    op.add_column('trades', sa.Column('invoice_id', sa.String(length=50), nullable=True))
    op.add_column('trades', sa.Column('is_active', sa.Boolean(), nullable=True))
    op.add_column('trades', sa.Column('is_paid', sa.Boolean(), nullable=True))
    op.add_column('trades', sa.Column('chat_id', sa.String(length=20), nullable=True))
    op.alter_column('trades', 'id',
               existing_type=sa.VARCHAR(length=16),
               type_=sa.String(length=20),
               existing_nullable=False)
    op.alter_column('trades', 'currency',
               existing_type=sa.VARCHAR(length=32),
               type_=sa.String(length=20),
               existing_nullable=True)
    op.alter_column('trades', 'created_at',
               existing_type=sa.VARCHAR(length=32),
               type_=sa.DateTime(),
               existing_nullable=True)
    op.alter_column('trades', 'updated_at',
               existing_type=sa.VARCHAR(length=32),
               type_=sa.DateTime(),
               existing_nullable=True)
    op.create_foreign_key(None, 'trades', 'users', ['seller_id'], ['id'])
    op.create_foreign_key(None, 'trades', 'users', ['buyer_id'], ['id'])
    op.create_foreign_key(None, 'trades', 'chats', ['chat_id'], ['id'])
    op.drop_column('trades', 'coin')
    op.drop_column('trades', 'agent_id')
    op.drop_column('trades', 'seller')
    op.drop_column('trades', 'is_open')
    op.drop_column('trades', 'wallet')
    op.drop_column('trades', 'address')
    op.drop_column('trades', 'payment_status')
    op.drop_column('trades', 'buyer')
    op.drop_column('trades', 'invoice')
    op.add_column('users', sa.Column('name', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'name')
    op.add_column('trades', sa.Column('invoice', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('trades', sa.Column('buyer', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('trades', sa.Column('payment_status', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('trades', sa.Column('address', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('trades', sa.Column('wallet', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('trades', sa.Column('is_open', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('trades', sa.Column('seller', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('trades', sa.Column('agent_id', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('trades', sa.Column('coin', sa.VARCHAR(length=32), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'trades', type_='foreignkey')
    op.drop_constraint(None, 'trades', type_='foreignkey')
    op.drop_constraint(None, 'trades', type_='foreignkey')
    op.alter_column('trades', 'updated_at',
               existing_type=sa.DateTime(),
               type_=sa.VARCHAR(length=32),
               existing_nullable=True)
    op.alter_column('trades', 'created_at',
               existing_type=sa.DateTime(),
               type_=sa.VARCHAR(length=32),
               existing_nullable=True)
    op.alter_column('trades', 'currency',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=32),
               existing_nullable=True)
    op.alter_column('trades', 'id',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=16),
               existing_nullable=False)
    op.drop_column('trades', 'chat_id')
    op.drop_column('trades', 'is_paid')
    op.drop_column('trades', 'is_active')
    op.drop_column('trades', 'invoice_id')
    op.drop_column('trades', 'buyer_id')
    op.drop_column('trades', 'seller_id')
    op.add_column('disputes', sa.Column('created_on', sa.VARCHAR(length=32), autoincrement=False, nullable=True))
    op.add_column('disputes', sa.Column('user', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'disputes', type_='foreignkey')
    op.drop_constraint(None, 'disputes', type_='foreignkey')
    op.create_foreign_key('disputes_trade_id_fkey', 'disputes', 'trades', ['trade_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint('disputes_id_key', 'disputes', ['id'])
    op.alter_column('disputes', 'complaint',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=162),
               existing_nullable=True)
    op.alter_column('disputes', 'trade_id',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=16),
               existing_nullable=True)
    op.drop_column('disputes', 'created_at')
    op.drop_column('disputes', 'is_resolved')
    op.drop_column('disputes', 'user_id')
    op.drop_table('chats')
    op.drop_table('agent', cascade=True)
    op.drop_table('affiliates', cascade=True)
    # ### end Alembic commands ###
