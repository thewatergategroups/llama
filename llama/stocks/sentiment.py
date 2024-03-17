import sys
import warnings
import logging
import yfinance as yf
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import matplotlib.ticker as mtick

# warnings.filterwarnings('ignore')
yf.pdr_override()  # Enable caching

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
file_handler = logging.FileHandler('/home/borisb/projects/llama/gol/sentiment.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

data_dir = '/home/borisb/projects/llama/'

class SentimentStrategy():
    """
    # Twitter Sentiment Investing Strategy

    ## 1. Load Twitter Sentiment Data
    # Load the twitter sentiment dataset, set the index, calculate engagement ratio, 
    # and filter out stocks with no significant twitter activity.
    """
    def load_data(self, data_dir):
        """
        Load data from CSV to DataFrame

        Args:
            data_dir (_type_): pth of data to load

        Returns:
            _type_: returns a DataFrame from the data dir
        """
        df = pd.read_csv(os.path.join(data_dir, 'sentiment_data.csv'))

        return df

    def normalize_twitter_data(self, df: pd.DataFrame):
        logger.info("Normalizing data for twitter based usage")
 
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index(['date', 'symbol'])

        # Need to kind of normalize this so twitter likes + comments are included
        df['engagement_ratio'] = df['twitterComments']/df['twitterLikes']
        df = df[(df['twitterLikes']>20)&(df['twitterComments']>10)]

        logger.debug("Done with normalizations")

        return df

    def aggregate_monthly_twitter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Starting to aggregate monthly data")
        aggregated_df = (df.reset_index('symbol').groupby([pd.Grouper(freq='M'), 'symbol'])
                 [['engagement_ratio']].mean())

        aggregated_df['rank'] = (aggregated_df.groupby(level=0)['engagement_ratio' ].transform(lambda x: x.rank(ascending=False)))
    
        logger.debug("Done with all aggregations")
        return aggregated_df

    def select_top_stocks_monthly(self, df: pd.DataFrame, max_rank = 5) -> pd.DataFrame:
        """
        Select the top N(5) stocks by rank for each month and fix the date to start at beginning of next month.

        Args:
            df (pd.DataFrame): Dataframe to work on
            max_rank (int, optional): Top number of stocks to filter. Defaults to 5.

        Returns:
            pd.DataFrame: Creates a new DataFrame
        """
        logger.info("Starting to select top stocks for each month")
        
        filtered_df = df[df['rank' ] <= max_rank].copy()
        filtered_df = filtered_df.reset_index(level=1)

        # Set the beginning of the next month (!!)
        filtered_df.index = filtered_df.index + pd.DateOffset(1)
        filtered_df = filtered_df.reset_index().set_index(['date', 'symbol'])
        # logger.debug(filtered_df.head(20))
        logger.debug("Done with choosing the top 20 stocks")
        
        return filtered_df
    
    def select_stocks_beginning_of_month(self, df: pd.DataFrame):
        # TODO: Hard type return
        # Create a dictionary containing start of month and corresponded selected stocks.
        logger.info("Filtering and selecting stocks for each month")
        dates = df.index.get_level_values('date').unique().tolist()

        top_number_of_stocks_with_dates = {}
        for d in dates:
            top_number_of_stocks_with_dates[d.strftime('%Y-%m-%d')] = df.xs(d, level=0).index.tolist()

        logger.debug(top_number_of_stocks_with_dates)
        return top_number_of_stocks_with_dates

    def calculate_portfolio(self, returns_df: pd.DataFrame):
        logger.info("Starting to calculate portfolio")
        portfolio_df = pd.DataFrame()

        for start_date in dates_to_top_stocks.keys():
            end_date = (pd.to_datetime(start_date) + pd.offsets.MonthEnd()).strftime('%Y-%m-%d')
            cols = dates_to_top_stocks[start_date]
            temp_df = returns_df[start_date:end_date][cols].mean(axis=1).to_frame('portfolio_return')
            portfolio_df = pd.concat([portfolio_df, temp_df], axis=0)
  
        logger.debug("Done with portfolio calculation")
        logger.debug(portfolio_df)
        return portfolio_df

    def download_data(self, ticker_list, start_date: str, end_date: str) -> pd.DataFrame:
        qqq_df = yf.download(tickers=ticker_list,
                     start=start_date,
                     end=end_date)
        
        return qqq_df

    def plot_df(self, df: pd.DataFrame):
        logger.info("Plotting")
        
        df.plot(figsize=(16, 6))

        plt.title('Twitter Engagement Ratio Strategy Return Over Time')
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1))

        plt.ylabel('Return')

        plt.show()
    
    def execute_twitter_sent_strategy(self):
        """
        Executes a sentiment analysis strategy 
        """
        logger.info("Starting twitter execute strategy")
        START_DATE = '2021-01-01'
        END_DATE = '2023-03-01'

        sentiment_df = self.load_data(data_dir)
        sentiment_df = self.normalize_twitter_data(sentiment_df)
        # logger.debug(sentiment_df)
        aggregated_df = self.aggregate_monthly_twitter_data(sentiment_df)
        # logger.debug(aggregated_df)
        filtered_df = self.select_top_stocks_monthly(aggregated_df)
        # logger.debug(filtered_df)
        dates_to_top_stocks = self.select_stocks_beginning_of_month(filtered_df)

        # Download fresh stock prices for only selected/shortlisted stocks
        stocks_list = sentiment_df.index.get_level_values('symbol').unique().tolist()
        prices_df = self.download_data(stocks_list, START_DATE, END_DATE)
        # Calculate Portfolio Returns with monthly rebalancing
        returns_df = np.log(prices_df['Adj Close']).diff()
        portfolio_df = self.calculate_portfolio(returns_df)
        # logger.debug(portfolio_df)

        # Download NASDAQ/QQQ prices and calculate returns to compare to our strategy
        qqq_df = self.download_data('QQQ', START_DATE, END_DATE)
        qqq_ref = np.log(qqq_df['Adj Close']).diff().to_frame('nasdaq_return')

        portfolio_df = portfolio_df.merge(qqq_ref, left_index=True, right_index=True)

        # logger.debug(portfolio_df)

        portfolios_cumulative_return = np.exp(np.log1p(portfolio_df).cumsum()).sub(1)

        self.plot_df(portfolios_cumulative_return)

