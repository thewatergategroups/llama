import logging
from datetime import datetime, timedelta

import requests
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame

from ..settings import Settings


class LlamaHistory:
    """Historic Trading data"""

    def __init__(self, client: StockHistoricalDataClient, news_url: str):
        self.client = client
        self.news_api_url = news_url

    @classmethod
    def create(cls, settings: Settings):
        """Create a historical data client"""
        client = StockHistoricalDataClient(settings.api_key, settings.secret_key)
        return cls(client, settings.news_url)

    def get_news(
        self,
        start_date: datetime = (datetime.utcnow() - timedelta(days=1)),
        end_date: datetime = datetime.utcnow(),
        symbols: list[str] | None = None,
    ):
        """Get stock news"""
        symbols = symbols if symbols is not None else ["SPY"]  ## Spy is S&P500
        headers = {
            "content-type": "application/json",
            "Apca-Api-Key-Id": self.client._api_key,  # type: ignore
            "Apca-Api-Secret-Key": self.client._secret_key,  # type: ignore
        }
        params = {
            "start": start_date.date(),
            "end": end_date.date(),
            "symbols": symbols,
        }
        response = requests.get(
            self.news_api_url,
            headers=headers,
            params=params,  # type: ignore
            timeout=20,
        )
        return response.json()

    def get_stock_bars(
        self,
        symbols: list[str] | None = None,
        time_frame: TimeFrame = TimeFrame.Hour,
        start_time: datetime = (datetime.utcnow() - timedelta(days=900)),
        end_time: datetime = (datetime.utcnow() - timedelta(minutes=15)),
    ):
        """get stock bars for stocks"""
        symbols = symbols if symbols is not None else ["TSLA"]  ## Spy is S&P500
        request_params = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=time_frame,
            start=start_time.isoformat(),
            end=end_time.isoformat(),
        )
        logging.debug("Getting historic data...")

        bars = self.client.get_stock_bars(request_params)
        return bars

    def get_latest_ask_price(self, symbols: list[str] | None = None):
        """get latest stock price"""
        symbols = symbols if symbols is not None else ["SPY"]
        multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=symbols)
        latest_multisymbol_quotes = self.client.get_stock_latest_quote(
            multisymbol_request_params
        )
        return {
            symbol: latest_multisymbol_quotes[symbol].ask_price for symbol in symbols
        }
