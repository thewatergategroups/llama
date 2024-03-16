from sqlalchemy.orm import Mapped, mapped_column
import numpy as np
import pandas_ta
import pandas_datareader as web
import pandas as pd
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from trekkers import BaseSql
import matplotlib.ticker as mtick
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime as dt
import logging
from statsmodels.regression.rolling import RollingOLS
from sklearn.cluster import KMeans
import sys

# warnings.filterwarnings('ignore')
yf.pdr_override()  # Enable caching

# poetry add PyPortfolioOpt, pandas_datareader, requests, yfinance, statsmodels, scikit-learn

# Needed to resolve from _bz2 import BZ2Compressor, BZ2Decompressor
# sudo apt-get install libbz2-dev
# pyenv install 3.11   

# class Bars(BaseSql):
#     __tablename__ = "bars"
#     __table_args__ = {"schema": "llama"}

#     symbol: Mapped[str] = mapped_column(primary_key=True)
#     timeframe: Mapped[str] = mapped_column(primary_key=True)
#     timestamp: Mapped[datetime] = mapped_column(primary_key=True)
#     open: Mapped[float]
#     close: Mapped[float]
#     high: Mapped[float]
#     low: Mapped[float]
#     trade_count: Mapped[int]
#     vwap: Mapped[float]
#     volume: Mapped[int]

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

data_folder = '/home/borisb/projects/llama/data/test/'

