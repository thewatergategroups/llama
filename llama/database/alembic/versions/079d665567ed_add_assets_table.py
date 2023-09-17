"""add assets table

Revision ID: 079d665567ed
Revises: baa9159e387b
Create Date: 2023-09-09 09:40:17.875164

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '079d665567ed'
down_revision: Union[str, None] = 'baa9159e387b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tradable_assets',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('bot_is_trading', sa.Boolean(), nullable=False),
    sa.Column('asset_class', sa.String(), nullable=False),
    sa.Column('exchange', sa.String(), nullable=False),
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('tradable', sa.Boolean(), nullable=False),
    sa.Column('marginable', sa.Boolean(), nullable=False),
    sa.Column('shortable', sa.Boolean(), nullable=False),
    sa.Column('easy_to_borrow', sa.Boolean(), nullable=False),
    sa.Column('fractionable', sa.Boolean(), nullable=False),
    sa.Column('min_order_size', sa.Float(), nullable=True),
    sa.Column('min_trade_increment', sa.Float(), nullable=True),
    sa.Column('price_increment', sa.Float(), nullable=True),
    sa.Column('maintenance_margin_requirement', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='llama'
    )
    op.create_index(op.f('ix_llama_tradable_assets_symbol'), 'tradable_assets', ['symbol'], unique=False, schema='llama')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_llama_tradable_assets_symbol'), table_name='tradable_assets', schema='llama')
    op.drop_table('tradable_assets', schema='llama')
    # ### end Alembic commands ###