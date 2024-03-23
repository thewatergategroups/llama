"""add positions

Revision ID: 7a87f23076b7
Revises: 1a01da067840
Create Date: 2023-09-03 10:08:51.860904

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7a87f23076b7'
down_revision: Union[str, None] = '1a01da067840'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('positions',
    sa.Column('asset_id', sa.Uuid(), nullable=False),
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('exchange', sa.String(), nullable=False),
    sa.Column('asset_class', sa.String(), nullable=False),
    sa.Column('asset_marginable', sa.Boolean(), nullable=True),
    sa.Column('avg_entry_price', sa.String(), nullable=False),
    sa.Column('qty', sa.String(), nullable=False),
    sa.Column('side', sa.String(), nullable=False),
    sa.Column('market_value', sa.String(), nullable=False),
    sa.Column('cost_basis', sa.String(), nullable=False),
    sa.Column('unrealized_pl', sa.String(), nullable=False),
    sa.Column('unrealized_plpc', sa.String(), nullable=False),
    sa.Column('unrealized_intraday_pl', sa.String(), nullable=False),
    sa.Column('unrealized_intraday_plpc', sa.String(), nullable=False),
    sa.Column('current_price', sa.String(), nullable=False),
    sa.Column('lastday_price', sa.String(), nullable=False),
    sa.Column('change_today', sa.String(), nullable=False),
    sa.Column('swap_rate', sa.String(), nullable=True),
    sa.Column('avg_entry_swap_rate', sa.String(), nullable=True),
    sa.Column('usd', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('qty_available', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('symbol'),
    schema='llama'
    )
    op.create_index(op.f('ix_llama_positions_asset_id'), 'positions', ['asset_id'], unique=True, schema='llama')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_llama_positions_asset_id'), table_name='positions', schema='llama')
    op.drop_table('positions', schema='llama')
    # ### end Alembic commands ###
