import logging
from datetime import datetime, timedelta
import time

import requests
from alpaca.data.models import BarSet
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, select
from ..settings import Settings
from .models import CustomBarSet
from ..database.models import Bars
from trekkers.config import get_sync_sessionmaker
from trekkers.statements import on_conflict_update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func, Values, column
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
        logging.info("inserting bars...")
        dict_bars = CustomBarSet.from_barset(bars).to_dict(time_frame.value)
        if not dict_bars:
            return
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
        symbol: str,
        timeframe: TimeFrame,
        start_time: datetime,
        end_time: datetime,
    ):
        logging.debug("identifying missing bars...")
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
                    Bars.symbol == symbol, Bars.timeframe == timeframe.value
                )
            ).subquery()
            query = (
                select(series)
                .select_from(
                    series.outerjoin(
                        match_query, series.c.time == match_query.c.timestamp
                    )
                )
                .where(match_query.c.timestamp.is_(None))
                .where(func.extract("isodow", series.c.time) < 6)
                .where(func.extract("hour", series.c.time).between(13, 19))
            )

            response: list[datetime] = session.execute(query).scalars().fetchall()

        max_gap_minutes = 30
        consecutive_groups = []
        response = sorted(list(set(response)))
        if not response:
            return consecutive_groups

        start_datetime = response[0]
        for i in range(len(response) - 1):
            diff = (response[i + 1] - response[i]).total_seconds() / 60
            if diff > max_gap_minutes:
                end_datetime = response[i]
                if (
                    end_datetime - start_datetime
                ).total_seconds() / 60 > max_gap_minutes:
                    consecutive_groups.append((start_datetime, end_datetime))

            start_datetime = response[i + 1]

        # If there's a consecutive sequence at the end, include it
        if start_datetime < response[-1]:
            end_datetime = response[-1]
            consecutive_groups.append((start_datetime, end_datetime))

        return consecutive_groups

    def get_stock_bars(
        self,
        symbols: list[str] | None = None,
        time_frame: TimeFrame = TimeFrame.Hour,
        start_time: datetime = (datetime.utcnow() - timedelta(days=900)),
        end_time: datetime = (datetime.utcnow() - timedelta(minutes=15)),
    ):
        """get stock bars for stocks"""
        logging.info("Getting stock bars...")
        symbols = symbols if symbols is not None else ["TSLA"]  ## Spy is S&P500
        for symbol in symbols:
            times = self.identify_missing_bars(symbol, time_frame, start_time, end_time)
            for starttime, endtime in times:
                logging.info(
                    "getting bars for %s between %s and %s",
                    symbol,
                    starttime,
                    endtime,
                )
                request_params = StockBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=time_frame,
                    start=starttime.isoformat(),
                    end=endtime.isoformat(),
                )
                bars: BarSet = self.client.get_stock_bars(request_params)
                self.insert_bars(bars, time_frame)
        with self.pg_sessionmaker.begin() as session:
            logging.info("fetching bars from postgres...")
            sym_table = Values(column("symbol"), name="symbol").data(
                [(symbol,) for symbol in symbols]
            )
            bars = (
                session.execute(
                    select(Bars)
                    .join(sym_table, Bars.symbol == sym_table.c.symbol)
                    .where(
                        Bars.symbol.in_(symbols),
                        Bars.timeframe == time_frame.value,
                        Bars.timestamp > start_time,
                        Bars.timestamp < end_time,
                    )
                )
                .scalars()
                .fetchall()
            )
            logging.info("converting to barset...")
            return CustomBarSet.from_postgres_bars(
                bars
            )  ## slowest bit - multiprocessing doesn't work

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