class GKV(): # Needs to extend Bars?

    # self.df = [] # TODO: Insert data here, ideally as a dataFrame

    """
    Downloads SP500 data for 1 year given an an end data.
    Also, saves the 
    TODO: Break this up into 2/3 other functions for each of the parts
    """
    def download_data_from_source(self, end_date = '2023-09-29', download_filename="sp500-yf-2.csv"):
        # url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        # response = requests.get(url)
        
        # with open('sp500.html', 'w') as file:
        #     file.write(response.text)

        # sp500 = pd.read_html(response.text)[0]
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        # sp500 = response.text[0]
        # Normalize the data
        sp500['Symbol'] = sp500['Symbol'].str.replace('.', '-')
        symbols_list = sp500['Symbol'].unique().tolist()

        # Exactly 1 year before start of the data
        start_date = pd.to_datetime(end_date)-pd.DateOffset(365*8)

        df = yf.download(tickers=symbols_list,
                            start=start_date,
                            end=end_date).stack()

        df.index.names = ['date', 'ticker']
        df.columns = df.columns.str.lower()

        # TODO: Improve to which dir it goes + date in filename
        df.to_csv(download_filename)
        logging.debug(df)
        
        return df

    def load_sp500_data(self) -> pd.DataFrame:
        """
        Load sp500 Data given an an already downloaded file
        Returns a fully populated pandas Dataframe with all of the necessary data

        Returns:
            pd.DataFrame: _description_
        """
        logging.info("Starting to load sp500 Data")
        # sp500 = pd.read_html('sp500.html')[0]
        # print(sp500)
        # sp500['Symbol'] = sp500['Symbol'].str.replace('.', '-')
        # symbols_list = sp500['Symbol'].unique().tolist()
        # end_date = '2023-09-27'

        # TODO: Improve to which dir it goes + date in filename
        df = pd.read_csv("sp500-yf-3.csv",index_col=['date', 'ticker'], encoding='utf-8-sig')
        logging.debug(df)
        return df

    def calculate_german_klass_vol(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates German Klass volatility technical indicator

        Args:
            df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """
        logging.info("Calculating German class vol")
        logging.debug(df)
        df['garman_klass_vol'] = ((np.log(df['high'])-np.log(df['low']))**2)/2-(2*np.log(2)-1)*((np.log(df['adj close'])-np.log(df['open']))**2)
        return df

    def calculate_rsi_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI indicator 

        Args:
            df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """ 
        logging.info("Calculating RSI indicator")
        logging.debug(df)
        logging.debug(df.index)
        df['rsi'] = df.groupby(level=1)['adj close'].transform(lambda x: pandas_ta.rsi(close=x, length=20))
        
        return df

    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate bollinger bands 

        Args:
            df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """
        logging.info("Calculating Bollinger bands")

        df['bb_low'] = df.groupby(level=1)['adj close'].transform(lambda x: pandas_ta.bbands(close=np.log1p(x), length=20).iloc[:,0])
        df['bb_mid'] = df.groupby(level=1)['adj close'].transform(lambda x: pandas_ta.bbands(close=np.log1p(x), length=20).iloc[:,1])
        df['bb_high'] = df.groupby(level=1)['adj close'].transform(lambda x: pandas_ta.bbands(close=np.log1p(x), length=20).iloc[:,2])
        logging.debug(df)
        return df

    def calculate_macd(self, close):
        """
        Calculate MACD indicator

        Args:
            close (_type_): _description_

        Returns:
            _type_: _description_
        """

        macd = pandas_ta.macd(close=close, length=20).iloc[:,0]
        return macd.sub(macd.mean()).div(macd.std())

    def calculate_atr(self, ticker, stock_low, stock_high, stock_close):
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
        logging.debug(f"attempting to calculate ATR for ${ticker}")
        # atr = pandas_ta.atr(
        #     high=stock_data['high'],
        #     low=stock_data['low'],
        #     close=stock_data['close'],
        #     length=14
        # )
        atr = pandas_ta.atr(
            high=stock_high,
            low=stock_low,
            close=stock_close,
            length=14
        )
        normalized_atr = atr.sub(atr.mean()).div(atr.std())
        # can be applied by doing 
        return normalized_atr
    
    def calculate_five_year_rolling_average(self, df: pd.DataFrame):
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

        # For the moment we don't care about the rest of the columns
        df['garman_klass_vol'] = ((np.log(df['high'])-np.log(df['low']))**2)/2-(2*np.log(2)-1)*((np.log(df['adj close'])-np.log(df['open']))**2)
        last_cols = [c for c in df.columns.unique(0) if c not in ['dollar_volume', 'volume', 'open', 'high', 'low','close']]

        data = (pd.concat([df.unstack('ticker')['dollar_volume'].resample('M').mean().stack('ticker').to_frame('dollar_volume'),
                           df.unstack()[last_cols].resample('M').last().stack('ticker')],
                          axis=1)).dropna()
        data['dollar_volume'] = (data.loc[: 'dollar_volume'].unstack('ticker').rolling(5*12, min_periods=12).mean().stack())
        data['dollar_vol_rank'] = (data.groupby('date')['dollar_volume'].rank(ascending=False))
        data = data[data['dollar_vol_rank']<150].drop(['dollar_volume', 'dollar_vol_rank'], axis=1)

        return [data, df]
 
    def calculate_returns(df):
        """ Calculate Monthly Returns for different time horizons as features.
            To capture time series dynamics that reflect, for example, momentum patterns, 
            we compute historical returns using the method .pct_change(lag), that is, 
            returns over various monthly periods as identified by lags.
        Args:
            df (_type_): _description_

        Returns:
            _type_: _description_
        """
        outlier_cutoff = 0.005
        lags = [1, 2, 6, 9, 12]
        
        for lag in lags:
            df[f'returnm_{lag}m'] = (df['adj close']
                                    .pct_change(lag) # calculate return for a given lag  
                                    .pipe(lambda x: x.clip(lower=x.quantile(outlier_cutoff),
                                                            upper=x.quantile(1-outlier_cutoff)))
                                    .add(1)
                                    .pow(1/lag)
                                    .sub(1))
        return df
    

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

        factor_data = web.DataReader('F-F_Research_Data_5_Factors_2x3',
                                    'famafrench',
                                    start='2010')[0].drop('RF', axis=1)
       
        # Fix index
        factor_data.index = factor_data.index.to_timestamp()
        # Fix end of month and percentages

        factor_data = factor_data.resample('M').last().div(100)
        factor_data.index.name = 'date'

        factor_data = factor_data.join(data['returns_1m']).sort_index()
        # factor_data

        # * Filter out stocks with less than 10 months of data. -> stock tha don't have enough data will not reliable and will break the trest
        observations = factor_data.groupby(level=1).size()

        valid_stocks = observations[observations >= 10] 

        factor_data = factor_data[factor_data.index.get_level_values('ticker').isin(valid_stocks.index)]
        
        # Calculate Rolling Factor Betas.
        # TODO: This needs to be abstracted in a sensible way in a separate function
        betas = (factor_data.groupby(level=1, group_keys=False)
                .apply(lambda x: RollingOLS(endog=x['return_1m'],
                                            exog=sm.add_constant(x.drop(['return_1m'], axis=1)),
                                            window=min(24, x.shape[0]),
                                            min_nobs=len(x.columns)+1)
                .fit(params_only=True)
                 .params # Do we need this? Not convinced
                .drop('const', axis=1)))


        # Join the rolling factors data to the main features dataframe.

        factors = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']
        data = (data.join(betas.groupby('ticker').shift()))

        data.loc[: factors] = data.groupby('ticker', group_keys=False)[factors].apply(lambda x: x.fillna(x.mean()))
        data = data.drop('adj close', axis=1)
        data = data.dropna()
        data.info()
        return data

    def visualize_stocks(self, data):
        """
        # 6. For each month fit a K-Means Clustering Algorithm to group similar assets based on their features.
        ### K-Means Clustering
        # You may want to initialize predefined centroids for each cluster based on your research.
        # For visualization purpose of this tutorial we will initially rely on the ‘k-means++’ initialization.
        # Then we will pre-define our centroids for each cluster.
        # We use this data and the plots to decide on which cluster of stocks to form our portfolio
        # For this particular strategy given the sp500 from 2023-09-27 (!!) and 1 year back:
        # the data Cluster 3 will be the cluster we will be using as they had good momentum in the previous month

        Args:
            data (_type_): _description_

        Returns:
            _type_: _description_
        """        

        data = data.drop('cluster', axis=1)
        cluster_numbers = 4

        target_rsi_values = [30, 45, 55, 70]

        # this will ensure we have the same cluster every time
        # We follow the trend of the stock with the RSI
        def get_clusters(df):
            initial_centroids = np.zeros((len(target_rsi_values), 18))
            initial_centroids[:, 6] = target_rsi_values
           
            df['cluster'] = KMeans(n_clusters=cluster_numbers,
                                random_state=0,
                                init=initial_centroids).fit(df).labels_
            return df

        data = data.dropna().groupby('date', group_keys=False).apply(get_clusters)

        def plot_clusters(data):

            cluster_0 = data[data['cluster']==0]
            cluster_1 = data[data['cluster']==1]
            cluster_2 = data[data['cluster']==2]
            cluster_3 = data[data['cluster']==3]

            plt.scatter(cluster_0.iloc[:,0],  cluster_0.iloc[:,6],  color = 'red', label='cluster 0')
            plt.scatter(cluster_1.iloc[:,0],  cluster_1.iloc[:,6],  color = 'green', label='cluster 1')
            plt.scatter(cluster_2.iloc[:,0],  cluster_2.iloc[:,6],  color = 'blue', label='cluster 2')
            plt.scatter(cluster_3.iloc[:,0],  cluster_3.iloc[:,6],  color = 'black', label='cluster 3')
           
            plt.legend()
            plt.show()
            return

        plt.style.use('ggplot')

        for i in data.index.get_level_values('date').unique().tolist():
            g = data.xs(i, level=0)
            plt.title(f'Date {i}')
            # This does the visual in the end
            plot_clusters(g)

    def form_portfolio(self, data):
        """
        # 7. For each month select assets based on the cluster and form a portfolio based on Efficient Frontier max sharpe ratio optimization
        # First we will filter only stocks corresponding to the cluster we choose based on our hypothesis.
        # For this particular strategy given the sp500 from 2023-09-27 (!!) and 1 year back: N = 3

        Args:
            data (_type_): _description_

        Returns:
            _type_: _description_
        """
        N = 3
        CLUSTER_NUMBER = N

        filtered_df = data[data['cluster']==CLUSTER_NUMBER].copy()
        filtered_df = filtered_df.reset_index(level=1)
        filtered_df.index = filtered_df.index + pd.DateOffset(1) # Move each index with 1 day in the future => beginning of the next month

        filtered_df = filtered_df.reset_index().set_index(['date', 'ticker'])

        dates = filtered_df.index.get_level_values('date').unique().tolist()

        fixed_dates = {}

        for d in dates:
            fixed_dates[d.strftime('%Y-%m-%d')] = filtered_df.xs(d, level=0).index.tolist()

        # Define portfolio optimization function
        # We will define a function which optimizes portfolio weights using PyPortfolioOpt package and EfficientFrontier optimizer to maximize the sharpe ratio.
        # Apply single stock weight bounds constraint for diversification (minimum half of equally weight and maximum 10% of portfolio)
        def optimize_weights(prices, lower_bound=0):
            returns = expected_returns.mean_historical_return(prices=prices,
                                                            frequency=252) # 252 days = 1 year of trading days
            cov = risk_models.sample_cov(prices=prices,
                                        frequency=252)
          
            ef = EfficientFrontier(expected_returns=returns,
                                cov_matrix=cov,
                                weight_bounds=(lower_bound, .1), # .1 because we want maximum weight of 10% our portfolio in a single stock
                                solver='SCS')
            weights = ef.max_sharpe() # Needs to returned. We needs in the outer scope
          
            return ef.clean_weights()

        # Download Fresh Daily Prices Data only for short listed stocks
        stocks = data.index.get_level_values('ticker').unique().tolist()
        new_df = yf.download(tickers=stocks,
                            start=data.index.get_level_values('date').unique()[0] - pd.DateOffset(months=12),
                            end=data.index.get_level_values('date').unique()[-1])

        # Calculate daily returns for each stock which could land up in our portfolio.
        # Then loop over each month start, select the stocks for the month and calculate their weights for the next month.
        # If the maximum sharpe ratio optimization fails for a given month, apply equally-weighted weights.
        # Calculated each day portfolio return.
        returns_dataframe = np.log(new_df['Adj Close']).diff()

        portfolio_df = pd.DataFrame()

        # This part needs to be verified. I am not sure this returns the expected value 
        for start_date in fixed_dates.items():
        # for start_date in fixed_dates.keys():
            try:
                end_date = (pd.to_datetime(start_date)+pd.offsets.MonthEnd(0)).strftime('%Y-%m-%d')
                cols = fixed_dates[start_date]
                optimization_start_date = (pd.to_datetime(start_date)-pd.DateOffset(months=12)).strftime('%Y-%m-%d') # Exactly 1 year before the start/end date
                optimization_end_date = (pd.to_datetime(start_date)-pd.DateOffset(days=1)).strftime('%Y-%m-%d')
                optimization_df = new_df[optimization_start_date:optimization_end_date]['Adj Close'][cols]
                success = False
                try:
                    weights = optimize_weights(prices=optimization_df, lower_bound=round(1/(len(optimization_df.columns)*2),3))
                    weights = pd.DataFrame(weights, index=pd.Series(0))
                    success = True
                except Exception as e:
                    logging.error(f'Max Sharpe Optimization failed for {start_date} Continuing with Equal-Weights')
                    logging.debug(e)
                if success == False:
                    weights = pd.DataFrame([1/len(optimization_df.columns) for i in range(len(optimization_df.columns))],
                                        index=optimization_df.columns.tolist(),
                                        columns=pd.Series(0)).T
                temp_df = returns_dataframe[start_date:end_date]
                temp_df = temp_df.stack().to_frame('return').reset_index(level=0)\
                        .merge(weights.stack().to_frame('weight').reset_index(level=0, drop=True),
                                left_index=True,
                                right_index=True)\
                        .reset_index().set_index(['Date', 'index']).unstack().stack()
                temp_df.index.names = ['date', 'ticker']
                temp_df['weighted_return'] = temp_df['return']*temp_df['weight']
                temp_df = temp_df.groupby(level=0)['weighted_return'].sum().to_frame('Strategy Return')
                portfolio_df = pd.concat([portfolio_df, temp_df], axis=0)
            except Exception as e:
                print(e)

        portfolio_df = portfolio_df.drop_duplicates()
        print(portfolio_df)
        return portfolio_df

    # Also compares to existing sp500 returns
    def visualize_portfolio_returns(self, portfolio_df, dt):
        # 8. Visualize Portfolio returns and compare to SP500 returns.
        # Download the returns of SP500
        # TODO: This should be an online CSV
        spy = yf.download(tickers='SPY',
                        start='2015-01-01',
                        end=dt.date.today())

        spy_ret = np.log(spy[['Adj Close']]).diff().dropna().rename({'Adjj Close': 'SPY Buy&Hold'}, axis=1)

        portfolio_df = portfolio_df.merge(spy_ret,
                                        left_index=True,
                                        right_index=True)

        # print(portfolio_df)

        plt.style.use('ggplot')

        portfolio_cumulative_return = np.exp(np.log1p(portfolio_df).cumsum())-1

        # Select the returns up to a given date
        portfolio_cumulative_return[:'2023-09-29'].plot(figsize=(16,6))

        plt.title('Unsupervised Learning Trading Strategy Returns Over Time')
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1))
        plt.ylabel('Return')
        plt.show()
    
gvk_strategy = GKV()
df = gvk_strategy.load_sp500_data()

df = gvk_strategy.calculate_german_klass_vol(df)
df = gvk_strategy.calculate_rsi_indicator(df)
df = gvk_strategy.calculate_bollinger_bands(df)
df['atr'] = df.groupby(level=1, group_keys=False).apply(gvk_strategy.compute_atr)
df['macd'] = df.groupby(level=1, group_keys=False)['adj close'].apply(gvk_strategy.calculate_macd)
df['dollar_volume'] =  (df['adj close']*df['volume'])/1e6
# Think we need to re-calculate the Garman class Volatility??
data, df = gvk_strategy.calculate_five_year_rolling_average(df)
logging.debug('---------------------------------')
logging.debug(data)
logging.debug(df)
logging.debug('---------------------------------')
data = data.groupby(level=1, group_keys=False).apply(gvk_strategy.calculate_returns).dropna()

data = gvk_strategy.download_fama_french_factors_and_calc_rolling_factors_betas(data)

gvk_strategy.visualize_stocks(data)

# portfolio_df = gvk_strategy.form_portfolio(df, data)
# gvk_strategy.visualize_portfolio_returns(portfolio_df)