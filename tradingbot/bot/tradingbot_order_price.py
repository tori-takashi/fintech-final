class TradingBotOrderPrice:
    def __init__(self, tradingbot):
        self.tradingbot = tradingbot

    def fetch_best_price(self, position):
        # open and close (long, short)
        
        # try open and limit order   => (bid, ask)
        # try close and market order => (bid, ask)

        # try open and market order  => (ask, bid)
        # try close and limit order  => (ask, bid)
        order_status = position.order_status
        order_method = position.order_method
        order_type   = position.order_type

        if (order_status == "pass" and order_method == "maker") or \
           (order_status == "open" and order_method == "taker"):
            price_type = "bid" if order_type == "long" else "ask"

        elif (order_status == "open" and order_method == "maker") or \
             (order_status == "pass" and order_method == "taker"):
             price_type = "ask" if order_type == "long" else "bid"

        return self.tradingbot.exchange_client.client.fetch_ticker(position.asset_name)[price_type]

    def calculate_order_price(self, position):
        order_status = position.order_status
        order_type = position.order_type
        best_price = self.fetch_best_price(position)
        
        # slippage =  0.5 # taker
        slippage = -0.5   # maker

        if (order_status == "pass" and order_type == "long") or (order_status == "open" and order_type == "short"):
            order_price = best_price + slippage
        elif (order_status == "pass" and order_type == "short") or (order_status == "open" and order_type == "long"):
            order_price = best_price - slippage
                
        order_price_base = round(order_price)
        order_price_decimal = order_price - order_price_base
        order_price = order_price_base if order_price_decimal < 0.5 else order_price_base + 0.5

        return order_price

