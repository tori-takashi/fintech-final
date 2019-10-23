# bitmex wrapper with pandas

from . import time_ms
import pandas as pd


class PandaMex:
    def __init__(self, bitmex):
        self.bitmex = bitmex

    def fetch_ohlcv(self, symbol, timeframe="1m", since=None, count=None, params={}):
        # o => open price
        # h => high price
        # l => low price
        # c => close price
        # v => volume

        ohlcv_columns = ["timestamp", "open", "high", "low", "close", "volume"]

        # limit is deprecated. we need to use count
        p = params
        if count != None:
            p["count"] = count

        ohlcvList = self.bitmex.fetch_ohlcv(
            symbol, timeframe, since, params=p)

        return pd.DataFrame(ohlcvList, columns=ohlcv_columns)

    @classmethod
    def to_timestamp(self, df):
        target = df
        target["timestamp"] = target["timestamp"].apply(
            lambda t: time_ms.TimeMS.fromtimestamp(t))
        return target
