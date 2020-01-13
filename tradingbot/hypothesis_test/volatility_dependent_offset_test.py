from datetime import datetime, timedelta
import pandas as pd

from client.exchange_client import ExchangeClient
from lib.pandamex import PandaMex


class VolatilityDependentOffsetTest:
    def __init__(self, bitmex, T):
        offset_time = timedelta(minutes=T + 1)

        symbol = "1m"
        start_time = datetime.now() - offset_time
        end_time = datetime.now()

        pdmex = PandaMex(bitmex)
        ohlcv_df = pdmex.fetch_ohlcv(
            "BTC/USD", symbol, start_time, end_time)

        # initialize ohlcv
        ohlcv_with_timestamp = PandaMex.to_timestamp(ohlcv_df)
        ohlcv_with_timestamp["close_t-1"] = ohlcv_with_timestamp["close"].shift(
            -1)
        ohlcv_with_timestamp = ohlcv_with_timestamp.drop(T)
        print(ohlcv_with_timestamp)

        self.offset_calculation(ohlcv_with_timestamp, T)

    def offset_calculation(self, ohlcv, T):
        print("\n###### Offset test with T=" + str(T) + "min #########\n")
        squared_price_difference = sum(
            (ohlcv["close"] - ohlcv["close_t-1"])**2)
        offset = round(squared_price_difference/T, 2)
        print("Volatility-Dependent Offset =>" + str(offset))
