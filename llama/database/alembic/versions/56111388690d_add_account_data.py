"""add account data

Revision ID: 56111388690d
Revises: 9c1bdc843852
Create Date: 2023-10-08 18:57:07.559655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56111388690d'
down_revision: Union[str, None] = '9c1bdc843852'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('account',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('account_number', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('ACCOUNT_CLOSED', 'ACCOUNT_UPDATED', 'ACTION_REQUIRED', 'ACTIVE', 'AML_REVIEW', 'APPROVAL_PENDING', 'APPROVED', 'DISABLED', 'DISABLE_PENDING', 'EDITED', 'INACTIVE', 'KYC_SUBMITTED', 'LIMITED', 'ONBOARDING', 'PAPER_ONLY', 'REAPPROVAL_PENDING', 'REJECTED', 'RESUBMITTED', 'SIGNED_UP', 'SUBMISSION_FAILED', 'SUBMITTED', name='accountstatus'), nullable=False),
    sa.Column('crypto_status', sa.Enum('ACCOUNT_CLOSED', 'ACCOUNT_UPDATED', 'ACTION_REQUIRED', 'ACTIVE', 'AML_REVIEW', 'APPROVAL_PENDING', 'APPROVED', 'DISABLED', 'DISABLE_PENDING', 'EDITED', 'INACTIVE', 'KYC_SUBMITTED', 'LIMITED', 'ONBOARDING', 'PAPER_ONLY', 'REAPPROVAL_PENDING', 'REJECTED', 'RESUBMITTED', 'SIGNED_UP', 'SUBMISSION_FAILED', 'SUBMITTED', name='accountstatus'), nullable=True),
    sa.Column('currency', sa.String(), nullable=True),
    sa.Column('buying_power', sa.String(), nullable=True),
    sa.Column('regt_buying_power', sa.String(), nullable=True),
    sa.Column('daytrading_buying_power', sa.String(), nullable=True),
    sa.Column('non_marginable_buying_power', sa.String(), nullable=True),
    sa.Column('cash', sa.String(), nullable=True),
    sa.Column('accrued_fees', sa.String(), nullable=True),
    sa.Column('pending_transfer_out', sa.String(), nullable=True),
    sa.Column('pending_transfer_in', sa.String(), nullable=True),
    sa.Column('portfolio_value', sa.String(), nullable=True),
    sa.Column('pattern_day_trader', sa.Boolean(), nullable=True),
    sa.Column('trading_blocked', sa.Boolean(), nullable=True),
    sa.Column('transfers_blocked', sa.Boolean(), nullable=True),
    sa.Column('account_blocked', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('trade_suspended_by_user', sa.Boolean(), nullable=True),
    sa.Column('multiplier', sa.String(), nullable=True),
    sa.Column('shorting_enabled', sa.Boolean(), nullable=True),
    sa.Column('equity', sa.String(), nullable=True),
    sa.Column('last_equity', sa.String(), nullable=True),
    sa.Column('long_market_value', sa.String(), nullable=True),
    sa.Column('short_market_value', sa.String(), nullable=True),
    sa.Column('initial_margin', sa.String(), nullable=True),
    sa.Column('maintenance_margin', sa.String(), nullable=True),
    sa.Column('last_maintenance_margin', sa.String(), nullable=True),
    sa.Column('sma', sa.String(), nullable=True),
    sa.Column('daytrade_count', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='llama'
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('account', schema='llama')
    # ### end Alembic commands ###