import matplotlib.pyplot as plt
from arch import arch_model
import pandas_ta
import pandas as pd
import numpy as np
import os
import matplotlib.ticker as mtick

data_folder = '/home/borisb/projects/llama/data/test/'
daily_df = pd.read_csv(os.path.join(data_folder, 'simulated_daily_data.csv'))

daily_df = daily_df.drop('Unnamed: 7', axis=1)
daily_df['Date'] = pd.to_datetime(daily_df['Date'])
daily_df = daily_df.set_index('Date')

intraday_5min_df = pd.read_csv(os.path.join(data_folder, 'simulated_5min_data.csv'))
intraday_5min_df = intraday_5min_df.drop('Unnamed: 6', axis=1)
intraday_5min_df['datetime'] = pd.to_datetime(intraday_5min_df['datetime'])
intraday_5min_df = intraday_5min_df.set_index('datetime')
intraday_5min_df['date'] = pd.to_datetime(intraday_5min_df.index.date)

print(intraday_5min_df)