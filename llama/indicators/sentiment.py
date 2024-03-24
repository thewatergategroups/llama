class Sentiment:
    """
    Class for sentiment analysis.
    Currently used only for Twitter data.
    """

    def __init__(self):
        # TODO: Fetch this data dynamically
        self.data_dir_twitter = "/home/borisb/projects/llama/"

    def load_data(self, data_dir):
        """
        Load data from CSV to DataFrame

        Args:
            data_dir (_type_): pth of data to load

        Returns:
            _type_: returns a DataFrame from the data dir
        """
        df = pd.read_csv(os.path.join(data_dir, "sentiment_data.csv"))

        return df

    def load_live_twitter_data(self):
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
            tweets_data = search_tweets(ticker)
            for tweet_data in tweets_data:
                print(tweet_data)

    def normalize_twitter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        # Need to kind of normalize this so twitter likes + comments are included
        """
        logging.info("Normalizing data for twitter based usage")

        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index(["date", "symbol"])

        df["engagement_ratio"] = df["twitterComments"] / df["twitterLikes"]

        min_likes = 20
        min_comments = 10
        df = df[
            (df["twitterLikes"] > min_likes) & (df["twitterComments"] > min_comments)
        ]

        logging.debug("Done with normalizations")
        return df

    def normalize_twitter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        # Need to kind of normalize this so twitter likes + comments are included
        """
        logging.info("Normalizing data for twitter based usage")

        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index(["date", "symbol"])

        df["engagement_ratio"] = df["twitterComments"] / df["twitterLikes"]

        min_likes = 20
        min_comments = 10
        df = df[
            (df["twitterLikes"] > min_likes) & (df["twitterComments"] > min_comments)
        ]

        logging.debug("Done with normalizations")
        return df

    def aggregate_monthly_twitter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate monthly twitter data

        Args:
            df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
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
        Select the top N(5) stocks by rank for each month and fix the date to start at beginning of next month.

        Args:
            df (pd.DataFrame): Dataframe to work on
            max_rank (int, optional): Top number of stocks to filter. Defaults to 5.

        Returns:
            pd.DataFrame: Creates a new DataFrame
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

    def select_stocks_beginning_of_month(self, df: pd.DataFrame):
        """
        TODO: Hard type return
        Create a dictionary containing start of month and corresponded selected stocks.
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

    def execute_twitter_sent_strategy(self):
        """
        Twitter Sentiment Investing Strategy
        # 1. Load Twitter Sentiment Data
        # Load the twitter sentiment dataset, set the index, calculate engagement ratio,
        # and filter out stocks with no significant twitter activity.
        """
        logging.info("Starting twitter execute strategy")
        START_DATE = "2021-01-01"
        END_DATE = "2023-03-01"

        sentiment_df = self.load_data(self.data_dir_twitter)
        sentiment_df = self.normalize_twitter_data(sentiment_df)
        # logger.debug(sentiment_df)
        aggregated_df = self.aggregate_monthly_twitter_data(sentiment_df)
        # logger.debug(aggregated_df)
        filtered_df = self.select_top_stocks_monthly(aggregated_df)
        # logger.debug(filtered_df)
        dates_to_top_stocks = self.select_stocks_beginning_of_month(filtered_df)

        # Download fresh stock prices for only selected/shortlisted stocks
        stocks_list = sentiment_df.index.get_level_values("symbol").unique().tolist()
        prices_df = self.download_data(stocks_list, START_DATE, END_DATE)
        # Calculate Portfolio Returns with monthly rebalancing
        returns_df = np.log(prices_df["Adj Close"]).diff()
        portfolio_df = self.calculate_portfolio(returns_df, dates_to_top_stocks)
        # logger.debug(portfolio_df)

        # Download NASDAQ/QQQ prices and calculate returns to compare to our strategy
        qqq_df = self.download_data("QQQ", START_DATE, END_DATE)
        qqq_ref = np.log(qqq_df["Adj Close"]).diff().to_frame("nasdaq_return")

        portfolio_df = portfolio_df.merge(qqq_ref, left_index=True, right_index=True)

        # logger.debug(portfolio_df)

        portfolios_cumulative_return = np.exp(np.log1p(portfolio_df).cumsum()).sub(1)

        self.plot_df(portfolios_cumulative_return)
