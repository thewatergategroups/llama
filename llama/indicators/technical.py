import numpy as np
import pandas_ta
import pandas_datareader as web
import pandas as pd
import pandas as pd
import logging
from statsmodels.regression.rolling import RollingOLS
import warnings

warnings.filterwarnings("ignore")


class Indicators:
    """
    Class used for technical indicators
    """

    def calculate_garman_klass_vol(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates Garman Klass volatility technical indicator

        Args:
            df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """
        logging.info("Calculating German class vol")
        logging.info(df)
        df["garman_klass_vol"] = ((np.log(df["high"]) - np.log(df["low"])) ** 2) / 2 - (
            2 * np.log(2) - 1
        ) * ((np.log(df["adj close"]) - np.log(df["open"])) ** 2)
        return df

    def calculate_rsi_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI indicator

        Args:
            df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """
        logging.info("Calculating RSI indicator")
        df["rsi"] = df.groupby(level=0)["adj close"].transform(
            lambda x: pandas_ta.rsi(close=x, length=20)
        )

        return df

    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate bollinger bands
        TODO: Depending on what data you pass, the level will be different. Configure through params?

        Args:
            df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """
        logging.info("Calculating Bollinger bands")

        df["bb_low"] = df.groupby(level=0)["adj close"].transform(
            lambda x: pandas_ta.bbands(close=np.log1p(x), length=20).iloc[:, 0]
        )
        df["bb_mid"] = df.groupby(level=0)["adj close"].transform(
            lambda x: pandas_ta.bbands(close=np.log1p(x), length=20).iloc[:, 1]
        )
        df["bb_high"] = df.groupby(level=0)["adj close"].transform(
            lambda x: pandas_ta.bbands(close=np.log1p(x), length=20).iloc[:, 2]
        )
        # logging.debug(df)
        return df

    def calculate_macd(self, close):
        """
        Calculate MACD indicator

        Args:
            close (_type_): _description_

        Returns:
            _type_: _description_
        """

        macd = pandas_ta.macd(close=close, length=20).iloc[:, 0]
        return macd.sub(macd.mean()).div(macd.std())

    def calculate_atr(self, stock_data):
        """
        Calculate the average true range (ATR) is a market volatility indicator.
        It is typically derived from the 14-day simple moving average of a series of true range indicators.
        The ATR was initially developed for use in commodities markets but has since been applied to all types of securities

        Exactly what stock_data is this expecting??

        Args:
            ticker (_type_): _description_
            stock_low (_type_): _description_
            stock_high (_type_): _description_
            stock_close (_type_): _description_

        Returns:
            _type_: _description_
        """
        # logging.info(f"attempting to calculate ATR for")
        atr = pandas_ta.atr(
            high=stock_data["high"],
            low=stock_data["low"],
            close=stock_data["close"],
            length=14,
        )
        # atr = pandas_ta.atr(
        #     high=stock_high,
        #     low=stock_low,
        #     close=stock_close,
        #     length=14
        # )
        normalized_atr = atr.sub(atr.mean()).div(atr.std())
        # can be applied by doing
        return normalized_atr

    def filter_top_most_liquid_stocks(self, df: pd.DataFrame):
        """Aggregate to monthly level and filter top 150 most liquid stocks for each month.
            * To reduce training time and experiment with features and strategies,
            we convert the business-daily data to month-end frequency

        Args:
            df (pd.DataFrame): _description_

        Returns:
            _type_: _description_
        """
        logging.debug("Filtering and aggregating current stock data")
        # For the moment we don't care about the rest of the columns
        # Features DataFrame
        last_cols = [
            c
            for c in df.columns.unique(0)
            if c not in ["dollar_volume" "volume" "open", "high" "low" "close"]
        ]

        # data = (pd.concat([df.unstack('ticker')['dollar_volume'].resample('M').mean().stack('ticker').to_frame('dollar_volume'),
        #                 df.unstack()[last_cols].resample('M').last().stack('ticker')],
        #                 axis=1)).dropna()
        df_first = (
            df.unstack("ticker")["dollar_volume"]
            .resample("M")
            .mean()
            .stack("ticker")
            .to_frame("dollar_volume")
        )
        # logging.info("Finished calculation of df_first")
        # logging.info(df_first)
        df_second = df.unstack()[last_cols].resample("M").last().stack("ticker")
        # logging.info("Finished calculation of df_second")
        # logging.info(df_second)

        data = (
            pd.concat([df_first, df_second], axis=1)
            .dropna()
            .drop_duplicates()
            .set_flags(allows_duplicate_labels=True)
        )

        data = data.dropna()
        logging.debug("Current data is:")
        # logging.info(data)

        return data

    def calculate_five_year_rolling_average(self, df: pd.DataFrame, data):
        """
        Calculate 5-year rolling average of dollar volume for each stocks before filtering. The reason for calculating the moving average of
        a stock is to help smooth out the price data by creating a constantly updated average price.

        By calculating the moving average, the impacts of random, short-term fluctuations on the price of a stock
        over a specified time frame are mitigated. Simple moving averages (SMAs) use a simple arithmetic average
        of prices over some timespan, while exponential moving averages (EMAs) place greater weight on more recent
        prices than older ones over the time period.

        Args:
            df (pd.DataFrame): _description_

        Returns:
            _type_: _description_
        """
        logging.info("Starting to calculate 5-year rolling average")
        top_number_of_stocks = 150

        logging.info("showing data before dollar volume")
        logging.info(data)
        logging.info(data.loc[:"dollar_volume"])
        logging.info(
            data.loc[:"dollar_volume"].unstack("ticker").rolling(5 * 12, min_periods=12)
        )
        logging.info(
            data.loc["dollar_volume"]
            .unstack("ticker")
            .rolling(5 * 12, min_periods=12)
            .mean()
        )
        data["dollar_volume"] = (
            data.loc["dollar_volume"]
            .unstack("ticker")
            .rolling(5 * 12, min_periods=12)
            .mean()
            .stack()
        )
        data["dollar_vol_rank"] = data.groupby("date")["dollar_volume"].rank(
            ascending=False
        )
        data = data[data["dollar_vol_rank"] < top_number_of_stocks].drop(
            ["dollar_volume", "dollar_vol_rank"], axis=1
        )

        return [data, df]

    def download_fama_french_factors_and_calc_rolling_factors_betas(self, data):
        """
        Download Fama-French Factors and Calculate Rolling Factor Betas.
        * Use the Fama—French data to estimate
        the exposure of assets to common risk factors using linear regression
        * The five Fama—French factors, namely market risk, size, value, operating profitability, and investment
        have been shown empirically to explain asset returns and are commonly used to assess the risk/return profile of portfolios.
        Hence, it is natural to include past factor exposures as financial features in models.
        * We can access the historical factor returns using the pandas-datareader
        and estimate historical exposures using the RollingOLS rolling linearregression.
        Data object is expected input from the calculate_five_year_rolling_average

        TODO: Exactly what data is this expecting? Possible to pass in a clear-er way?

        Args:
            data (_type_): _description_

        Returns:
            _type_: _description_
        """

        factor_data = web.DataReader(
            "F-F_Research_Data_5_Factors_2x3", "famafrench", start="2010"
        )[0].drop("RF", axis=1)
        # Fix index
        factor_data.index = factor_data.index.to_timestamp()
        # Fix end of month and percentages

        factor_data = factor_data.resample("M").last().div(100)
        factor_data.index.name = "date"

        factor_data = factor_data.join(data["returns_1m"]).sort_index()
        # factor_data

        # * Filter out stocks with less than 10 months of data. -> stock tha don't have enough data will not reliable and will break the trest
        observations = factor_data.groupby(level=1).size()

        valid_stocks = observations[observations >= 10]

        factor_data = factor_data[
            factor_data.index.get_level_values("ticker").isin(valid_stocks.index)
        ]

        # Calculate Rolling Factor Betas.
        # TODO: This needs to be abstracted in a sensible way in a separate function
        betas = factor_data.groupby(level=1, group_keys=False).apply(
            lambda x: RollingOLS(
                endog=x["return_1m"],
                exog=sm.add_constant(x.drop(["return_1m"], axis=1)),
                window=min(24, x.shape[0]),
                min_nobs=len(x.columns) + 1,
            )
            .fit(params_only=True)
            .params.drop("const", axis=1)  # Do we need this? Not convinced
        )

        # Join the rolling factors data to the main features dataframe.

        factors = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
        data = data.join(betas.groupby("ticker").shift())

        data.loc[:factors] = data.groupby("ticker", group_keys=False)[factors].apply(
            lambda x: x.fillna(x.mean())
        )
        data = data.drop("adj close", axis=1)
        data = data.dropna()
        data.info()
        return data
