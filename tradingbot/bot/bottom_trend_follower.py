# bottom trend detection and follow with MACD
import pandas as pd
from sqlalchemy import Column, Integer

from bot.trading_bot import TradingBot
from technical_analysis.MACD import TechnicalAnalysisMACD


class BottomTrendFollow(TradingBot):
    def __init__(self, exchange_client, db_client, default_params=None, specific_params=None, is_backtest=False):
        # default hyper parameters
        # please follow this order to name on real environment
        self.default_params = {
            "bot_name": "bottom_trend_follow",
            "version": "v1.0.0",
            "timeframe": 60,
            "close_position_on_do_nothing": True,
            "inverse_trading": False
        }

        # specific params
        self.bottom_trend_tick = 12
        self.middle_trend_tick = 6
        self.top_trend_tick = 3

        self.specific_params = {
            "bottom_trend_tick": self.bottom_trend_tick,
            "middle_trend_tick": self.middle_trend_tick,
            "top_trend_tick": self.top_trend_tick
        }

        if default_params is not None and specific_params is not None:
            self.default_params = default_params
            self.specific_params = specific_params
        super().__init__(exchange_client=exchange_client, db_client=db_client, default_params=self.default_params,
                         specific_params=self.specific_params, is_backtest=is_backtest)

    def calculate_lot(self, row):
        return 60  # USD
        # if you need, you can override
        # default is invest all that you have

    def append_specific_params_column(self, table_def):
        table_def.append_column(Column("bottom_trend_tick", Integer))
        table_def.append_column(Column("middle_trend_tick", Integer))
        table_def.append_column(Column("top_trend_tick", Integer))
        return table_def

    def set_trend_column(self):
        specific_params_values = list(self.specific_params.values())
        self.bottom_trend_col = "ema_" + \
            str(specific_params_values[0]) + "_trend"
        self.middle_trend_col = "ema_" + \
            str(specific_params_values[1]) + "_trend"
        self.top_trend_col = "ema_" + str(specific_params_values[2]) + "_trend"

    def calculate_metrics(self, df):
        self.set_trend_column()

        ohlcv_with_metrics = df
        ta_ema = TechnicalAnalysisMACD(ohlcv_with_metrics)

        for tick in list(self.specific_params.values()):
            col = "ema_" + str(tick)
            diff_col = col + "_diff"
            trend_col = col + "_trend"

            ohlcv_with_metrics[col] = ta_ema.append_ema_close(tick)

            # percentage of ema moving
            ohlcv_with_metrics[diff_col] = ohlcv_with_metrics[col].diff() / \
                ohlcv_with_metrics[col] * 100
            # trend of ema moving
            ohlcv_with_metrics.loc[:, trend_col] = ohlcv_with_metrics[diff_col].map(
                self.create_trend_col)

        return ohlcv_with_metrics

    def create_trend_col(self, diff):
        if diff > 0:
            return "uptrend"
        else:
            return "downtrend"

    def calculate_signals(self, df):
        # for real environment
        # [FIXME] almost copy and paste

        bottom = df[self.bottom_trend_col]
        middle = df[self.middle_trend_col]
        top = df[self.top_trend_col]
        df.loc[((bottom == "uptrend")
                & (middle == "uptrend")
                & (top == "uptrend")), "signal"] = "buy"
        df.loc[((bottom == "downtrend")
                & (middle == "downtrend")
                & (top == "downtrend")), "signal"] = "sell"
        df["signal"].fillna("do_nothing", inplace=True)
        return df
