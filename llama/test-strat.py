# import alpaca.data.requests
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import StockBarsRequest
from datetime import datetime
import llama.technical as tt
from database.models import Bars

API_KEY='PKCTFA47WCR9XYAZJ6C8'
SECRET_KEY = 'jOHa3DTjOcOnezvKDoFjSbikcl2RDWCXwFg8PLF1'

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
gvk_client = tt.GKV()

# NVDIA
stock_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

nvidia_full_df_req = StockBarsRequest( 
    symbol_or_symbols=["NVDA"],
    timeframe=TimeFrame.Day,
    start=datetime(2022, 9, 1),
    end=datetime(2023, 9, 7)
    )

# nvidia_adj_df_req = StockBarsRequest(
#     symbol_or_symbols=["NVDA"],
#     timeframe=TimeFrame.Day,
#     start=datetime(2022, 9, 1),
#     end=datetime(2023, 9, 7),
#     adjustment='split'
#     )

print(nvidia_full_df_req)

# nvidia_df = stock_client.get_stock_bars(nvidia_full_df_req)
# nvidia_adj_df= stock_client.get_stock_bars(nvidia_adj_df_req)

# working_df = nvidia_df.df
# working_df['adj close'] = nvidia_adj_df.df['close'].to_numpy()

# working_df = gvk_client.calculate_garman_klass_vol(working_df)
# working_df = gvk_client.calculate_rsi_indicator(working_df)
# working_df = gvk_client.calculate_bollinger_bands(working_df)
# # working_df['atr'] = working_df.groupby(level=0, group_keys=False).apply(gvk_client.calculate_atr) # ValueError: Cannot set a DataFrame with multiple columns to the single column atr
# working_df['macd'] = working_df.groupby(level=0, group_keys=False)['adj close'].apply(gvk_client.calculate_macd)
# working_df['dollar_volume'] =  (working_df['adj close'] * working_df['volume'])/1e6

# print(working_df)
