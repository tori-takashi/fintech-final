import pandas as pd
import talib as ta


class TechnicalAnalysisAD:
    def __init__(self, df):
        # calculate and apply AD
        self.ta_AD = ta.AD(df["high"], df["low"], df["close"], df["volume"])

    def get_ad(self):
        return pd.DataFrame(self.ta_AD)
