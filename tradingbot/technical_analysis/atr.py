import pandas as pd
import talib as ta


class TechnicalAnalysisATR:
    def __init__(self, df):
        # calculate and apply AD
        self.ta_ATR = ta.ATR(df["high"], df["low"], df["close"])

    def get_atr(self):
        return pd.DataFrame(self.ta_ATR, columns=["atr"])
