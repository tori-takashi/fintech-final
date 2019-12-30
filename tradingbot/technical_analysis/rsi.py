import pandas as pd
import talib as ta


class TechnicalAnalysisRSI:
    def __init__(self, df):
        # calculate and apply RSI
        self.ta_RSI = ta.RSI(df["close"])

    def get_rsi(self):
        return pd.DataFrame(self.ta_RSI, columns=["rsi"])
