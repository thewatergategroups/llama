from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import StockBarsRequest,StockLatestQuoteRequest
from datetime import datetime,timedelta
from ..consts import Settings
import requests

class LlamaHistory:
    def __init__(self,client:StockHistoricalDataClient):
        self.client = client
        self.news_api_url = "https://data.alpaca.markets/v1beta1/news"
    @classmethod
    def create(cls,settings:Settings):
        """Create a historical data client"""
        client = StockHistoricalDataClient(settings.api_key,settings.secret_key)
        return cls(client)

    def get_news(self,start_date:datetime = (datetime.utcnow() - timedelta(days=1)), end_date:datetime = datetime.utcnow(),symbols:list = ["TSLA"]):
        """Get stock news"""
        headers = {
            'content-type': 'application/json',
            'Apca-Api-Key-Id': self.client._api_key,  # type: ignore
            'Apca-Api-Secret-Key': self.client._secret_key # type: ignore
        }
        params = {"start":start_date.date(),"end":end_date.date(),"symbols":symbols}
        response = requests.get(self.news_api_url, headers=headers,params=params,timeout=20) # type: ignore
        return response.json()

    def get_stock_bars(self,symbols:list[str] = ["TSLA"],time_frame:TimeFrame = TimeFrame.Day,start_date:datetime = (datetime.utcnow() - timedelta(days=1))):
        """get stock bars for stocks"""
        request_params = StockBarsRequest(
                        symbol_or_symbols=symbols,
                        timeframe=time_frame,
                        start=start_date.isoformat()
                 )
        bars = self.client.get_stock_bars(request_params)
        return bars

    def get_latest_ask_price(self,symbols:list[str] = ["TSLA"]):
        """get latest stock price"""
        multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=symbols)
        latest_multisymbol_quotes = self.client.get_stock_latest_quote(multisymbol_request_params)
        return {symbol:latest_multisymbol_quotes[symbol].ask_price for symbol in symbols}

