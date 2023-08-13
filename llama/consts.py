from .stocks.trader import LlamaTrader, MockLlamaTrader
from alpaca.data.models import BarSet
from .stocks.models import CustomBarSet

TRADER_TYPE = LlamaTrader | MockLlamaTrader

BARSET_TYPE = BarSet | CustomBarSet
