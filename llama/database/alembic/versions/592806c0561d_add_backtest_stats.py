"""add backtest stats

Revision ID: 592806c0561d
Revises: fbe531239951
Create Date: 2023-10-07 21:37:19.089733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '592806c0561d'
down_revision: Union[str, None] = 'fbe531239951'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('backtest_stats',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('backtest_id', sa.Integer(), nullable=False),
    sa.Column('positions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('orders', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('balance', sa.Float(), nullable=False),
    sa.Column('starting_balance', sa.Float(), nullable=False),
    sa.Column('buys', sa.Integer(), nullable=False),
    sa.Column('sells', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['backtest_id'], ['llama.backtests.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='llama'
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('backtest_stats', schema='llama')
    # ### end Alembic commands ###
