import ccxt
from datetime import datetime, timedelta

from lib.pandamex import PandaMex


class TradingBot:
    def __init__(self, exchange_client, is_backtest=False):
        self.is_backtest = is_backtest

        self.exchange_client = exchange_client
        self.client = exchange_client.client

        self.transaction_fee_by_order = 0.0005
        self.lot = 1
        # do not close opening position after n ticks.
        self.close_condition = 0
        self.timeframe = "1m"

    def run(self):
        self.ohlcv_df = self.init_ohlcv_data()
        self.calculate_metrics()
        self.calculate_sign_backtest()

    def calculate_metrics(self):
        pass
        # need to override

    def calculate_sign(self):
        return "signal"
        # return "buy"
        # return "sell"
        # return "do_nothing"

    def calculate_sign_backtest(self):
        pass
        # return dataframe with signal

    def init_ohlcv_data(self, start_time=datetime.now() - timedelta(days=30), end_time=datetime.now()):
        self.start_time = start_time
        self.end_time = end_time

        self.stock_duration = end_time - start_time

        if self.exchange_client.name == "bitmex":
            ohlcv_df = PandaMex(self.client).fetch_ohlcv(
                timeframe=self.timeframe, start_time=self.start_time, end_time=self.end_time)
            # fetch ohlcv data
            return PandaMex.to_timestamp(ohlcv_df)