sent_strat = SentimentStrategy()
sent_strat.execute_twitter_sent_strategy()

# sentiment_df = sent_strat.load_data(data_dir)
# sentiment_df = sent_strat.normalize_twitter_data(sentiment_df)
# # logger.debug(sentiment_df)
# aggregated_df = sent_strat.aggregate_monthly_twitter_data(sentiment_df)
# # logger.debug(aggregated_df)
# filtered_df = sent_strat.select_top_stocks_monthly(aggregated_df)
# logger.debug(filtered_df)
# dates_to_top_stocks = sent_strat.select_stocks_beginning_of_month(filtered_df)

# # Download fresh stock prices for only selected/shortlisted stocks
# stocks_list = sentiment_df.index.get_level_values('symbol').unique().tolist()
# prices_df = yf.download(tickers=stocks_list,
#                         start='2021-01-01',
#                         end='2023-03-01')

# # Calculate Portfolio Returns with monthly rebalancing
# returns_df = np.log(prices_df['Adj Close']).diff()
# portfolio_df = sent_strat.calculate_portfolio(returns_df)
# # logger.debug(portfolio_df)

# # Download NASDAQ/QQQ prices and calculate returns to compare to our strategy
# qqq_df = sent_strat.download_data('QQQ')
# qqq_ref = np.log(qqq_df['Adj Close']).diff().to_frame('nasdaq_return')

# portfolio_df = portfolio_df.merge(qqq_ref, left_index=True, right_index=True)

# # logger.debug(portfolio_df)

# portfolios_cumulative_return = np.exp(np.log1p(portfolio_df).cumsum()).sub(1)

# sent_strat.plot_df(portfolios_cumulative_return)
