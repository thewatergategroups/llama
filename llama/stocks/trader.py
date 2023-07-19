from alpaca.trading.requests import MarketOrderRequest,LimitOrderRequest,GetOrdersRequest,GetAssetsRequest
from alpaca.trading import TradeAccount,TradingClient,Asset,Position
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from ..consts import Settings



class LlamaTrader:
    """Llama is created"""
    def __init__(self,
        client:TradingClient, 
        account:TradeAccount,
        assets:list[Asset], positions:list[Position]
    ):
        self.client = client
        self.account = account
        self.assets = assets
        self.positions = positions
    
    @classmethod
    def create(cls, settings:Settings):
        """Create class with data"""
        client = TradingClient(
            settings.api_key,
            settings.secret_key,
            paper=True
        )
        account = client.get_account()
        
        search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
        assets = client.get_all_assets(search_params)
        positions = client.get_all_positions()
        return cls(client,account,assets,positions)

    def profit(self):
        """Get profit from account data"""
        return float(self.account.equity) - float(self.account.last_equity)

    def get_all_assets(self):
        """get all assets that can be bought"""
        search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
        return self.client.get_all_assets(search_params)

    def place_limit_order(self,symbol:str = "TSLA",limit_price:int = 17000, notional:int= 4000, time_in_force:TimeInForce = TimeInForce.FOK,side:OrderSide = OrderSide.SELL):
        """preparing limit order"""
        limit_order_data = LimitOrderRequest(
                            symbol=symbol,
                            limit_price=limit_price,
                            notional=notional,
                            side=side,
                            time_in_force=time_in_force
                        )

        # Limit order
        return self.client.submit_order(
                        order_data=limit_order_data
                    )


    def place_order(self,symbol:str = "TSLA",time_in_force:TimeInForce = TimeInForce.FOK,side:OrderSide = OrderSide.BUY,quantity:int = 1):
        """place order"""
        market_order_data = MarketOrderRequest(
        symbol=symbol,
        qty=quantity,
        side=side,
        time_in_force=time_in_force
    )
        return self.client.submit_order(market_order_data)

    def get_all_positions(self):
        """Get positions"""
        return self.client.get_all_positions()

    def close_position(self,symbol:str):
        """close symbol on stock"""
        self.client.close_position(symbol)

    def cancel_order(self,id_:str):
        """cancel order"""
        return self.client.cancel_order_by_id(id_)

    def get_all_orders(self,side:OrderSide = OrderSide.SELL):
        """get all orders I have placed"""
        request_params = GetOrdersRequest(
                    status='all',
                    side=side
        )
        return self.client.get_orders(filter=request_params)