# bottom trend detection and follow with MACD
import pandas as pd
from sqlalchemy import Column, Integer

from bot.trading_bot import TradingBot
from technical_analysis.MACD import TechnicalAnalysisMACD


class BottomTrendFollow(TradingBot):
    def __init__(self, exchange_client, db_client, is_backtest=False):
        # default hyper parameters
        self.default_params = {
            "bot_name": "bottom_trend_follow",
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

        super().__init__(exchange_client=exchange_client, db_client=db_client, default_params=self.default_params,
                         specific_params=self.specific_params, is_backtest=is_backtest)

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

    def calculate_metrics_for_backtest(self):
        self.set_trend_column()

        ohlcv_with_metrics = self.ohlcv_df
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
            ohlcv_with_metrics.loc[(ohlcv_with_metrics[diff_col] > 0),
                                   trend_col] = "uptrend"
            ohlcv_with_metrics.loc[~(ohlcv_with_metrics[diff_col] > 0),
                                   trend_col] = "downtrend"
        return ohlcv_with_metrics

    def calculate_sign(self, row):
        if (row[self.bottom_trend_col] == "uptrend"
            and row[self.middle_trend_col] == "uptrend"
                and row[self.top_trend_col] == "uptrend"):
            return "buy"
        elif (row[self.bottom_trend_col] == "downtrend"
              and row[self.middle_trend_col] == "downtrend"
                and row[self.top_trend_col] == "downtrend"):
            return "sell"
        else:
            return "do_nothing"

    def calculate_signs_for_backtest(self):
        self.ohlcv_df.loc[((self.ohlcv_df[self.bottom_trend_col] == "uptrend")
                           & (self.ohlcv_df[self.middle_trend_col] == "uptrend")
                           & (self.ohlcv_df[self.top_trend_col] == "uptrend")), "signal"] = "buy"
        self.ohlcv_df.loc[((self.ohlcv_df[self.bottom_trend_col] == "downtrend")
                           & (self.ohlcv_df[self.middle_trend_col] == "downtrend")
                           & (self.ohlcv_df[self.top_trend_col] == "downtrend")), "signal"] = "sell"
        self.ohlcv_df["signal"] = self.ohlcv_df["signal"].fillna("do_nothing")
        return self.ohlcv_df
