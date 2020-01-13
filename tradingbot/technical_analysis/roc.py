import pandas as pd
import talib as ta


class TechnicalAnalysisROC:
    def __init__(self, df):
        # calculate and apply ROC
        self.ta_roc = ta.ROC(df["close"])

    def get_roc(self):
        return pd.DataFrame(self.ta_roc, columns=["roc"])
