import logging
import warnings

import pandas as pd
import numpy as np
import yfinance as yf
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
import matplotlib.ticker as mtick
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

warnings.filterwarnings("ignore")


class Utils:
    """
    Mix of functions which are either used by mulitple modules
    or need to be moved to another more appropriate place.
    """

    def visualize_stocks(self, data: pd.DataFrame) -> None:
        """
        For each month fit a K-Means Clustering Algorithm
        to group similar assets based on their features.

        You may want to initialize predefined centroids for
        each cluster based on your research.
        For visualization purpose of this tutorial we will initially rely on the
        `k-means++` initialization. Then we will pre-define our centroids
        for each cluster.  We use this data and the plots to decide on which cluster
        of stocks to form our portfolio. For this particular strategy given the
        sp500 from 2023-09-27 (!!)ship and 1 year back:
        the data Cluster 3 will be the cluster we will be using as
        they had good momentum in the previous month
        """

        data = data.drop("cluster", axis=1)
        cluster_numbers = 4

        target_rsi_values = [30, 45, 55, 70]

        # this will ensure we have the same cluster every time
        # We follow the trend of the stock with the RSI
        def get_clusters(df):
            initial_centroids = np.zeros((len(target_rsi_values), 18))
            initial_centroids[:, 6] = target_rsi_values

            df["cluster"] = (
                KMeans(
                    n_clusters=cluster_numbers, random_state=0, init=initial_centroids
                )
                .fit(df)
                .labels_
            )
            return df

        data = data.dropna().groupby("date", group_keys=False).apply(get_clusters)

        def plot_clusters(data):

            cluster_0 = data[data["cluster"] == 0]
            cluster_1 = data[data["cluster"] == 1]
            cluster_2 = data[data["cluster"] == 2]
            cluster_3 = data[data["cluster"] == 3]

            plt.scatter(
                cluster_0.iloc[:, 0],
                cluster_0.iloc[:, 6],
                color="red",
                label="cluster 0",
            )
            plt.scatter(
                cluster_1.iloc[:, 0],
                cluster_1.iloc[:, 6],
                color="green",
                label="cluster 1",
            )
            plt.scatter(
                cluster_2.iloc[:, 0],
                cluster_2.iloc[:, 6],
                color="blue",
                label="cluster 2",
            )
            plt.scatter(
                cluster_3.iloc[:, 0],
                cluster_3.iloc[:, 6],
                color="black",
                label="cluster 3",
            )

            plt.legend()
            plt.show()
            return

        plt.style.use("ggplot")

        for i in data.index.get_level_values("date").unique().tolist():
            g = data.xs(i, level=0)
            plt.title(f"Date {i}")
            # This does the visual in the end
            plot_clusters(g)

    def form_portfolio(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        7. For each month select assets based on the cluster and
        form a portfolio based on Efficient Frontier max sharpe ratio optimization
        First we will filter only stocks corresponding
        to the cluster we choose based on our hypothesis.
        For this particular strategy given the sp500
        from 2023-09-27 (!!) and 1 year back: N = 3
        """

        N = 3
        CLUSTER_NUMBER = N

        filtered_df = data[data["cluster"] == CLUSTER_NUMBER].copy()
        filtered_df = filtered_df.reset_index(level=1)
        filtered_df.index = filtered_df.index + pd.DateOffset(
            1
        )  # Move each index with 1 day in the future => beginning of the next month

        filtered_df = filtered_df.reset_index().set_index(["date", "ticker"])

        dates = filtered_df.index.get_level_values("date").unique().tolist()

        fixed_dates = {}

        for d in dates:
            fixed_dates[d.strftime("%Y-%m-%d")] = filtered_df.xs(
                d, level=0
            ).index.tolist()

        # Define portfolio optimization function
        # We will define a function which optimizes portfolio weights using PyPortfolioOpt package a
        # nd EfficientFrontier optimizer to maximize the sharpe ratio.
        # Apply single stock weight bounds constraint for diversification
        # (minimum half of equally weight and maximum 10% of portfolio)
        # TODO: Needs to be abstracted in a separate function
        def optimize_weights(prices, lower_bound=0):
            returns = expected_returns.mean_historical_return(
                prices=prices, frequency=252
            )  # 252 days = 1 year of trading days
            cov = risk_models.sample_cov(prices=prices, frequency=252)

            ef = EfficientFrontier(
                expected_returns=returns,
                cov_matrix=cov,
                weight_bounds=(
                    lower_bound,
                    0.1,
                ),  # .1 because we want maximum weight of 10% our portfolio in a single stock
                solver="SCS",
            )
            ef.max_sharpe()  # Needs to returned. We needs in the outer scope

            return ef.clean_weights()

        # Download Fresh Daily Prices Data only for short listed stocks
        stocks = data.index.get_level_values("ticker").unique().tolist()
        new_df = yf.download(
            tickers=stocks,
            start=data.index.get_level_values("date").unique()[0]
            - pd.DateOffset(months=12),
            end=data.index.get_level_values("date").unique()[-1],
        )

        # Calculate daily returns for each stock which could land up in our portfolio.
        # Then loop over each month start, select the stocks for the month and calculate their weights for the next month.
        # If the maximum sharpe ratio optimization fails for a given month, apply equally-weighted weights.
        # Calculated each day portfolio return.
        returns_dataframe = np.log(new_df["Adj Close"]).diff()

        portfolio_df = pd.DataFrame()

        # This part needs to be verified. I am not sure this returns the expected value
        for start_date in fixed_dates.items():
            # for start_date in fixed_dates.keys():
            try:
                end_date = (
                    pd.to_datetime(start_date) + pd.offsets.MonthEnd(0)
                ).strftime("%Y-%m-%d")
                cols = fixed_dates[start_date]
                optimization_start_date = (
                    pd.to_datetime(start_date) - pd.DateOffset(months=12)
                ).strftime(
                    "%Y-%m-%d"
                )  # Exactly 1 year before the start/end date
                optimization_end_date = (
                    pd.to_datetime(start_date) - pd.DateOffset(days=1)
                ).strftime("%Y-%m-%d")
                optimization_df = new_df[optimization_start_date:optimization_end_date][
                    "Adj Close"
                ][cols]
                success = False
                try:
                    weights = optimize_weights(
                        prices=optimization_df,
                        lower_bound=round(1 / (len(optimization_df.columns) * 2), 3),
                    )
                    weights = pd.DataFrame(weights, index=pd.Series(0))
                    success = True
                except Exception as e:
                    logging.error(
                        f"Max Sharpe Optimization failed for {start_date} Continuing with Equal-Weights"
                    )
                    logging.info(e)
                if success is False:
                    weights = pd.DataFrame(
                        [
                            1 / len(optimization_df.columns)
                            for i in range(len(optimization_df.columns))
                        ],
                        index=optimization_df.columns.tolist(),
                        columns=pd.Series(0),
                    ).T
                temp_df = returns_dataframe[start_date:end_date]
                temp_df = (
                    temp_df.stack()
                    .to_frame("return")
                    .reset_index(level=0)
                    .merge(
                        weights.stack()
                        .to_frame("weight")
                        .reset_index(level=0, drop=True),
                        left_index=True,
                        right_index=True,
                    )
                    .reset_index()
                    .set_index(["Date", "index"])
                    .unstack()
                    .stack()
                )
                temp_df.index.names = ["date", "ticker"]
                temp_df["weighted_return"] = temp_df["return"] * temp_df["weight"]
                temp_df = (
                    temp_df.groupby(level=0)["weighted_return"]
                    .sum()
                    .to_frame("Strategy Return")
                )
                portfolio_df = pd.concat([portfolio_df, temp_df], axis=0)
            except Exception as e:
                logging.error(e)

        portfolio_df = portfolio_df.drop_duplicates()
        logging.info(portfolio_df)
        return portfolio_df

    # Also compares to existing sp500 returns
    def visualize_portfolio_returns(
        self, portfolio_df: pd.DataFrame, dt: pd.DataFrame
    ) -> None:
        # 8. Visualize Portfolio returns and compare to SP500 returns.
        # Download the returns of SP500
        # TODO: This should be an online CSV
        spy = yf.download(tickers="SPY", start="2015-01-01", end=dt.date.today())

        spy_ret = (
            np.log(spy[["Adj Close"]])
            .diff()
            .dropna()
            .rename({"Adjj Close": "SPY Buy&Hold"}, axis=1)
        )

        portfolio_df = portfolio_df.merge(spy_ret, left_index=True, right_index=True)

        logging.info("Sample portfolio is: ")
        # logging.info(portfolio_df)

        plt.style.use("ggplot")

        portfolio_cumulative_return = np.exp(np.log1p(portfolio_df).cumsum()) - 1

        # Select the returns up to a given date
        portfolio_cumulative_return[:"2023-09-29"].plot(figsize=(16, 6))

        plt.title("Unsupervised Learning Trading Strategy Returns Over Time")
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1))
        plt.ylabel("Return")
        plt.show()

    ###### FOR Twitter sentiment Analysis
    def calculate_portfolio(self, returns_df: pd.DataFrame, dates_to_top_stocks):
        """
        Calculate portfolio returns
        """
        logging.info("Starting to calculate portfolio")
        portfolio_df = pd.DataFrame()

        for start_date in dates_to_top_stocks.keys():
            end_date = (pd.to_datetime(start_date) + pd.offsets.MonthEnd()).strftime(
                "%Y-%m-%d"
            )
            cols = dates_to_top_stocks[start_date]
            temp_df = (
                returns_df[start_date:end_date][cols]
                .mean(axis=1)
                .to_frame("portfolio_return")
            )
            portfolio_df = pd.concat([portfolio_df, temp_df], axis=0)

        logging.debug("Done with portfolio calculation")
        logging.debug(portfolio_df)
        return portfolio_df

    def plot_df(self, df: pd.DataFrame):
        """
        Plots a DataFrame

        Args:
            df (pd.DataFrame): _description_
        """
        logging.info("Plotting")
        plt.style.use("ggplot")

        df.plot(figsize=(16, 6))

        plt.title("Twitter Engagement Ratio Strategy Return Over Time")
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1))

        plt.ylabel("Return")

        # plt.show()
        plt.savefig("returns.png")
        ###### [END] %£FOR Twitter sentiment Analysis


# poetry add PyPortfolioOpt, pandas_datareader, requests, yfinance, statsmodels, scikit-learn

# Needed to resolve from _bz2 import BZ2Compressor, BZ2Decompressor
# sudo apt-get install libbz2-dev
# pyenv install 3.11

# gvk_strategy = GKV()
# df = gvk_strategy.load_sp500_data("temporary-bb-16-03-v3.csv")

# # df = gvk_strategy.calculate_garman_klass_vol(df)
# # df = gvk_strategy.calculate_rsi_indicator(df)
# # df = gvk_strategy.calculate_bollinger_bands(df)
# # df.to_csv("temporary-bb-16-03-v2.csv")
# # logging.debug("------------------------SAVING DF FOR TEMPORARY USE------------------------")
# # logging.info(df)
# # df['atr'] = df.groupby(level=1, group_keys=False).apply(gvk_strategy.calculate_atr)
# # df['macd'] = df.groupby(level=1, group_keys=False)['adj close'].apply(gvk_strategy.calculate_macd)
# # TODO: This needs to be in a function
# # df['dollar_volume'] =  (df['adj close']*df['volume'])/1e6
# # df.to_csv("temporary-bb-16-03-v3.csv")
# logging.info(df)

# data = gvk_strategy.filter_top_most_liquid_stocks(df)
# logging.info('---------------------------------')
# logging.info(data)
# logging.info(df)
# logging.info('---------------------------------')
# data, df = gvk_strategy.calculate_five_year_rolling_average(df, data)
# logging.info("calculate_five_year_rolling_average:")
# logging.info(data)
# logging.info(df)

# data = data.groupby(level=1, group_keys=False).apply(gvk_strategy.calculate_returns).dropna()
# logging.info("After regroup by")
# logging.info(data)

# data = gvk_strategy.download_fama_french_factors_and_calc_rolling_factors_betas(data)

# gvk_strategy.visualize_stocks(data)

# portfolio_df = gvk_strategy.form_portfolio(df, data)
# gvk_strategy.visualize_portfolio_returns(portfolio_df)
