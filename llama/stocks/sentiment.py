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
file_handler = logging.FileHandler('/home/borisb/projects/llama/gol/gvk.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)
data_dir = ''

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
        logging.info("Normalizing data for twitter based usage")
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index(['date', 'symbol'])

        # Need to kind of normalize this so twitter likes + comments are included
        df['engagement_ratio'] = df['twitterComments']/df['twitterLikes']
        df = df[(df['twitterLikes']>20)&(df['twitterComments']>10)]
        
        logging.debug("Done with normalizations")
        
        return df
sent_strat = SentimentStrategy()

sentiment_df = sent_strat.load_data(data_dir)
