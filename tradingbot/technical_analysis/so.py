import pandas as pd
import talib as ta


class TechnicalAnalysisSTOCH:
    def __init__(self, df):
        # calculate and apply stochastic oscilator
        self.ta_slowk, self.ta_slowd = ta.STOCH(
            df["high"], df["low"], df["close"])

    def get_so(self):
        slowk = pd.DataFrame(self.ta_slowk, columns=["slowk"])
        slowd = pd.DataFrame(self.ta_slowd, columns=["slowd"])
        return pd.concat([slowk, slowd], axis=1)
