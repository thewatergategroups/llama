from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import logging
from . import LlamaHistory, MockLlamaTrader, STRATEGIES, Strategy
from concurrent.futures import ProcessPoolExecutor, as_completed
from alpaca.data.models import Bar
from collections import defaultdict
import json


class BackTester:
    def __init__(self):
        self.processes = []

    def backtest_strats(
        self, history: LlamaHistory, symbols: list[str], days_to_test: int = 30
    ):
        minutes_to_test = (
            datetime.utcnow() - (datetime.utcnow() - timedelta(days=days_to_test))
        ).total_seconds() / 60

        start_time = datetime.utcnow() - timedelta(minutes=minutes_to_test)
        end_time = datetime.utcnow() - timedelta(minutes=15)

        logging.info("getting data...")
        data = history.get_stock_bars(
            symbols,
            time_frame=TimeFrame.Minute,
            start_time=start_time,
            end_time=end_time,
        )
        strat_data: dict[str, list[Strategy, MockLlamaTrader, list[Bar]]] = defaultdict(
            lambda: []
        )
        for strat in STRATEGIES:
            for symbol in symbols:
                strat_data[symbol].append(
                    (
                        strat.create(history, symbols, days=10, force=True),
                        MockLlamaTrader(),
                        data.data[symbol],
                    )
                )

        with ProcessPoolExecutor(max_workers=4) as xacuter:
            for symbol, strat_list in strat_data.items():
                for strat, trader, bars in strat_list:
                    self.processes.append(
                        xacuter.submit(
                            self.test_strat,
                            strategy=strat,
                            trader=trader,
                            bars=bars,
                        )
                    )
        overall = defaultdict(lambda: defaultdict(lambda: 0))
        for future in as_completed(self.processes):
            result: tuple[MockLlamaTrader, Strategy] = future.result()
            trader, strat = result
            for key, value in trader.aggregate().items():
                overall[type(strat).__name__][key] += value
        Strategy.store("overall_results", overall)

    @staticmethod
    def test_strat(
        strategy: Strategy,
        trader: MockLlamaTrader,
        bars: list[Bar],
    ):
        strat_name = type(strategy).__name__
        num_bars = len(bars)
        symbol = bars[0].symbol
        last_percent = 0
        for i in range(num_bars):
            percent_completed = int(i / num_bars * 100)
            if percent_completed > last_percent:
                last_percent = percent_completed
                logging.info(
                    "Progress of %s on %s: %s", strat_name, symbol, percent_completed
                )
            strategy.run(trader, bars[i])
        logging.info("Strategy: %s", strat_name)
        logging.info(trader.aggregate())
        return trader, strategy