"""
Base Conditions added to all strategies
"""

import logging

from alpaca.trading import OrderSide

from ...stocks.trader import Trader
from .consts import Condition, ConditionType
from ...stocks.extendend_bars import ExtendedBar


def quantity_sell(most_recent_bar: ExtendedBar, trader: Trader, min_quantity: int):
    """
    sell condition based on quantity
    """
    position = trader.get_position(most_recent_bar.symbol, force=True)
    qty_avail = int(position.qty_available)
    condition = qty_avail > min_quantity
    logging.info(qty_avail)
    return condition


def is_profitable_sell(
    most_recent_bar: ExtendedBar, trader: Trader, unrealized_pl: float
):
    """
    purchase condition based on buy prices.. PURELY a sell condition
    """

    position = trader.get_position(most_recent_bar.symbol, force=True)
    condition = float(position.unrealized_pl) > unrealized_pl
    logging.info(
        "is profitable sell condition on %s where unrealised profit/loss is %s condition response is %s",
        most_recent_bar.symbol,
        position.unrealized_pl,
        condition,
    )
    return condition


def stop_loss_sell(
    most_recent_bar: ExtendedBar, trader: Trader, unrealized_plpc: float
):
    """
    purchase condition based on buy prices.. PURELY a sell condition
    """

    position = trader.get_position(most_recent_bar.symbol, force=True)
    condition = float(position.unrealized_plpc) <= unrealized_plpc
    logging.info(
        "stop loss sell condition on %s where unrealised profit/loss percent is %s condition response is %s",  # pylint: disable=line-too-long
        most_recent_bar.symbol,
        position.unrealized_plpc,
        condition,
    )
    return condition


def quantity_buy(most_recent_bar: ExtendedBar, trader: Trader, max_quantity: int):
    """buy condition based on quantity"""
    position = trader.get_position(most_recent_bar.symbol, force=True)
    qty_avail = int(position.qty_available)
    condition = qty_avail < max_quantity
    return condition


def take_profit_buy(
    most_recent_bar: ExtendedBar,
    trader: Trader,
    unrealized_plpc: float,
):
    """
    purchase condition based on buy prices.. PURELY a sell condition
    """

    position = trader.get_position(most_recent_bar.symbol, force=True)
    condition = float(position.unrealized_plpc) >= unrealized_plpc
    logging.info(
        "take profit condition on %s where unrealised profit/loss percent is %s condition response is %s",  # pylint: disable=line-too-long
        most_recent_bar.symbol,
        position.unrealized_plpc,
        condition,
    )
    return condition


def get_base_conditions():
    """
    Return a list of all base conditions
    """
    return [
        Condition(
            name="max_quantity_allowed",
            func=quantity_buy,
            variables={"max_quantity": 5},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        Condition(
            name="take_profit",
            func=take_profit_buy,
            variables={"unrealized_plpc": 2},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.OR,
        ),
        Condition(
            name="min_quantity_allowed",
            func=quantity_sell,
            variables={"min_quantity": 0},
            active=True,
            side=OrderSide.SELL,
            type=ConditionType.AND,
        ),
        Condition(
            name="is_profitable",
            func=is_profitable_sell,
            variables={"unrealized_pl": 0},
            active=True,
            side=OrderSide.SELL,
            type=ConditionType.AND,
        ),
        Condition(
            name="stop_loss",
            func=stop_loss_sell,
            variables={"unrealized_plpc": -10},
            active=True,
            side=OrderSide.SELL,
            type=ConditionType.OR,
        ),
    ]
