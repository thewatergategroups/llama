"""
Technical inidicators implementation
"""

import logging
import numpy as np
import pandas_datareader as web
import pandas as pd
import pandas_ta
from statsmodels.regression.rolling import RollingOLS
import statsmodels.api as sm


class Indicators:
    """
    Class used for technical indicators
    """

    def __init__(self) -> None:
        self.close_type: str = "close"  # vs "adj close"

    def calculate_garman_klass_vol(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates Garman Klass volatility technical indicator.

        Garman Klass volatility measures the volatility of an asset's price by
        taking into account the high, low, open, and close prices over a period.

        It provides insight into the degree of price fluctuation, aiding in risk
        assessment and trade decision-making.

        Args:
            df (pd.DataFrame): DataFrame containing OHLC (open, high, low, close)
            data.

        Returns:
            pd.DataFrame: DataFrame with an additional column for Garman Klass
            volatility.

        How to apply:
        - Call this function with a DataFrame containing OHLC data.
        - Use the resulting DataFrame with Garman Klass volatility values to
        assess the level of price fluctuation in assets.
        - Higher Garman Klass volatility values indicate higher volatility, which
        may influence risk management strategies such as setting stop-loss levels
        or adjusting position sizes.
        """
        logging.info("Calculating German class vol")

        df["garman_klass_vol"] = ((np.log(df["high"]) - np.log(df["low"])) ** 2) / 2 - (
            2 * np.log(2) - 1
        ) * ((np.log(df[self.close_type]) - np.log(df["open"])) ** 2)

        logging.debug(df)
        return df

    def calculate_rsi_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the Relative Strength Index (RSI) technical indicator.

        RSI measures the magnitude of recent price changes to evaluate overbought
        or oversold conditions in a security. It is calculated based on the
        average gain and loss over a specified period, typically 14 days. RSI
        values range from 0 to 100, where readings above 70 suggest overbought
        conditions, and readings below 30 indicate oversold conditions.

        Args:
            df (pd.DataFrame): DataFrame containing closing prices.

        Returns:
            pd.DataFrame: DataFrame with an additional column for RSI values.

        How to apply:
        - Call this function with a DataFrame containing closing prices.
        - Utilize the resulting DataFrame with RSI values to identify potential
        overbought or oversold conditions in assets.
        - Consider using RSI values as part of a broader trading strategy, such
        as confirming trends or generating buy/sell signals.
        """
        logging.info("Calculating RSI indicator")

        df["rsi"] = df.groupby(level=0)[self.close_type].transform(
            lambda x: pandas_ta.rsi(close=x, length=20)
        )

        return df

    def calculate_bollinger_bands(self, df: pd.DataFrame, level: int) -> pd.DataFrame:
        """
        Calculates Bollinger Bands technical indicator.

        Bollinger Bands consist of three lines plotted based on moving averages
        and standard deviations of an asset's price. The middle band represents
        the simple moving average (SMA) of the asset's price over a specified
        period, while the upper and lower bands represent a certain number of
        standard deviations above and below the SMA, respectively. Bollinger Bands
        are used to identify volatility and potential price reversals.

        Args:
            df (pd.DataFrame): DataFrame containing closing prices.
            level (int): Level of the DataFrame for grouping purposes.

        Returns:
            pd.DataFrame: DataFrame with additional columns for Bollinger Bands
            (upper, middle, lower).

        How to apply:
        - Call this function with a DataFrame containing closing prices and a
        level for grouping purposes.
        - Use the resulting DataFrame with Bollinger Bands to identify periods
        of high or low volatility.
        - Consider combining Bollinger Bands with other technical indicators or
        fundamental analysis to confirm signals and make informed trading
        decisions.
        """
        logging.info("Calculating Bollinger bands")

        length: int = 20

        df["bb_low"] = df.groupby(level=level)[self.close_type].transform(
            lambda x: pandas_ta.bbands(close=np.log1p(x), length=length).iloc[:, 0]
        )
        df["bb_mid"] = df.groupby(level=level)[self.close_type].transform(
            lambda x: pandas_ta.bbands(close=np.log1p(x), length=length).iloc[:, 1]
        )
        df["bb_high"] = df.groupby(level=level)[self.close_type].transform(
            lambda x: pandas_ta.bbands(close=np.log1p(x), length=length).iloc[:, 2]
        )

        return df

    def calculate_macd(self, close, length: int = 20):
        """
        Calculates the Moving Average Convergence Divergence (MACD) technical
        indicator.

        MACD is a trend-following momentum indicator that shows the relationship
        between two moving averages of an asset's price. It consists of the MACD
        line (the difference between a short-term and a long-term exponential
        moving average) and the signal line (a short-term exponential moving
        average of the MACD line). Traders use MACD to identify bullish and
        bearish signals, as well as to confirm the strength of a trend.

        Args:
            close (pd.Series): Series containing closing prices.
            length (int, optional): Length of the MACD calculation window.
            Defaults to 20.

        Returns:
            pd.Series: Series containing MACD values.

        How to apply:
        - Call this function with a Series containing closing prices.
        - Utilize the resulting Series with MACD values to identify potential
        trend reversals or confirm existing trends.
        - Consider using MACD crossovers (when the MACD line crosses above or
        below the signal line) as buy or sell signals, respectively, in
        conjunction with other indicators or analysis.
        """
        logging.debug("Calculating single column MACD")

        macd = pandas_ta.macd(close=close, length=length).iloc[:, 0]
        final_macd = macd.sub(macd.mean()).div(macd.std())

        return final_macd

    def calculate_atr(self, df: pd.DataFrame):
        """
        Calculates the Average True Range (ATR) technical indicator.

        A market volatility indicator
        Derived from 14-day simple moving average of a series of true range indicators
        The ATR was initially developed for use in commodities markets
        but has since been applied to all types of securities

        ATR measures market volatility by analyzing the true range of price
        movements. It considers the greatest of the following: the current high
        minus the current low, the absolute value of the current high minus the
        previous close, and the absolute value of the current low minus the
        previous close. ATR is commonly used to set stop-loss levels and
        determine the size of potential price movements.

        Args:
            df (pd.DataFrame): DataFrame containing high, low, and close prices.

        Returns:
            pd.Series: Series containing ATR values.

        How to apply:
        - Call this function with a DataFrame containing high, low, and close
        prices.
        - Use the resulting Series with ATR values to gauge the volatility of
        assets and adjust risk management strategies accordingly.
        - Higher ATR values may indicate increased volatility, prompting wider
        stop-loss orders or smaller position sizes to mitigate risk.
        """
        logging.info("attempting to calculate ATR")

        length = 14

        atr = pandas_ta.atr(
            high=df["high"], low=df["low"], close=df["close"], length=length
        )

        normalized_atr = atr.sub(atr.mean()).div(atr.std())

        # Probably best to apply over the whole dFrame and then return it
        return normalized_atr

    def filter_top_most_liquid_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filters top 150 most liquid stocks monthly.

        Aggregate to monthly level and filter top 150 most liquid stocks for each month
        To reduce training time and experiment with features and strategies,
        we convert the business-daily data to month-end frequency

        This function aggregates stock data to the monthly level and filters the
        top 150 most liquid stocks for each month. It aims to reduce training
        time and focus on stocks with high liquidity for better analysis and
        strategy development.

        Args:
            df (pd.DataFrame): DataFrame containing stock data.

        Returns:
            pd.DataFrame: DataFrame with the top most liquid stocks for each
            month.

        How to apply:
        - Utilize the resulting DataFrame with filtered top most liquid stocks
        for each month for further analysis or strategy development.
        - High liquidity stocks are often preferred for trading due to tighter
        bid-ask spreads and higher trading volumes, which can lead to improved
        execution and reduced slippage.
        """
        logging.info("Filtering and aggregating current stock data")

        aggregated_by_dollar_volume_df = (
            df.unstack("ticker")["dollar_volume"]
            .resample("M")
            .mean()
            .stack("ticker")
            .to_frame("dollar_volume")
        )

        # For the moment we don't care about the rest of the columns
        last_cols = [
            col
            for col in df.columns.unique(0)
            if col not in ["dollar_volume", "volume", "open", "high", "low", "close"]
        ]

        filtered_df = df.unstack()[last_cols].resample("M").last().stack("ticker")

        most_liquid_df = (
            pd.concat([aggregated_by_dollar_volume_df, filtered_df], axis=1)
            .dropna()
            .drop_duplicates()
            .set_flags(allows_duplicate_labels=True)
        ).dropna()

        return most_liquid_df

    def calculate_five_year_rolling_average(
        self, most_liquid_stocks_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculates the 5-year rolling average of dollar volume for stocks.

        Calculate 5-year rolling average of dollar volume for each stocks
        The reason for calculating the moving average of
        a stock is to help smooth out the price most_liquid_stocks_df by creating
        a constantly updated average price

        By calculating the moving average which is
        the impacts of random, short-term fluctuations on the price of a stock
        over a specified time frame are mitigated

        Simple moving averages (SMAs) use a simple arithmetic average
        of prices over some timespan, while exponential moving averages (EMAs)
        place greater weight on more recent prices than older ones over the time period.


        This function calculates the 5-year rolling average of dollar volume for
        each stock before filtering. It helps smooth out price fluctuations by
        creating a constantly updated average price. By mitigating the impact of
        short-term fluctuations, this rolling average aids in better analysis
        and decision-making.

        Args:
            most_liquid_stocks_df (pd.DataFrame): DataFrame containing stock
            data.

        Returns:
            pd.DataFrame: DataFrame with the 5-year rolling average of dollar
            volume for stocks

        How to apply:
        - Call this function with a DataFrame containing stock data.
        - Use the resulting DataFrame with the 5-year rolling average of dollar
        volume to assess the long-term liquidity trend of stocks.
        - A rising rolling average may indicate increasing investor interest
        and liquidity, while a declining trend may suggest diminishing interest
        and potential liquidity constraints.
        - Consider combining this indicator with other liquidity metrics and
        fundamental analysis to gain a comprehensive understanding of a stock's
        liquidity profile.
        """
        logging.info("Starting to calculate 5-year rolling average")
        top_number_of_stocks = 150

        most_liquid_stocks_df["dollar_volume"] = (
            most_liquid_stocks_df.loc["dollar_volume"]
            .unstack("ticker")
            .rolling(5 * 12, min_periods=12)
            .mean()
            .stack()
        )

        most_liquid_stocks_df["dollar_vol_rank"] = most_liquid_stocks_df.groupby(
            "date"
        )["dollar_volume"].rank(ascending=False)

        most_liquid_stocks_df = most_liquid_stocks_df[
            most_liquid_stocks_df["dollar_vol_rank"] < top_number_of_stocks
        ].drop(["dollar_volume", "dollar_vol_rank"], axis=1)

        return most_liquid_stocks_df

    def download_fama_french_factors_and_calc_rolling_factors_betas(
        self, top_most_liquid_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Downloads Fama-French factors and calculates rolling factor betas.

        This function downloads Fama-French factor data and calculates rolling
        factor betas for stocks. The Fama-French factors (market risk, size,
        value, operating profitability, and investment) are commonly used to
        assess the risk-return profile of portfolios. Estimating historical
        exposures using rolling linear regression aids in feature modeling and
        risk assessment.

        * We can access the historical factor returns using the pandas-datareader
        and estimate historical exposures using the RollingOLS rolling linearregression.
        Data object is expected input from the calculate_five_year_rolling_average

        Args:
            top_most_liquid_df (pd.DataFrame): DataFrame containing top most
            liquid stocks data.

        Returns:
            pd.DataFrame: DataFrame with rolling factor betas for stocks.

        How to apply:
        - Call this function with a DataFrame containing top most liquid stocks
        data.
        - Use the resulting DataFrame with rolling factor betas to assess the
        sensitivity of stocks to various risk factors such as market movements,
        company size, and value metrics.
        - Factor betas provide insights into how stocks may perform under
        different market conditions and can guide portfolio construction and
        risk management strategies.
        - Consider incorporating factor betas as features in quantitative
        models or using them for portfolio optimization to enhance risk-adjusted
        returns.

        Note: Not thoroughly tested
        """

        factor_data = web.DataReader(
            "F-F_Research_Data_5_Factors_2x3", "famafrench", start="2010"
        )[0].drop("RF", axis=1)

        # Fix index
        factor_data.index = factor_data.index.to_timestamp()
        # Fix end of month and percentages

        factor_data = factor_data.resample("M").last().div(100)
        factor_data.index.name = "date"

        factor_data = factor_data.join(top_most_liquid_df["returns_1m"]).sort_index()

        # Filter out stocks with less than 10 months of data.
        # -> stock tha don't have enough data will not reliable and will break the trest
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
            ).fit(params_only=True)
            # .params.drop("const", axis=1)  # Do we need this? Not convinced
        )

        # Join the rolling factors data to the main features dataframe.

        factors = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
        top_most_liquid_by_betas_df = top_most_liquid_df.join(
            betas.groupby("ticker").shift()
        )

        top_most_liquid_by_betas_df.loc[:factors] = top_most_liquid_by_betas_df.groupby(
            "ticker", group_keys=False
        )[factors].apply(lambda x: x.fillna(x.mean()))
        top_most_liquid_by_betas_df = top_most_liquid_by_betas_df.drop(
            self.close_type, axis=1
        ).dropna()

        logging.debug(top_most_liquid_by_betas_df.info())

        return top_most_liquid_by_betas_df

    def calculate_stochastic(
        self, df: pd.DataFrame, k_period: int = 14
    ) -> pd.DataFrame:
        """
        Stochastic Oscillator

        Args:
            df (pd.DataFrame): _description_
            k_period (int, optional): _description_. Defaults to 14.

        Returns:
            pd.DataFrame: _description_
        """
        logging.info("Calculating stochastic Oscillator")
        low_min = df["low"].rolling(window=k_period).min()
        high_max = df["high"].rolling(window=k_period).max()

        df["sto"] = ((df[self.close_type] - low_min) / (high_max - low_min)) * 100
        logging.debug(df)
        return df
