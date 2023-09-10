import logging
from datetime import datetime, timedelta

import requests
from alpaca.data.models import BarSet
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from sqlalchemy import func, select
from ..settings import Settings
from .models import CustomBarSet
from ..database import Bars
from trekkers.statements import upsert
from trekkers.config import get_sync_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func, Values, column
import pandas as pd
from datetime import datetime

FRAME_PARAMS = {
    TimeFrameUnit.Minute: {
        "delta": timedelta(minutes=1),
        "allowed_delta": timedelta(minutes=60),
    },
    TimeFrameUnit.Hour: {
        "delta": timedelta(hours=1),
        "allowed_delta": timedelta(hours=1),
    },
    TimeFrameUnit.Day: {
        "delta": timedelta(hours=24),
        "allowed_delta": timedelta(hours=24),
    },
    TimeFrameUnit.Month: {
        "delta": timedelta(weeks=4),
        "allowed_delta": timedelta(weeks=4),
    },
    TimeFrameUnit.Week: {
        "delta": timedelta(weeks=1),
        "allowed_delta": timedelta(weeks=1),
    },
}


class History:
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
        next_page: str | None = None,
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
        if next_page is not None:
            params["page_token"] = next_page
        response = requests.get(
            self.news_api_url,
            headers=headers,
            params=params,  # type: ignore
            timeout=20,
        )
        return response.json()

    def insert_bars(self, bars: BarSet, time_frame: TimeFrame):
        logging.debug("inserting bars...")
        dict_bars = CustomBarSet.from_barset(bars).to_dict(time_frame.value)
        if not dict_bars:
            return
        upsert(self.pg_sessionmaker, dict_bars, Bars)

    @staticmethod
    def _round_datetime(dt: datetime, timeframe: TimeFrame):
        if timeframe.unit == TimeFrameUnit.Day:
            dt = dt.replace(hour=4, minute=0, second=0)
        if timeframe.unit == TimeFrameUnit.Minute:
            dt = dt.replace(hour=0, minute=0, second=0)

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
        """
        Currently geta all data we already have between start and end time,
        checks what data is missing during trading hours, and turns them into consecutive sequences of data that we need to fetch.
        DO NOT TOUCH
        """
        logging.debug("identifying missing bars...")
        start_time = self._round_datetime(start_time, timeframe)
        end_time = self._round_datetime(end_time, timeframe)

        delta = FRAME_PARAMS[timeframe.unit]["delta"]
        allowed_delta = FRAME_PARAMS[timeframe.unit]["allowed_delta"]

        with self.pg_sessionmaker.begin() as session:
            generator = func.generate_series(start_time, end_time, delta)
            series = select(generator.label("time")).subquery()
            match_query = (
                select(Bars.timestamp)
                .where(Bars.symbol == symbol, Bars.timeframe == timeframe.value)
                .subquery()
            )
            query = (
                select(series)
                .select_from(
                    series.outerjoin(
                        match_query, series.c.time == match_query.c.timestamp
                    )
                )
                .where(match_query.c.timestamp.is_(None))
            )
            if timeframe.unit in {TimeFrameUnit.Minute, TimeFrameUnit.Day}:
                query = query.where(func.extract("isodow", series.c.time) < 6)
            if timeframe.unit == TimeFrameUnit.Minute:
                query = query.where(func.extract("hour", series.c.time).between(13, 19))

            response: list[datetime] = session.execute(query).scalars().fetchall()

        consecutive_groups = []
        response = sorted(list(set(response)))

        if not response:
            return consecutive_groups

        start_datetime = response[0]
        for i in range(len(response) - 1):
            diff = response[i + 1] - response[i]

            if diff > delta:
                end_datetime = response[i]

                if (
                    start_datetime != end_datetime
                    and (end_datetime - start_datetime) > allowed_delta
                ):
                    consecutive_groups.append((start_datetime, end_datetime))
                start_datetime = response[i + 1]

        diff = response[-1] - start_datetime
        if diff > allowed_delta:
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
        logging.debug("Getting stock bars...")
        symbols = symbols if symbols is not None else ["AAPL"]  ## Spy is S&P500
        start_time = start_time.replace(hour=0, minute=0, second=0)
        for symbol in symbols:
            times = self.identify_missing_bars(symbol, time_frame, start_time, end_time)
            for starttime, endtime in times:
                logging.info(
                    "getting bars for %s between %s and %s with timeframe of %s",
                    symbol,
                    starttime,
                    endtime,
                    time_frame.value,
                )
                request_params = StockBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=time_frame,
                    start=starttime.isoformat(),
                    end=endtime.isoformat(),
                )
                bars: BarSet = self.client.get_stock_bars(request_params)
                # bars = self.fill_bars(bars, start_time, end_time)
                if bars.data:
                    self.insert_bars(bars, time_frame)
        with self.pg_sessionmaker.begin() as session:
            logging.debug("fetching bars from postgres...")
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
                        Bars.timestamp >= start_time,
                        Bars.timestamp <= end_time,
                    )
                )
                .scalars()
                .fetchall()
            )
            logging.debug("converting to barset...")
            return CustomBarSet.from_postgres_bars(
                bars
            )  ## slowest bit - multiprocessing doesn't work

    def get_latest_qoute(self, symbol: list[str] | None = None):
        """get latest stock price"""
        symbols = symbols if symbols is not None else ["SPY"]
        multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        latest_multisymbol_quotes = self.client.get_stock_latest_quote(
            multisymbol_request_params
        )
        return latest_multisymbol_quotes[symbol]
