import pandas as pd
import pathlib
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer

import talib as ta

from bot.trading_bot import TradingBot


class BasicBreakout():
    def __init__(self, exchange_client, db_client, default_params=None, specific_params=None, is_backtest=False):
        self.default_params = {
            "bot_name": "basic_breakout",
            "version": "v1.0.0",
            "timeframe": 60,
            "close_position_on_do_nothing": False,
            "inverse_trading": False,
            "random_leverage": False,
            "random_forest_leverage_adjust": False
        }

        self.system1_entry_timeperiod = 10
        self.system1_exit_timeperiod = 20

        self.specific_params = {
            "system1_entry_timeperiod": self.system1_entry_timeperiod,
            "system1_exit_timeperiod": self.system1_exit_timeperiod
        }

        if default_params is not None and specific_params is not None:
            self.default_params = default_params
            self.specific_params = specific_params

        super().__init__(exchange_client=exchange_client, db_client=db_client, default_params=self.default_params,
                         specific_params=self.specific_params, is_backtest=is_backtest)

    def calculate_specific_lot(self, row):
        return 1  # USD

    def calculate_specific_leverage(self, row):
        return 1  # x

    def append_specific_param_columns(self):
        # return table def_keys
        # {"<column name>" : sqlalchemy column type (like Integer, String, Float....) }
        table_def_keys = {
            "system1_entry_timeperiod": Integer,
            "system1_exit_timeperiod": Integer,
        }
        return table_def_keys

    def calculate_metrics(self, df):
        ohlcv_with_metrics = df

        ohlcv_with_metrics["system1_entry_atr"] = ta.ATR(
            df["high"], df["low"], df["close"], timeperiod=self.system1_entry_timeperiod)
        ohlcv_with_metrics["system1_exit_atr"] = ta.ATR(
            df["high"], df["low"], df["close"], timeperiod=self.system1_exit_timeperiod)

        ohlcv_with_metrics["system1_entry_high"] = ohlcv_with_metrics["high"].rolling(
            self.system1_entry_timeperiod).max()
        ohlcv_with_metrics["system1_entry_low"] = ohlcv_with_metrics["low"].rolling(
            self.system1_entry_timeperiod).min()
        ohlcv_with_metrics["system1_exit_from_long"] = ohlcv_with_metrics["low"].rolling(
            self.system1_exit_timeperiod).min()
        ohlcv_with_metrics["system1_exit_from_short"] = ohlcv_with_metrics["high"].rolling(
            self.system1_exit_timeperiod).max()

        return ohlcv_with_metrics

    def calculate_signals(self, df):
        #df.loc[None, "signal"] = "buy"
        #df.loc[None, "signal"] = "sell"
        #df["signal"].fillna("do_nothing", inplace=True)
        return df
