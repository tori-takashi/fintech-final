import ccxt
import pandas as pd
import numpy as np

import random
from datetime import datetime, timedelta
from time import sleep

from lib.dataset import Dataset
from lib.line_notification import LineNotification

from .tradingbot_base.ohlcv_tradingbot import OHLCV_tradingbot

from .tradingbot_base.trading_bot_backtest import TradingBotBacktest
from .tradingbot_base.trading_bot_real import TradingBotReal

# default_params = {
#    "bot_name" : string, bot name
#    "version" : string version
#    "timeframe": integer, timeframe
#    "close_position_on_do_nothing": bool, close_position_on_do_nothing,
#    "inverse_trading": bool, inverse_trading
#    "random_leverage": bool, for backtest to cpmpare with the efficiency of leverage adjusting
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

    def set_params(self, default_params, specific_params):
        self.default_params = default_params
        self.specific_params = specific_params
        self.combined_params = dict(
            **self.default_params, **self.specific_params)

    def set_helper_libs(self):
        self.dataset_manipulator = Dataset(
            self.db_client, self.exchange_client, self.is_backtest)
        self.ohlcv_tradingbot = OHLCV_tradingbot(
            self.dataset_manipulator, self.default_params, self.specific_params)

        if self.is_backtest:
            self.trading_bot_backtest = TradingBotBacktest(self)
        else:
            self.trading_bot_real = TradingBotReal(self)
            self.line = LineNotification(self.db_client.config_path)

    # need to be override

    def append_specific_param_columns(self):
        return {}
        # return table def_keys
        # {"<column name>" : sqlalchemy column type (like Integer, String, Float....) }

    def calculate_specific_lot(self, row):
        # designate with value [0,1] range
        # 0 is 0%, 1 is 100% and the value is multiplied with default lot in position_lot.py
        return 1  # backtest

    def calculate_specific_leverage(self, row):
        # designate to [0, 100]
        return 1

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

        if ohlcv_df is None:
            self.ohlcv_tradingbot.update_ohlcv()

        if self.is_backtest:
            self.trading_bot_backtest.run(
                ohlcv_df, ohlcv_start_time, ohlcv_end_time, floor_time)

        else:
            self.line.notify(
                {**self.default_params, **self.specific_params}.items())
            self.ohlcv_df = self.ohlcv_tradingbot.get_ohlcv() if ohlcv_df is None else ohlcv_df
            self.trading_bot_real.run()
