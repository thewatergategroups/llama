# import alpaca.data.requests
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import StockBarsRequest
from datetime import datetime
import llama.technical as tt

API_KEY=''
SECRET_KEY = ''

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# search for US equities
# search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)

# # assets = trading_client.get_all_assets(search_params)
# # print(assets)

# aapl_asset = trading_client.get_asset('AAPL')

# if aapl_asset.tradable:
#     print('We can trade AAPL.')

# print(aapl_asset)
# NVDIA
stock_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

nvidia_full_df_req = StockBarsRequest( 
    symbol_or_symbols=["NVDA"],
    timeframe=TimeFrame.Day,
    start=datetime(2022, 9, 1),
    end=datetime(2023, 9, 7)
    )

nvidia_adj_df_req = StockBarsRequest(
    symbol_or_symbols=["NVDA"],
    timeframe=TimeFrame.Day,
    start=datetime(2022, 9, 1),
    end=datetime(2023, 9, 7),
    adjustment='split'
    )

nvidia_df = stock_client.get_stock_bars(nvidia_full_df_req)
nvidia_adj_df= stock_client.get_stock_bars(nvidia_adj_df_req)

# nvidia_df= stock_client.get_stock_bars(nvidia_full_df_req)
working_df = nvidia_df.df

# print(nvidia_df.df)
# print(nvidia_adj_df.df['close'])
# nvidia_df.df['adj close'] =  nvidia_df.df + nvidia_adj_df.df['close']
working_df['adj close'] = nvidia_adj_df.df['close'].to_numpy()
# nvidia_adj_df. = nvidia_adj_df.df.join(nvidia_adj_df.df['close'])
print("===========================================================================================================================")
print("===========================================================================================================================")
print(working_df)

gvk_client = tt.GKV()
working_df = gvk_client.calculate_garman_klass_vol(working_df)
working_df = gvk_client.calculate_rsi_indicator(working_df)
print("RSI::")
# print(working_df)
working_df = gvk_client.calculate_bollinger_bands(working_df)
# working_df['atr'] = working_df.groupby(level=0, group_keys=False).apply(gvk_client.calculate_atr) # ValueError: Cannot set a DataFrame with multiple columns to the single column atr
working_df['macd'] = working_df.groupby(level=0, group_keys=False)['adj close'].apply(gvk_client.calculate_macd)
working_df['dollar_volume'] =  (working_df['adj close'] * working_df['volume'])/1e6

print(working_df)
