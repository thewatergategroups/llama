import logging
from datetime import datetime, timedelta

import requests
from alpaca.data.models import BarSet
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, select
from ..tools import custom_json_encoder
from ..settings import Settings
from .models import CustomBarSet
from ..database.models import Bars
from trekkers.config import get_sync_sessionmaker
from trekkers.statements import on_conflict_update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
import json
import pandas as pd
from datetime import datetime


class LlamaHistory:
    """Historic Trading data"""

    def __init__(
        self,
        client: StockHistoricalDataClient,
        news_url: str,
        pg_sessionmaker: sessionmaker[Session],
    ):
        self.client = client
        self.news_api_url = news_url
        self.pg_sessionmaker = pg_sessionmaker

    @classmethod
    def create(cls, settings: Settings):
        """Create a historical data client"""
        client = StockHistoricalDataClient(settings.api_key, settings.secret_key)
        pg_sessionmaker = get_sync_sessionmaker(settings.db_settings)
        return cls(client, settings.news_url, pg_sessionmaker)

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

    def insert_bars(self, bars: BarSet, time_frame: TimeFrame):
        dict_bars = CustomBarSet.from_barset(bars).to_dict(time_frame.value)
        stmt = insert(Bars).values(dict_bars)
        stmt = on_conflict_update(stmt, Bars)
        with self.pg_sessionmaker.begin() as session:
            session.execute(stmt)

    @staticmethod
    def _round_datetime(dt: datetime):
        pandas_timestamp = pd.Timestamp(dt)
        # Round to the nearest minute
        rounded_timestamp = pandas_timestamp.round("T")
        return rounded_timestamp.to_pydatetime()

    def identify_missing_bars(
        self,
        symbols: list[str],
        timeframe: TimeFrame,
        start_time: datetime,
        end_time: datetime,
    ):
        print("identifying bars")
        start_time = self._round_datetime(start_time)
        end_time = self._round_datetime(end_time)
        increment = {
            TimeFrameUnit.Minute: timedelta(minutes=1),
            TimeFrameUnit.Hour: timedelta(hours=1),
            TimeFrameUnit.Day: timedelta(days=1),
            TimeFrameUnit.Month: timedelta(weeks=4),
            TimeFrameUnit.Week: timedelta(weeks=1),
        }
        with self.pg_sessionmaker.begin() as session:
            generator = func.generate_series(
                start_time, end_time, increment[timeframe.unit]
            )
            series = select(generator.label("time")).subquery()
            match_query = (
                select(Bars.timestamp).where(
                    Bars.symbol.in_(symbols), Bars.timeframe == timeframe.value
                )
            ).subquery()
            query = select(series, match_query).select_from(
                series.outerjoin(match_query, series.c.time == match_query.c.timestamp)
            )
            response = session.execute(query).fetchall()

        output = []

        for row in response:
            val = row.tuple()
            output.append({"gen": val[0], "bar": val[1]})

        with open("./data/comparison.json", "w") as f:
            f.write(json.dumps(output, default=custom_json_encoder))

        print("done")

    def get_stock_bars(
        self,
        symbols: list[str] | None = None,
        time_frame: TimeFrame = TimeFrame.Hour,
        start_time: datetime = (datetime.utcnow() - timedelta(days=900)),
        end_time: datetime = (datetime.utcnow() - timedelta(minutes=15)),
    ):
        """get stock bars for stocks"""
        self.identify_missing_bars(symbols, time_frame, start_time, end_time)
        symbols = symbols if symbols is not None else ["TSLA"]  ## Spy is S&P500
        request_params = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=time_frame,
            start=start_time.isoformat(),
            end=end_time.isoformat(),
        )
        logging.debug("Getting historic data...")

        bars: BarSet = self.client.get_stock_bars(request_params)
        self.insert_bars(bars, time_frame)

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
