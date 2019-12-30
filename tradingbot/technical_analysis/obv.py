import pandas as pd
import talib as ta


class TechnicalAnalysisOBV:
    def __init__(self, df):
        # calculate and apply OBV
        self.ta_obv = ta.OBV(df["close"], df["volume"])

    def get_obv(self):
        return pd.DataFrame(self.ta_obv, columns=["obv"])
