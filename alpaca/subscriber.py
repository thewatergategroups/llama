"""
Alpaca API Subscriber to events on the stock exchange
"""
import logging

import alpaca_trade_api as tradeapi

from .consts import GLOBAL_SETTINGS


def subscribe():
    """Subscribe to data stream"""
    conn = tradeapi.stream2.StreamConn(
        GLOBAL_SETTINGS.alpaca_api_key, GLOBAL_SETTINGS.alpaca_secret_key,
        GLOBAL_SETTINGS.alpaca_url
    )
    logging.info("Streaming ['account_updates', 'trade_updates'] ")
    conn.run(['account_updates', 'trade_updates'])
    # @conn.on(r'^account_updates$')
    # async def on_account_updates(conn, channel, account):
    #     logging.info('%s', account)
    # @conn.on(r'^trade_updates$')
    # async def on_trade_updates(conn, channel, trade):
    #     logging.info('%s', trade)
