# import alpaca.data.requests
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import StockBarsRequest
from datetime import datetime
from stocks.technical import GKV

def main():
    print("Hello World!")
    API_KEY='PKCTFA47WCR9XYAZJ6C8'
    SECRET_KEY = 'jOHa3DTjOcOnezvKDoFjSbikcl2RDWCXwFg8PLF1'

    trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

    # search for US equities
    # search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)

    # # assets = trading_client.get_all_assets(search_params)
    # # print(assets)

    # aapl_asset = trading_client.get_asset('AAPL')

    # if aapl_asset.tradable:
    #     print('We can trade AAPL.')

    # print(aapl_asset)
    # NVDA
    stock_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

    req_params = StockBarsRequest( 
        symbol_or_symbols=["NVDA"],
        timeframe=TimeFrame.Day,
        start=datetime(2022, 9, 1),
        end=datetime(2023, 9, 7)
        )

    nvidia_df= stock_client.get_stock_bars(req_params)

    print(nvidia_df.df)
    print("===========================================================================================================================")
    print("===========================================================================================================================")

    gvk_client = GKV()

    df = nvidia_df.df
    df_gkl = gvk_client.calculate_garman_klass_vol(df)

    print(df_gkl)


    # print(nvidia_df)
    # for symbol in symbols:
    #     times = self.identify_missing_bars(symbol, time_frame, start_time, end_time)
    #     for starttime, endtime in times:
    #         print(
    #             "getting bars for %s between %s and %s with timeframe of %s",
    #             symbol,
    #             starttime,
    #             endtime,
    #             time_frame.value,
    #         )
    #         request_params = StockBarsRequest(
    #             symbol_or_symbols=[symbol],
    #             timeframe=time_frame,
    #             start=starttime.isoformat(),
    #             end=endtime.isoformat(),
    #         )
    #         bars: BarSet = self.client.get_stock_bars(request_params)
    #         # bars = self.fill_bars(bars, start_time, end_time)
    #         if bars.data:
    #             self.insert_bars(bars, time_frame)



if __name__ == "__main__":
    main()