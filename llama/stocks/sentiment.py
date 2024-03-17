import sys
import warnings
import logging
import yfinance as yf
import matplotlib.pyplot as plt
import os
import pandas as pd

warnings.filterwarnings('ignore')
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
        sentiment_df = pd.read_csv(os.path.join(data_dir, 'sentiment_data.csv'))

        return sentiment_df

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

sent_strat = SentimentStrategy()

sentiment_df = sent_strat.load_data(data_dir)
sentiment_df = sent_strat.normalize_twitter_data(sentiment_df)
# logger.debug(sentiment_df)
aggregated_df = sent_strat.aggregate_monthly_twitter_data(sentiment_df)
# logger.debug(aggregated_df)
filtered_df = sent_strat.select_top_stocks_monthly(aggregated_df)
logger.debug(filtered_df)