from sqlalchemy.orm import Mapped, mapped_column
import numpy as np
import pandas_ta
import pandas as pd

from trekkers import BaseSql

class Bars(BaseSql):
    __tablename__ = "bars"
    __table_args__ = {"schema": "llama"}

    symbol: Mapped[str] = mapped_column(primary_key=True)
    timeframe: Mapped[str] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)
    open: Mapped[float]
    close: Mapped[float]
    high: Mapped[float]
    low: Mapped[float]
    trade_count: Mapped[int]
    vwap: Mapped[float]
    volume: Mapped[int]

class GKV(Bars):

    df = [] # TODO: Insert data here, ideally as a dataFrame
    
    def load_sp500_data():
        sp500 = pd.read_html('sp500.html')[0]
        print(sp500)
        sp500['Symbol'] = sp500['Symbol'].str.replace('.', '-')
        # symbols_list = sp500['Symbol'].unique().tolist()
        end_date = '2023-09-27'

        df = pd.read_csv("sp500-yf-1.csv", index_col=0, encoding='utf-8-sig')
        return df
    def download_data_from_source():
        import requests
        import pandas as pd
        import yfinance as yf
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        response = requests.get(url)
        with open('sp500.html', 'w') as file:
            file.write(response.text)

            sp500 = pd.read_html(response.text)[0]
            
            # sp500 = response.text[0]
            sp500['Symbol'] = sp500['Symbol'].str.replace('.', '-')
            symbols_list = sp500['Symbol'].unique().tolist()
            
            end_date = '2024-03-30'
            # Exactly 1 year before start of the data
            start_date = pd.to_datetime(end_date)-pd.DateOffset(365*8)
            
            df = yf.download(tickers=symbols_list,
                             start=start_date,
                             end=end_date)
            df.to_csv("sp500-yf-2.csv")
            return df


    def calculate_german_klass_vol(df):
        df['garman_klass_vol'] = ((np.log(df['high'])-np.log(df['low']))**2)/2-(2*np.log(2)-1)*((np.log(df['adj close'])-np.log(df['open']))**2)

        # RSI indicator
    def calculate_rsi_indicator(df):
        df['rsi'] = df.groupby(level=1)['adj close'].transform(lambda x: pandas_ta.rsi(close=x, length=20))
        return df
    
    # Bollinger Bands
    def calculate_bollinger_bands(df):
        df['bb_low'] = df.groupby(level=1)['adj close'].transform(lambda x: pandas_ta.bbands(close=np.log1p(x), length=20).iloc[:,0])

        df['bb_mid'] = df.groupby(level=1)['adj close'].transform(lambda x: pandas_ta.bbands(close=np.log1p(x), length=20).iloc[:,1])

        df['bb_high'] = df.groupby(level=1)['adj close'].transform(lambda x: pandas_ta.bbands(close=np.log1p(x), length=20).iloc[:,2])
        return df
    
    # MACD
    def calculate_macd(close):
        macd = pandas_ta.macd(close=close, length=20).iloc[:,0]
        return macd.sub(macd.mean()).div(macd.std())

    # ATR 
    # Exactly what stock_data is this expecting??
    def calculate_atr(stock_data):
        atr = pandas_ta.atr(
            high=stock_data['high'],
            low=stock_data['low'],
            close=stock_data['close'],
            length=14
        )
        
        normalized_atr = atr.sub(atr.mean()).div(atr.std())
        # can be applied by doing df['atr'] = df.groupby(level=1, group_keys=False).apply(compute_atr)
        return normalized_atr

    def execute_strategy_1():
        pass
    
        # Calculate 5-year rolling average of dollar volume for each stocks before filtering
    def foo(df):
        last_cols = [c for c in df.columns.unique(0) if c not in ['dollar_volume', 'volume', 'open', 'high', 'low','close']]

        data = (pd.concat([df.unstack('ticker')['dollar_volume'].resample('M').mean().stack('ticker').to_frame('dollar_volume'),
                           df.unstack()[last_cols].resample('M').last().stack('ticker')],
                          axis=1)).dropna()
        
        data['dollar_volume'] = (data.loc[: 'dollar_volume'].unstack('ticker').rolling(5*12, min_periods=12).mean().stack())
        data['dollar_vol_rank'] = (data.groupby('date')['dollar_volume'].rank(ascending=False))
        data = data[data['dollar_vol_rank']<150].drop(['dollar_volume', 'dollar_vol_rank'], axis=1)
        
        return [data df]

    
    # Download Fama-French Factors and Calculate Rolling Factor Betas.
    # * We will introduce the Fama—French data to estimate the exposure of assets to common risk factors using linear regression.
    # * The five Fama—French factors, namely market risk, size, value, operating profitability, and investment have been shown empirically to explainasset returns and are commonly used to assess the risk/return profile of portfolios. Hence, it is natural to include past factor exposures asfinancial features in models.
    # * We can access the historical factor returns using the pandas-datareader and estimate historical exposures using the RollingOLS rolling linearregression. 
    def startegy_2():
        factor_data = web.DataReader('F-F_Research_Data_5_Factors_2x3',
                                    'famafrench',
                                    start='2010')[0].drop('RF', axis=1)
        
        #  FIx index
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
        betas = (factor_data.groupby(level=1, group_keys=False)
                .apply(lambda x: RollingOLS(endog=x['return_1m'],
                                            exog=sm.add_constant(x.drop(['return_1m'], axis=1)),
                                            window=min(24, x.shape[0]),
                                            min_nobs=len(x.columns)+1)
                .fit(params_only=True)
                #  .params
                .drop('const', axis=1)))


        # Join the rolling factors data to the main features dataframe.

        factors = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']
        data = (data.join(betas.groupby('ticker').shift()))

        data.loc[: factors] = data.groupby('ticker', group_keys=False)[factors].apply(lambda x: x.fillna(x.mean()))
        data = data.drop('adj close', axis=1)
        data = data.dropna()
        data.info()

