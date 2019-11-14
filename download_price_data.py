from datetime import datetime, timedelta
import pandas as pd

from client.exchange_client import ExchangeClient
from client.db_client import DBClient
from lib.time_ms import TimeMS
from lib.pandamex import PandaMex

bitmex = ExchangeClient("bitmex").client

symbol = "1m"
start_time = datetime.now() - timedelta(days=100)
end_time = datetime.now()

pdmex = PandaMex(bitmex)
ohlcv_df = pdmex.fetch_ohlcv(
    "BTC/USD", symbol, start_time, end_time)

# initialize ohlcv
ohlcv_with_timestamp = PandaMex.to_timestamp(ohlcv_df)
ohlcv_with_timestamp.to_csv("ohlcv_1min.csv")
