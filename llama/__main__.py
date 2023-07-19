"""
Entrypoint to the application
"""
from pprint import pprint
from .stocks import LlamaHistory,LlamaTrader
from .consts import Settings


if __name__ == "__main__":
    settings = Settings()
    trader = LlamaTrader.create(settings)
    history = LlamaHistory.create(settings)

    pprint(history.get_stock_bars())
    pprint(history.get_latest_ask_price())
    # pprint(trader.get_all_assets())

