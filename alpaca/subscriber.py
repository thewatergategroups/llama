import asyncio
import logging

from celery import Celery
import alpaca_trade_api as tradeapi
from alpaca_trade_api.common import URL
from alpaca_trade_api.rest import REST, TimeFrame

from main import ALPACA_URL,ALPACA_SECRET_KEY,ALPACA_API_KEY

app = Celery('tasks', broker='redis:redis')
app.config_from_object('celery_config')


app.task
def subscribe():
    conn = tradeapi.stream2.StreamConn(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_URL)
    logging.info("Streaming ['account_updates', 'trade_updates'] ")
    conn.run(['account_updates', 'trade_updates'])
    @conn.on(r'^account_updates$')
    
    async def on_account_updates(conn, channel, account):
        print('account', account)

    @conn.on(r'^trade_updates$')
    async def on_trade_updates(conn, channel, trade):
        print('trade', trade)
   
   
    