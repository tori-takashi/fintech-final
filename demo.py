from datetime import datetime, timedelta

import client.exchange_client as exchange_client
import client.db_client as db_client

from lib.time_ms import TimeMS
from lib.pandamex import PandaMex

import pandas as pd

bitmex = exchange_client.ExchangeClient("bitmex").client
db = db_client.DBClient("sqlite3")
db_client = db.client
db_cursor = db.cursor

pdmex = PandaMex(bitmex)

start_time = datetime.now() - timedelta(days=3)
end_time = datetime.now() - timedelta(days=3) + timedelta(hours=1)

df = pdmex.fetch_ohlcv("BTC/USD", "1m", start_time, end_time)
ohlcv = PandaMex.to_timestamp(df)

ohlcv.to_sql("ohlcv_data", db_client, if_exists="append", index=None)

print(pd.read_sql_query("SELECT * FROM ohlcv_data", db_client))
db_client.close()
