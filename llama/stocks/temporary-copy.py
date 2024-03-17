import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import yfinance as yf
import os
import matplotlib.ticker as mtick

# Twitter Sentiment Investing Strategy

## 1. Load Twitter Sentiment Data
# Load the twitter sentiment dataset, set the index, calculate engagement ratio, 
# and filter out stocks with no significant twitter activity.

plt.style.use('ggplot')
data_folder = '/home/borisb/projects/Algorithmic_Trading_Machine_Learning'

sentiment_df = pd.read_csv(os.path.join(data_folder, 'sentiment_data.csv'))

sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])
sentiment_df = sentiment_df.set_index(['date', 'symbol'])

# Need to kind of normalize this so twitter likes + comments are included
sentiment_df['engagement_ratio'] = sentiment_df['twitterComments']/sentiment_df['twitterLikes']
sentiment_df = sentiment_df[(sentiment_df['twitterLikes']>20)&(sentiment_df['twitterComments']>10)]

# print(sentiment_df)

# Aggregate on a monthly level and calculate average monthly metric, for the one we choose
aggragated_df = (sentiment_df.reset_index('symbol').groupby([pd.Grouper(freq='M'), 'symbol'])
                 [['engagement_ratio']].mean())

aggragated_df['rank'] = (aggragated_df.groupby(level=0)['engagement_ratio' ].transform(lambda x: x.rank(ascending=False)))

# print(aggragated_df)

# Select top 5 stocks by rank for each month and fix the date to start at beginning of next month.

filtered_df = aggragated_df[aggragated_df['rank']<6].copy()
filtered_df = filtered_df.reset_index(level=1)

# Set the beginning of the next month
filtered_df.index = filtered_df.index + pd.DateOffset(1)
filtered_df = filtered_df.reset_index().set_index(['date', 'symbol'])

filtered_df.head(20)

# Create a dictionary containing start of month and corresponded selected stocks.

dates = filtered_df.index.get_level_values('date').unique().tolist()

fixed_dates = {}

for d in dates:
    fixed_dates[d.strftime('%Y-%m-%d')] = filtered_df.xs(d,level=0).index.tolist()

# print(fixed_dates)

# Download fresh stock prices for only selected/shortlisted stocks

stocks_list = sentiment_df.index.get_level_values('symbol').unique().tolist()

# TODO: Needs to be offline
prices_df = yf.download(tickers=stocks_list,
                        start='2021-01-01',
                        end='2023-03-01')

# Calculate Portfolio Returns with monthly rebalancing

returns_df = np.log(prices_df['Adj Close']).diff()
# print("prices_df DF")
# print(prices_df)
# print("RETURN DF")
# print(returns_df)
portfolio_df = pd.DataFrame()

# for start_date in fixed_dates.keys():
for start_date in fixed_dates.keys():
    end_date = (pd.to_datetime(start_date) + pd.offsets.MonthEnd()).strftime('%Y-%m-%d')
    cols = fixed_dates[start_date]
    temp_df = returns_df[start_date:end_date][cols].mean(axis=1).to_frame('portfolio_return')
    portfolio_df = pd.concat([portfolio_df, temp_df], axis=0)

# print(portfolio_df)
# Download NASDAQ/QQQ prices and calculate returns to compare to our strategy

qqq_df = yf.download(tickers='QQQ',
                     start='2021-01-01',
                     end='2023-03-01')


qqq_ref = np.log(qqq_df['Adj Close']).diff().to_frame('nasdaq_return')

portfolio_df = portfolio_df.merge(qqq_ref, left_index=True, right_index=True)

# print(portfolio_df)

portfolios_cumulative_return = np.exp(np.log1p(portfolio_df).cumsum()).sub(1)
portfolios_cumulative_return.plot(figsize=(16, 6))

plt.title('Twitter Engagement Ratio Strategy Return Over Time')
plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1))

plt.ylabel('Return')

plt.show()