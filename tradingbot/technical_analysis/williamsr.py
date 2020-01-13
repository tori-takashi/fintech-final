import pandas as pd
import talib as ta


class TechnicalAnalysisWilliamsR:
    def __init__(self, df):
        # calculate and apply WilliamsR
        self.ta_williams_r = ta.WILLR(df["high"], df["low"], df["close"])

    def get_williams_r(self):
        return pd.DataFrame(self.ta_williams_r, columns=["williams_r"])
