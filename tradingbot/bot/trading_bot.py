import ccxt
import pandas as pd
import numpy as np

import random
from datetime import datetime, timedelta
from time import sleep
from ccxt import ExchangeNotAvailable, RequestTimeout, BaseError

from lib.pandamex import PandaMex
from lib.dataset import Dataset
from lib.line_notification import LineNotification

from model.backtest_management import BacktestManagement
from model.backtest_summary import BacktestSummary
from model.backtest_transaction_log import BacktestTransactionLog

from machine_learning.random_forest_prediction import RandomForestPredict30min

from .position import Position
from .position_management import PositionManagement
from .ohlcv_tradingbot import OHLCV_tradingbot
from .tradingbot_order_price import TradingBotOrderPrice

from .trading_bot_backtest import TradingBotBacktest

        # default_params = {
        #    "bot_name" : string, bot name
        #    "version" : string version
        #    "timeframe": integer, timeframe
        #    "close_position_on_do_nothing": bool, close_position_on_do_nothing,
        #    "inverse_trading": bool, inverse_trading
        #    "random_forest_leverage_adjust"
        # }

class TradingBot:
    def __init__(self, default_params, specific_params, db_client, exchange_client=None, is_backtest=False):
        # initialize status and settings of bot.
        # if you try backtest, db_client is in need.
        self.is_backtest = is_backtest

        self.exchange_client = exchange_client
        self.db_client = db_client

        self.set_params(default_params, specific_params)
        self.set_helper_libs()

        self.random_leverage_only_backtest = False
        self.random_forest_predict_30min = RandomForestPredict30min()

        self.initial_balance = 100  # BTC
        self.account_currency = "USD"
        
    def set_params(self, default_params, specific_params):
        self.default_params = default_params
        self.specific_params = specific_params
        self.combined_params = dict(**self.default_params, **self.specific_params)

    def set_helper_libs(self):
        self.dataset_manipulator = Dataset(self.db_client, self.exchange_client, self.is_backtest)
        self.ohlcv_tradingbot = OHLCV_tradingbot(self.dataset_manipulator, self.default_params, self.specific_params)
        self.position_management = PositionManagement(self)

        if self.is_backtest:
            self.trading_bot_backtest = TradingBotBacktest(self)
        else:
            self.line = LineNotification(self.db_client.config_path)


    ###### need to be override
    def append_specific_params_columns(self):
        return {}
        # return table def_keys
        # {"<column name>" : sqlalchemy column type (like Integer, String, Float....) }

    def calculate_lot(self, row):
        # {FIXME} backtest is the percentage but real is the real USD number
        return 1 # backtest
        #return 60 # real
        # default is invest all that you have

    def calculate_metrics(self, df):
        return df

    def calculate_signals(self, df):
        return df
        # return ["buy", "sell", "do_nothing"]
    #####

    def run(self, ohlcv_df=None, ohlcv_start_time=datetime.now() - timedelta(days=90), ohlcv_end_time=datetime.now(),
            floor_time=True):
        self.processed_flag = False

        self.ohlcv_tradingbot.ohlcv_start_time = ohlcv_start_time
        self.ohlcv_tradingbot.ohlcv_end_time = ohlcv_end_time

        self.ohlcv_tradingbot.update_ohlcv()
        
        if self.is_backtest:
            self.trading_bot_backtest.run_backtest(ohlcv_df, ohlcv_start_time, ohlcv_end_time, floor_time)

        else:
            self.line.notify({**self.default_params, **self.specific_params}.items())
            self.ohlcv_df = self.ohlcv_tradingbot.get_ohlcv() if ohlcv_df is None else ohlcv_df
            # for real environment
            # [FIXME] having only one position 

            while True:
                try:
                    self.trade_loop_for_real(ohlcv_df)
                except ExchangeNotAvailable:
                    self.line.notify("Exchange Not Available Error, Retry after 15 seconds")
                    sleep(15)
                    self.line.notify("loop restart...")
                except RequestTimeout:
                    self.line.notify("Request Time out, Retry after 15 seconds")
                    sleep(15)
                    self.line.notify("loop restart...")
                except BaseError:                    
                    self.line.notify("Unknown Error, Retry after 15 seconds")
                    sleep(15)
                    self.line.notify("loop restart...")

    def trade_loop_for_real(self, ohlcv_df):
        self.current_balance = self.exchange_client.client.fetch_balance()["BTC"]["total"]
        self.line.notify("trade loop start")

        while True:
            self.position_management.execute_with_time()

            latest_row = self.ohlcv_tradingbot.generate_latest_row(self.calculate_metrics, self.calculate_signals)
            self.line.notify(latest_row)

            self.position = self.position_management.signal_judge(latest_row)
            self.processed_flag = True

    def bulk_insert(self):
        self.db_client.session.commit()

    def reset_backtest_result_with_params(self, default_params, specific_params):
        # for loop and serach optimal metrics value
        self.ohlcv_with_metrics = None
        self.ohlcv_with_signals = None
        self.closed_positions_df = None

        self.default_params = default_params
        self.specific_params = specific_params
        self.combined_params = dict(**self.default_params, **self.specific_params)

    def set_random_leverage_only_backtest(self, random_leverage):
        self.random_leverage_only_backtest = random_leverage

    def calculate_leverage(self, row, leverage=1):
        # if you need, you can override
        leverage = leverage
        if self.is_backtest and self.random_leverage_only_backtest:
            return self.random_leverage_test([1,2])

        predict_seed = self.predict_seed_generator(row)
        if self.default_params["random_forest_leverage_adjust"]:
            random_forest_prediction = self.random_forest_predict_30min.binaryClassificationInThirtyMinutes(predict_seed)
            if self.default_params["inverse_trading"]:
                if (row.signal == "buy" and random_forest_prediction == "downtrend") or\
                        (row.signal == "sell" and random_forest_prediction == "uptrend"):
                    leverage *= 2
            else:
                if (row.signal == "buy" and random_forest_prediction == "uptrend") or\
                        (row.signal == "sell" and random_forest_prediction == "downtrend"):
                    leverage *= 2

        return leverage

    def random_leverage_test(self, samples):
        return random.choice(samples) 

    def random_forest_predict(self, predict_seed):
        prediction = int(self.random_forest_predict_30min.binaryClassificationInThirtyMinutes(
            predict_seed[["open", "high", "low", "close", "volume"]]))
        return "downtrend" if prediction == 0 else "uptrend"

    def predict_seed_generator(self, row, data_range=75):
        if self.is_backtest:
            entry_time = pd.to_datetime(row.Index).to_pydatetime()
        else:
            entry_time = pd.to_datetime(row.name).to_pydatetime()
        predict_seed = self.dataset_manipulator.get_ohlcv(timeframe=1,
            start_time=entry_time - timedelta(minutes=75), end_time=entry_time, round=False)
        return predict_seed
