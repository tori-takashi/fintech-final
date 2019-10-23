import client.exchange_client as exchange_client
from datetime import datetime, timedelta
from lib.time_ms import TimeMS
from lib.pandamex import PandaMex

bitmex = exchange_client.ExchangeClient("bitmex").client
now = datetime.now()

start_time = datetime.now() - timedelta(days=3)
end_time = datetime.now() - timedelta(days=3) + timedelta(hours=1)

pdmex = PandaMex(bitmex)
df = pdmex.fetch_ohlcv("BTC/USD", "1m", start_time, end_time)
ohlcv = PandaMex.to_timestamp(df)

print(ohlcv)
