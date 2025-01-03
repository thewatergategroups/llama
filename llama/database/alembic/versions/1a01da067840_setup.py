"""setup

Revision ID: 1a01da067840
Revises: 
Create Date: 2023-08-31 21:22:52.941444

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1a01da067840'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bars',
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('timeframe', sa.String(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('open', sa.Float(), nullable=False),
    sa.Column('close', sa.Float(), nullable=False),
    sa.Column('high', sa.Float(), nullable=False),
    sa.Column('low', sa.Float(), nullable=False),
    sa.Column('trade_count', sa.Integer(), nullable=False),
    sa.Column('vwap', sa.Float(), nullable=False),
    sa.Column('volume', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('symbol', 'timeframe', 'timestamp'),
    schema='llama'
    )
    op.create_table('orders',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('client_order_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(), nullable=False),
    sa.Column('filled_at', sa.DateTime(), nullable=True),
    sa.Column('expired_at', sa.DateTime(), nullable=True),
    sa.Column('canceled_at', sa.DateTime(), nullable=True),
    sa.Column('failed_at', sa.DateTime(), nullable=True),
    sa.Column('replaced_at', sa.DateTime(), nullable=True),
    sa.Column('replaced_by', sa.Uuid(), nullable=True),
    sa.Column('replaces', sa.Uuid(), nullable=True),
    sa.Column('asset_id', sa.Uuid(), nullable=False),
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('asset_class', sa.String(), nullable=False),
    sa.Column('notional', sa.String(), nullable=True),
    sa.Column('qty', sa.String(), nullable=True),
    sa.Column('filled_qty', sa.String(), nullable=True),
    sa.Column('filled_avg_price', sa.String(), nullable=True),
    sa.Column('order_class', sa.String(), nullable=False),
    sa.Column('order_type', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('side', sa.String(), nullable=False),
    sa.Column('time_in_force', sa.String(), nullable=False),
    sa.Column('limit_price', sa.String(), nullable=True),
    sa.Column('stop_price', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('extended_hours', sa.Boolean(), nullable=False),
    sa.Column('legs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('trail_percent', sa.String(), nullable=True),
    sa.Column('trail_price', sa.String(), nullable=True),
    sa.Column('hwm', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='llama'
    )
    op.create_table('qoutes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('ask_exchange', sa.String(), nullable=False),
    sa.Column('ask_price', sa.Float(), nullable=False),
    sa.Column('ask_size', sa.Integer(), nullable=False),
    sa.Column('bid_exchange', sa.String(), nullable=False),
    sa.Column('bid_price', sa.Float(), nullable=False),
    sa.Column('bid_size', sa.Integer(), nullable=False),
    sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('tape', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='llama'
    )
    op.create_table('trades',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('exchange', sa.String(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=False),
    sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('tape', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='llama'
    )
    op.create_table('trade_updates',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('execution_id', sa.Uuid(), nullable=True),
    sa.Column('event', sa.String(), nullable=False),
    sa.Column('order_id', sa.Uuid(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('position_qty', sa.Float(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('qty', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['llama.orders.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='llama'
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('trade_updates', schema='llama')
    op.drop_table('trades', schema='llama')
    op.drop_table('qoutes', schema='llama')
    op.drop_table('orders', schema='llama')
    op.drop_table('bars', schema='llama')
    # ### end Alembic commands ###
