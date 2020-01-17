class OrderPriceCalculator:
    def __init__(self, tradingbot):
        self.tradingbot = tradingbot

    def fetch_best_price(self, position):
        bid_ask = self.convert_bid_ask(position)
        best_price = self.tradingbot.exchange_client.client.fetch_ticker(
            position.asset_name)[bid_ask]
        return best_price

    def convert_bid_ask(self, position):
        # try open and limit order   => (bid, ask)
        # try close and market order => (bid, ask)

        # try open and market order  => (ask, bid)
        # try close and limit order  => (ask, bid)
        order_status = position.order_status
        order_method = position.order_method
        order_type = position.order_type

        if (order_status == "pass" and order_method == "limit") or \
           (order_status == "open" and order_method == "market"):
            return "bid" if order_type == "long" else "ask"

        elif (order_status == "open" and order_method == "limit") or \
             (order_status == "pass" and order_method == "market"):
            return "ask" if order_type == "long" else "bid"

    def calculate_order_price(self, position, order_method):
        order_status = position.order_status
        order_type = position.order_type
        best_price = self.fetch_best_price(position)

        if order_method == "limit":
            slippage = -0.5   # maker
        elif order_method == "market":
            slippage = 0.5   # taker

        if (order_status == "pass" and order_type == "long") or (order_status == "open" and order_type == "long"):
            order_price = best_price + slippage
        elif (order_status == "pass" and order_type == "short") or (order_status == "open" and order_type == "short"):
            order_price = best_price - slippage

        order_price_base = round(order_price)
        order_price_decimal = order_price - order_price_base
        order_price = order_price_base if order_price_decimal < 0.5 else order_price_base + 0.5

        return order_price
