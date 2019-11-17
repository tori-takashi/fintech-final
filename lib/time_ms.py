from datetime import datetime
import pandas as pd
import calendar


class TimeMS:
    @classmethod
    def fromtimestamp(self, ms):
        return pd.Timestamp(datetime.fromtimestamp(ms/1000))
