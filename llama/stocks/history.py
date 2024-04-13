"""
History object to pull back data from alpaca's apis
"""

import logging
from datetime import datetime, timedelta

import pandas as pd
import requests
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestQuoteRequest,
    StockQuotesRequest,
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from sqlalchemy import Values, column, func, select
from trekkers.statements import upsert

from ..database import Bars, Qoutes
from ..settings import Settings, get_sync_sessionm
from .models import CustomBarSet
from .extendend_bars import ExtendedBarSet
from ..indicators.technical import Indicators

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
    ):
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
        next_page: str | None = None,
    ):
        """Get stock news"""
        symbols = symbols if symbols is not None else ["SPY"]  ## Spy is S&P500
        headers = {
            "content-type": "application/json",
            "Apca-Api-Key-Id": self.client._api_key,  # pylint: disable=protected-access
            "Apca-Api-Secret-Key": self.client._secret_key,  # pylint: disable=protected-access
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

    def insert_bars(self, bars: ExtendedBarSet | pd.DataFrame, time_frame: TimeFrame):
        """_summary_

        Args:
            bars (ExtendedBarSet): _description_
            time_frame (TimeFrame): _description_
        """
        logging.info("inserting bars...")
        # dict_bars = list[Dict]

        if isinstance(bars, pd.DataFrame):
            logging.info("Inserting bars as DataFrame")
            # TODO: Fix that up?! Should probably be .apply on each elem
            bars["timeframe"] = time_frame.value
            dict_bars = list(bars.T.to_dict().values())
            logging.info("Done converting")
        else:
            logging.info("Inserting from custom barset")
            dict_bars = CustomBarSet.from_barset(bars).to_dict(time_frame.value)
        if not dict_bars:
            return
        logging.info(dict_bars)
        logging.info("Attempting to upsert into db")
        upsert(get_sync_sessionm(), dict_bars, Bars)

    @staticmethod
    def _round_datetime(dt: datetime, timeframe: TimeFrame):
        if timeframe.unit == TimeFrameUnit.Day:
            if dt.hour < 4:
                dt = dt - timedelta(days=1)
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
        checks what data is missing during trading hours,
        and turns them into consecutive sequences of data that we need to fetch.
        DO NOT TOUCH
        """
        logging.debug("identifying missing bars...")
        start_time = self._round_datetime(start_time, timeframe)
        end_time = self._round_datetime(end_time, timeframe)

        delta = FRAME_PARAMS[timeframe.unit]["delta"]
        allowed_delta = FRAME_PARAMS[timeframe.unit]["allowed_delta"]

        with get_sync_sessionm().begin() as session:
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
                query = query.where(
                    func.extract(  # pylint: disable=not-callable
                        "isodow", series.c.time
                    )
                    < 6
                )
            if timeframe.unit == TimeFrameUnit.Minute:
                query = query.where(
                    func.extract(  # pylint: disable=not-callable
                        "hour", series.c.time
                    ).between(13, 19)
                )

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
                # bars: BarSet/ = self.client.get_stock_bars(request_params)
                bars: ExtendedBarSet = self.client.get_stock_bars(request_params)
                # cucstomBarset = Barset(custom)
                # bars = self.fill_bars(bars, start_time, end_time)
                #  create custom bars
                # insert them
                # here is technical
                bars_df: pd.DataFrame = bars.df
                # logging.info(bars_df)

                technical_indicators = Indicators()
                bars_df = technical_indicators.calculate_garman_klass_vol(df=bars_df)
                # logging.info("Finished calculating the GVK")
                # logging.info(bars_df)
                # logging.info(bars_df["garman_klass_vol"])

                # logging.info("Finished calculating the RSI")
                bars_df = technical_indicators.calculate_rsi_indicator(bars_df)
                # logging.info(bars_df["rsi"])
                # logging.info(bars_df)

                # bars_df = technical_indicators.calculate_bollinger_bands(
                #     bars_df, level=1
                # )
                # logging.info(bars_df["bb_low"])
                # logging.info(bars_df["bb_mid"])
                # logging.info(bars_df["bb_high"])
                # apply(calculate_macd)
                # TODO: Add ATR to tables
                # df['atr'] = df.groupby(level=1, group_keys=False).apply(compute_atr)
                # TODO: Add macdto tables
                # bars_df["macd"] = bars_df.groupby(level=1, group_keys=False)[
                #     "close"
                # ].apply(technical_indicators.calculate_macd)
                bars_df = technical_indicators.calculate_stochastic(
                    bars_df
                )  # k_period=1 ?
                # logging.info(bars_df["rsi"])
                # logging.info(bars_df["stochastic_osci"])

                bars_df = technical_indicators.calculate_smas(bars_df)
                # logging.info(bars_df)

                # extended_bars = bars_df.to_dict ??
                # bars.df = bars_df
                logging.info("Converted bars after technical")
                # if bars.data:
                self.insert_bars(bars_df, time_frame)
        with get_sync_sessionm().begin() as session:
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

    def get_latest_qoute(self, symbol: str | None = None):
        """get latest stock price"""
        multisymbol_request_params = StockLatestQuoteRequest(
            symbol_or_symbols=symbol,
        )
        latest_multisymbol_quotes = self.client.get_stock_latest_quote(
            multisymbol_request_params
        )
        return latest_multisymbol_quotes[symbol]

    def get_qoutes(
        self,
        symbol: str,
        start_time: datetime = (datetime.utcnow() - timedelta(days=900)),
        end_time: datetime = (datetime.utcnow() - timedelta(minutes=15)),
    ):
        """Get the existing qoutes for a symbol"""
        logging.info("getting qoutes...")
        with get_sync_sessionm().begin() as session:
            stmt = select(Qoutes.timestamp).where(
                Qoutes.timestamp >= start_time,
                Qoutes.timestamp <= end_time,
                Qoutes.symbol == symbol,
            )
            first = (
                session.execute(stmt.order_by(Qoutes.timestamp.asc())).scalars().first()
            )
            last = (
                session.execute(stmt.order_by(Qoutes.timestamp.desc()))
                .scalars()
                .first()
            )
        if not first and not last:
            logging.info(
                "getting all qoutes between %s and %s for %s...",
                start_time,
                end_time,
                symbol,
            )
            request = StockQuotesRequest(
                symbol_or_symbols=symbol, start=start_time, end=end_time
            )
            qoutes = self.client.get_stock_quotes(request).data[symbol]
            upsert(
                get_sync_sessionm(), [qoute.model_dump() for qoute in qoutes], Qoutes
            )
        if first and first >= start_time + timedelta(days=1):
            logging.info(
                "getting qoutes at beginning between %s and %s for %s...",
                start_time,
                first,
                symbol,
            )
            request = StockQuotesRequest(
                symbol_or_symbols=symbol, start=start_time, end=first
            )
            qoutes = self.client.get_stock_quotes(request).data[symbol]
            upsert(
                get_sync_sessionm(), [qoute.model_dump() for qoute in qoutes], Qoutes
            )
        if last and last <= end_time - timedelta(days=1):
            logging.info(
                "getting qoutes at end between %s and %s for %s...",
                last,
                end_time,
                symbol,
            )

            request = StockQuotesRequest(
                symbol_or_symbols=symbol, start=last, end=end_time
            )
            qoutes = self.client.get_stock_quotes(request).data[symbol]
            upsert(
                get_sync_sessionm(), [qoute.model_dump() for qoute in qoutes], Qoutes
            )
