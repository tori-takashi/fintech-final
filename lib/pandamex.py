# bitmex wrapper with pandas

from . import time_ms
import pandas as pd


class PandaMex:
    def __init__(self, bitmex):
        self.bitmex = bitmex

    def fetch_ohlcv(self, symbol, timeframe="1m", start_time=None, end_time=None, count=None, reverse=True):
        # o => open price
        # h => high price
        # l => low price
        # c => close price
        # v => volume

        ohlcv_columns = ["timestamp", "open", "high", "low", "close", "volume"]

        # limit is deprecated. we need to use count
        # appending optional paramaters
        params = {"reverse": reverse}

        if start_time == None:
            raise ValueError("empty start time")
        if count != None:
            params["count"] = count

        filter_param = r'{"startTime":"' + start_time + r'"'
        if end_time == None:
            filter_param += r'}'
        else:
            filter_param += r',"endTime":"' + end_time + r'"}'

        params["filter"] = filter_param

        ohlcvList = self.bitmex.fetch_ohlcv(
            symbol, timeframe, params=params)

        return pd.DataFrame(ohlcvList, columns=ohlcv_columns)

    @classmethod
    def to_timestamp(self, df):
        target = df
        target["timestamp"] = target["timestamp"].apply(
            lambda t: time_ms.TimeMS.fromtimestamp(t))
        return target
