import logging
import os
from pathlib import Path
import pandas as pd
import numpy as np
import tweepy
from utilities import Utils


class Sentiment:
    """
    Class for sentiment analysis.
    Currently used only for Twitter data.
    """

    def load_data(self, data_dir: str, data_file_name: str = "sentiment_data.csv"):
        """
        Load data from CSV to DataFrame

        Args:
            data_dir (_type_): pth of data to load

        Returns:
            _type_: returns a DataFrame from the data dir
        """
        logging.debug("Attempting to load data to CSV")
        df = pd.read_csv(os.path.join(data_dir, data_file_name))

        return df

    def load_live_twitter_data(self):
        """
        Load live Twitter data for specified stock tickers

        Description:
            This function fetches live Twitter data using the Tweepy library for
            the specified stock tickers. It searches for tweets containing the ticker
            symbols and collects relevant data such as tweet text, likes, and retweets.
            The function can be used to gather real-time sentiment information
            from Twitter, which can be valuable for short-term trading strategies
            based on social media sentiment analysis.

        TODO: This just needs a settings obj passed
        """
        # Your Twitter API credentials
        api_key = ""
        api_secret = ""
        access_token = ""
        access_token_secret = ""

        # Set up Twitter API access
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        # Load S&P 500 tickers
        tickers = ["AAPL", "MSFT", "GOOGL"]  # Replace this with your actual list

        # Function to get Twitter data
        def get_twitter_data(ticker):
            """
            No free access for this.
            TODO: Look for mock data online
            """
            # Search for tweets containing the ticker
            tweets = api.search_tweets(q=ticker, count=100)  # Adjust count as needed
            data = []
            for tweet in tweets:
                logging.info(tweet)
                # Here we're just collecting the tweet's text, likes and retweets count.
                # You can adjust this as needed.
                tweet_data = {
                    "text": tweet.text,
                    "likes": tweet.favorite_count,
                    "retweets": tweet.retweet_count,
                }
                data.append(tweet_data)

            logging.info("all twitter data is:")
            logging.info(data)
            return data

        # Iterate over tickers and get Twitter data
        for ticker in tickers:
            ticker_data = get_twitter_data(ticker)
            print(f"Data for {ticker}: {ticker_data}")
            # Here you can also save this data to a file, database, etc.

        # Example usage
        tickers = ["AAPL", "MSFT", "GOOGL"]  # Add your S&P 500 tickers here
        for ticker in tickers:
            print(f"Data for {ticker}:")
            tweets_data = api.search_tweets(ticker)
            for tweet_data in tweets_data:
                print(tweet_data)

    def normalize_twitter_data(
        self, df: pd.DataFrame, min_likes: int = 20, min_comments: int = 10
    ) -> pd.DataFrame:
        """
        Normalize Twitter data for analysis

        This function normalizes raw Twitter data for analysis by converting
        relevant columns to appropriate data types, calculating engagement ratios,
        and filtering out insignificant data. The engagement ratio is computed
        by dividing the number of comments by the number of likes for each tweet.
        Normalizing the data prepares it for further analysis, such as aggregating
        monthly sentiment scores or selecting top-performing stocks based on
        Twitter activity.

        Args:
            df (pd.DataFrame): DataFrame containing raw Twitter data.

        Returns:
            pd.DataFrame: DataFrame with normalized Twitter data.
        """
        logging.info("Normalizing data for twitter based usage")

        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index(["date", "symbol"])

        df["engagement_ratio"] = df["twitterComments"] / df["twitterLikes"]

        df = df[
            (df["twitterLikes"] > min_likes) & (df["twitterComments"] > min_comments)
        ]

        logging.debug("Done with normalizations")
        return df

    def aggregate_monthly_twitter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate monthly twitter data

        This function aggregates normalized Twitter data on a monthly basis,
        calculating the mean engagement ratio for each stock symbol. Additionally,
        it ranks the stocks based on their engagement ratio within each month.
        Aggregating the data allows for a broader analysis of sentiment trends
        over time, aiding in identifying stocks with consistently high social
        media engagement, which may be indicative of market sentiment.

        Args:
            df (pd.DataFrame): DataFrame containing normalized Twitter data.

        Returns:
            pd.DataFrame: DataFrame with aggregated monthly Twitter data.
        """
        logging.info("Starting to aggregate monthly data")
        aggregated_df = (
            df.reset_index("symbol")
            .groupby([pd.Grouper(freq="M"), "symbol"])[["engagement_ratio"]]
            .mean()
        )

        aggregated_df["rank"] = aggregated_df.groupby(level=0)[
            "engagement_ratio"
        ].transform(lambda x: x.rank(ascending=False))

        logging.debug("Done with all aggregations")
        return aggregated_df

    def select_top_stocks_monthly(self, df: pd.DataFrame, max_rank=5) -> pd.DataFrame:
        """
        Select top-performing stocks monthly
        * fixes the date to start at beginning of next month.

        Args:
            df (pd.DataFrame): DataFrame containing aggregated monthly Twitter data.
            max_rank (int, optional): Maximum number of top-performing stocks to select.
                Defaults to 5.

        Returns:
            pd.DataFrame: DataFrame containing selected top-performing stocks.

        """
        logging.info("Starting to select top stocks for each month")

        filtered_df = df[df["rank"] <= max_rank].copy()
        filtered_df = filtered_df.reset_index(level=1)

        # Set the beginning of the next month (!!)
        filtered_df.index = filtered_df.index + pd.DateOffset(1)
        filtered_df = filtered_df.reset_index().set_index(["date", "symbol"])
        # logging.debug(filtered_df.head(20))
        logging.debug("Done with choosing the top 20 stocks")
        return filtered_df

    def select_stocks_beginning_of_month(self, df: pd.DataFrame) -> dict:
        """
        Select stocks at the beginning of each month

        Args:
            df (pd.DataFrame): DataFrame containing selected top-performing stocks.

        Returns:
            dict: Dictionary mapping dates to corresponding selected stocks.

        This function selects the top-performing stocks at the beginning of each month
        and returns a dictionary mapping dates to the selected stocks. By filtering
        stocks at the beginning of each month, traders can ensure that their portfolio
        reflects the most recent sentiment trends, allowing for timely adjustments
        based on changing market dynamics.
        """
        logging.info("Filtering and selecting stocks for each month")
        dates = df.index.get_level_values("date").unique().tolist()

        top_number_of_stocks_with_dates = {}
        for d in dates:
            top_number_of_stocks_with_dates[d.strftime("%Y-%m-%d")] = df.xs(
                d, level=0
            ).index.tolist()

        logging.debug(top_number_of_stocks_with_dates)
        return top_number_of_stocks_with_dates

    def execute_twitter_sent_strategy(
        self,
        start_date: str = "2021-01-01",
        end_date: str = "2023-03-01",
    ) -> None:
        """
        Twitter Sentiment Investing Strategy
        # 1. Load Twitter Sentiment Data
        # Load the twitter sentiment dataset, set the index, calculate engagement ratio,
        # and filter out stocks with no significant twitter activity.
        Execute Twitter sentiment-based trading strategy

        This function implements a trading strategy based on Twitter sentiment analysis.
        It loads historical Twitter sentiment data, normalizes the data, aggregates it
        on a monthly basis, selects the top-performing stocks monthly, and constructs
        a portfolio based on these selections. The portfolio's performance is evaluated
        by comparing it to a benchmark index, such as NASDAQ/QQQ, to assess the
        effectiveness of the sentiment-based strategy. By executing this strategy,
        traders can leverage social media sentiment to make informed trading decisions
        and potentially outperform traditional market benchmarks.
        """
        logging.info("Starting twitter execute strategy")

        utils = Utils()
        data_dir = Path().absolute()

        sentiment_df = self.load_data(data_dir)
        sentiment_df = self.normalize_twitter_data(sentiment_df)
        # logger.debug(sentiment_df)
        aggregated_df = self.aggregate_monthly_twitter_data(sentiment_df)
        # logger.debug(aggregated_df)
        filtered_df = self.select_top_stocks_monthly(aggregated_df)
        # logger.debug(filtered_df)
        dates_to_top_stocks = self.select_stocks_beginning_of_month(filtered_df)

        # Download fresh stock prices for only selected/shortlisted stocks
        stocks_list = sentiment_df.index.get_level_values("symbol").unique().tolist()

        # Needs to fetch from DB
        prices_df = utils.download_data(stocks_list, start_date, end_date)
        # Calculate Portfolio Returns with monthly rebalancing
        returns_df = np.log(prices_df["Adj Close"]).diff()
        portfolio_df = utils.calculate_portfolio(returns_df, dates_to_top_stocks)
        # logger.debug(portfolio_df)

        # Download NASDAQ/QQQ prices and calculate returns to compare to our strategy
        qqq_df = utils.download_data("QQQ", start_date, end_date)
        qqq_ref = np.log(qqq_df["Adj Close"]).diff().to_frame("nasdaq_return")

        portfolio_df = portfolio_df.merge(qqq_ref, left_index=True, right_index=True)

        # logger.debug(portfolio_df)

        portfolios_cumulative_return = np.exp(np.log1p(portfolio_df).cumsum()).sub(1)

        utils.plot_df(portfolios_cumulative_return)
