import ccxt
from datetime import datetime, timedelta

from lib.pandamex import PandaMex


class TradingBot:
    def __init__(self, exchange_client, is_backtest=False):
        self.is_backtest = is_backtest

        self.exchange_client = exchange_client
        self.client = exchange_client.client

        self.lot = 1
        # do not close opening position after n ticks.
        self.close_condition = 0
        self.timeframe = "1m"

    def run(self):
        self.ohlcv_df = self.init_ohlcv_data()
        self.calculate_metrics()
        if self.is_backtest:
            self.calculate_sign_backtest()
            print(self.ohlcv_df)
            self.run_backtest()

    def calculate_lot(self):
        return 1

    def calculate_metrics(self):
        pass
        # need to override

    def calculate_sign(self):
        return "signal"
        # need to override
        # return ["buy", "sell", "do_nothing"]

    def calculate_sign_backtest(self):
        pass
        # need to override
        # return dataframe with ["buy", "sell", "do_nothing"]

    def init_ohlcv_data(self, start_time=datetime.now() - timedelta(days=30), end_time=datetime.now()):
        self.start_time = start_time
        self.end_time = end_time

        self.stock_duration = end_time - start_time

        if self.exchange_client.name == "bitmex":
            ohlcv_df = PandaMex(self.client).fetch_ohlcv(
                timeframe=self.timeframe, start_time=self.start_time, end_time=self.end_time)
            # fetch ohlcv data
            return PandaMex.to_timestamp(ohlcv_df)

    def run_backtest(self, close_in_do_nothing=True):
        # [close_in_do_nothing option]
        # True  => close position when the [buy/sell] signal change to the [do_nothing/opposite] signal
        # False => close position when the [buy/sell] signal change to the opposite signal

        # refer to signal then calculate
        # having only one order

        position = None
        contain_signal_df = self.ohlcv_df

        closed_positions = []

        for row in contain_signal_df.itertuples():
            print(str(row.timestamp) + " : open price: $" +
                  str(row.open) + " close price: $" + str(row.close))

            if position is not None and row.signal == "buy":
                if position.order_type == "long":
                    # still holding
                    pass
                elif position is not None and position.order_type == "short":
                    # close position
                    position.close_position(row)
                    position = None
                else:  # do_nothing
                    # open position
                    lot = self.calculate_lot()
                    position = OrderPosition(
                        row, "long", lot, is_backtest=True)

            elif row.signal == "sell":
                if position is not None and position.order_type == "long":
                    position.close_position(row)
                    position = None
                elif position is not None and position.order_type == "short":
                    # still holding
                    pass
                else:
                    # open position
                    lot = self.calculate_lot()
                    position = OrderPosition(
                        row, "short", lot, is_backtest=True)

            elif row.signal == "do_nothing":
                if close_in_do_nothing:
                    if position is not None and position.order_type == "long":
                        # close position
                        position.close_position(row)
                        position = None
                    elif position is not None and position.order_type == "short":
                        # close position
                        position.close_position(row)
                        position = None


class OrderPosition:
    def __init__(self, row, order_type, lot, is_backtest=False):
        self.transaction_fee_by_order = 0.0005
        self.status = "open"

        self.order_type = order_type
        # order_type = ["long", "short"]
        self.is_backtest = is_backtest
        self.lot = lot

        self.entry_price = row.close
        self.close_price = 0

        self.open_position()

    def open_position(self):
        print("Entry" + self.order_type + " at $" + str(self.entry_price))
        if self.is_backtest:
            pass

    def close_position(self, row_execution):
        self.close_price = row_execution.close
        print("Close long at $" + str(self.close_price))

        transaction_cost = self.close_price * self.transaction_fee_by_order

        if self.order_type == "long":
            self.profit = (self.close_price -
                           self.entry_price) - transaction_cost
        elif self.order_type == "short":
            self.profit = (self.entry_price -
                           self.close_price) - transaction_cost

        if self.profit > 0:
            print("$" + str(self.profit) + " profit")
        else:
            print("$" + str(self.profit) + " loss")

        self.status = "closed"
        if self.is_backtest:
            pass
