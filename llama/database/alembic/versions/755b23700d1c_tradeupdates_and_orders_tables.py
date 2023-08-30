"""tradeupdates and orders tables

Revision ID: 755b23700d1c
Revises: a506959cf187
Create Date: 2023-08-30 18:18:03.813572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '755b23700d1c'
down_revision: Union[str, None] = 'a506959cf187'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('orders',
    sa.Column('id_', sa.Uuid(), nullable=False),
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
    sa.PrimaryKeyConstraint('id_'),
    schema='llama'
    )
    op.create_table('trade_updates',
    sa.Column('execution_id', sa.Uuid(), nullable=False),
    sa.Column('event', sa.String(), nullable=False),
    sa.Column('order_id', sa.Uuid(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('position_qty', sa.Float(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('qty', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['llama.orders.id_'], ),
    sa.PrimaryKeyConstraint('execution_id'),
    schema='llama'
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('trade_updates', schema='llama')
    op.drop_table('orders', schema='llama')
    # ### end Alembic commands ###
