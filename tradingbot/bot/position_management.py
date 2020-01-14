from datetime import datetime
from time import sleep

from .position import Position

class PositionManagement:
    def __init__(self, tradingbot):
        # current holding position
        self.position = None

        # prevent from pushing same order in one minutes
        self.processed_flag = False

        self.tradingbot = tradingbot

    def execute_with_time(self, interval=0.5):
        while True:
            # [FIXME] corner case, if the timeframe couldn't divide by 60, it's wrong behavior
            if (self.processed_flag is not True) and (datetime.now().minute % self.tradingbot.default_params["timeframe"] == 0):
                    break
            else:
                self.processed_flag = False
            sleep(interval)

    def signal_judge(self, row):
        if self.position is None:
            return self.open_position if row.signal == "buy" or row.signal == "sell" else None
        else:
            order_type = self.position.order_type
            inverse_trading = self.tradingbot.default_params["inverse_trading"]
            close_position_on_do_nothing = self.tradingbot.default_params["close_position_on_do_nothing"]

            if (row.signal == "buy"  and ((order_type == "long"  and inverse_trading) or (order_type == "short" and not inverse_trading))) or\
               (row.signal == "sell" and ((order_type == "short" and inverse_trading) or (order_type == "long"  and not inverse_trading))) or\
               (row.signal == "do_nothing" and close_position_on_do_nothing):
            
                self.close_position(row)
                return None

    def open_position(self, row):

        lot = self.calculate_lot(row) # fixed value
        leverage = self.calculate_leverage(row)  # fixed value

        # [FIXME] symbol is hardcoded, only for bitmex

        self.position = Position(row, self.tradingbot.is_backtest)

        self.position.current_balance = self.current_balance
        self.position.lot = lot
        self.position.leverage = leverage
        self.position.order_method = "limit" # limit or market order
        self.position.order_type = self.get_order_type(row)

        self.execute_open_order(row)

    def get_order_type(self, row):
        inverse_trading = self.tradingbot.default_params["inverse_trading"]

        if row.signal == "buy":
            return "long" if not inverse_trading else "short"
        elif row.signal == "sell":
            return "short" if not inverse_trading else "long"

    def execute_open_order(self, row):
        if self.tradingbot.is_backtest:
            self.position.open_position()
            return self.position
        else:
            self.tradingbot.exchange_client.client.private_post_position_leverage({"symbol": "XBTUSD", "leverage": str(self.position.leverage)})
            self.position = self.create_order(row)
            # discard failed opening orders
            return self.position if self.position is not None and self.position.order_status == "open" else None


    def close_position(self, row):
        if self.tradingbot.is_backtest:
            self.position.close_position(row)
            self.current_balance = self.position.current_balance
            return self.position
        else:
            self.create_order(row)

    def clean_position_after_create_backtest_logs(self):
        self.position = None

    