import pandas as pd
import talib as ta


class TechnicalAnalysisWMA:
    def __init__(self, df):
        # calculate and apply WMA
        self.ta_wma = ta.WMA(df["close"])

    def get_wma(self):
        return pd.DataFrame(self.ta_wma, columns=["wma"])
