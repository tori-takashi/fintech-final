import pandas as pd
from datetime import timedelta

import random
from machine_learning.random_forest_prediction import RandomForestPredict30min


class PositionLeverage:
    def __init__(self, tradingbot, position_management):
        self.tradingbot = tradingbot
        self.position_management = position_management

        self.calculate_specific_leverage = self.tradingbot.calculate_specific_leverage

        self.random_forest_predict_30min = RandomForestPredict30min()

    def calculate_leverage(self, row):
        leverage = 1
        recent_market = None

        self.leverage_option_check()

        # for compare to random leverage
        if self.tradingbot.is_backtest and self.random_leverage:
            recent_market = self.recent_market_generator(row)
            return self.test_random_leverage([1, 2])

        # default leverage options
        leverage *= self.random_forest_leverage(row, recent_market)

        # bot specific leverage option
        leverage *= self.calculate_specific_leverage(row)

        return leverage

    def leverage_option_check(self):
        self.random_forest_leverage_adjust = self.tradingbot.default_params[
            "random_forest_leverage_adjust"]
        self.random_leverage = self.tradingbot.default_params["random_leverage"]

    def random_forest_leverage(self, row, recent_market):
        if self.random_forest_leverage_adjust is False:
            return 1
        # if the option was off

        random_forest_prediction = self.random_forest_predict_30min.binaryClassificationInThirtyMinutes(
            recent_market)

        if self.tradingbot.default_params["inverse_trading"]:
            if (row.signal == "buy" and random_forest_prediction == "downtrend") or\
                    (row.signal == "sell" and random_forest_prediction == "uptrend"):
                return 2
        else:
            if (row.signal == "buy" and random_forest_prediction == "uptrend") or\
                    (row.signal == "sell" and random_forest_prediction == "downtrend"):
                return 2
        return 1

    def random_forest_predict(self, predict_seed):
        prediction = int(self.random_forest_predict_30min.binaryClassificationInThirtyMinutes(
            predict_seed[["open", "high", "low", "close", "volume"]]))
        return "downtrend" if prediction == 0 else "uptrend"

    def recent_market_generator(self, row, data_range=75):
        # [FIXME] hard coded 75
        params = self.tradingbot.default_params
        if self.tradingbot.is_backtest:
            entry_time = pd.to_datetime(row.Index).to_pydatetime()
        else:
            entry_time = pd.to_datetime(row.name).to_pydatetime()

        recent_market = self.tradingbot.dataset_manipulator.get_ohlcv(timeframe=params["timeframe"],
                                                                      start_time=entry_time - timedelta(minutes=params["timeframe"] * 30), end_time=entry_time, round=True)

        return recent_market

    def test_random_leverage(self, samples):
        return random.choice(samples)
