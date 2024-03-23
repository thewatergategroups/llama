"""add timestamp

Revision ID: 9c1bdc843852
Revises: 592806c0561d
Create Date: 2023-10-07 22:53:36.028330

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9c1bdc843852'
down_revision: Union[str, None] = '592806c0561d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('backtest_stats', sa.Column('timestamp', sa.DateTime(), nullable=False), schema='llama')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('backtest_stats', 'timestamp', schema='llama')
    # ### end Alembic commands ###
