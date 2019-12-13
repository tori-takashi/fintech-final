# bottom trend detection and follow with MACD
import pandas as pd
from bot.trading_bot import TradingBot
from technical_analysis.MACD import TechnicalAnalysisMACD


class BottomTrendFollow(TradingBot):
    def __init__(self, client, is_backtest=False):

        # hyper parameters
        self.timeframe = "1m"
        self.bottom_trend_tick = 180
        self.middle_trend_tick = 30
        self.top_trend_tick = 5
        close_in_do_nothing = True
        inverse_trading = True

        self.bot_name = "bottom_trend_follow_" + self.timeframe + "_" + \
            str(self.bottom_trend_tick) + "_" + \
            str(self.middle_trend_tick) + "_" + str(self.top_trend_tick)
        super().__init__(
            client,
            is_backtest,
            self.bot_name,
            self.timeframe,
            close_in_do_nothing=close_in_do_nothing,
            inverse_trading=inverse_trading
        )

        self.logger.info("hyper parameters")
        self.logger.info("timeframe : " + self.timeframe)
        self.logger.info("bottom_trend_tick : " + str(self.bottom_trend_tick))
        self.logger.info("middle_trend_tick : " + str(self.middle_trend_tick))
        self.logger.info("top_trend_tick : " + str(self.top_trend_tick))

        # for EMA and columns
        self.bottom_col = "ema_" + str(self.bottom_trend_tick)
        self.bottom_diff_col = self.bottom_col + "_diff"
        self.bottom_trend_col = self.bottom_col + "_trend"

        self.middle_col = "ema_" + str(self.middle_trend_tick)
        self.middle_diff_col = self.middle_col + "_diff"
        self.middle_trend_col = self.middle_col + "_trend"

        self.top_col = "ema_" + str(self.top_trend_tick)
        self.top_diff_col = self.top_col + "_diff"
        self.top_trend_col = self.top_col + "_trend"

    def calculate_metrics(self):
        ta_ema = TechnicalAnalysisMACD(self.ohlcv_df)

        self.ohlcv_df[self.bottom_col] = ta_ema.append_ema_close(
            self.bottom_trend_tick)
        self.ohlcv_df[self.middle_col] = ta_ema.append_ema_close(
            self.middle_trend_tick)
        self.ohlcv_df[self.top_col] = ta_ema.append_ema_close(
            self.top_trend_tick)

        # percentage of ema moving
        self.ohlcv_df[self.bottom_diff_col] = self.ohlcv_df[self.bottom_col].diff(
        ) / self.ohlcv_df[self.bottom_col] * 100
        self.ohlcv_df[self.middle_diff_col] = self.ohlcv_df[self.middle_col].diff(
        ) / self.ohlcv_df[self.middle_col] * 100
        self.ohlcv_df[self.top_diff_col] = self.ohlcv_df[self.top_col].diff(
        ) / self.ohlcv_df[self.top_col] * 100

        # trend of ema moving
        self.ohlcv_df.loc[(self.ohlcv_df[self.bottom_diff_col]
                           > 0), self.bottom_trend_col] = "uptrend"
        self.ohlcv_df.loc[~(self.ohlcv_df[self.bottom_diff_col]
                            > 0), self.bottom_trend_col] = "downtrend"

        self.ohlcv_df.loc[(self.ohlcv_df[self.middle_diff_col]
                           > 0), self.middle_trend_col] = "uptrend"
        self.ohlcv_df.loc[~(self.ohlcv_df[self.middle_diff_col]
                            > 0), self.middle_trend_col] = "downtrend"

        self.ohlcv_df.loc[(self.ohlcv_df[self.top_diff_col]
                           > 0), self.top_trend_col] = "uptrend"
        self.ohlcv_df.loc[~(self.ohlcv_df[self.top_diff_col]
                            > 0), self.top_trend_col] = "downtrend"

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

    def calculate_sign_backtest(self):
        self.ohlcv_df.loc[((self.ohlcv_df[self.bottom_trend_col] == "uptrend")
                           & (self.ohlcv_df[self.middle_trend_col] == "uptrend")
                           & (self.ohlcv_df[self.top_trend_col] == "uptrend")), "signal"] = "buy"
        self.ohlcv_df.loc[((self.ohlcv_df[self.bottom_trend_col] == "downtrend")
                           & (self.ohlcv_df[self.middle_trend_col] == "downtrend")
                           & (self.ohlcv_df[self.top_trend_col] == "downtrend")), "signal"] = "sell"
        self.ohlcv_df["signal"] = self.ohlcv_df["signal"].fillna("do_nothing")
