from datetime import datetime, timedelta
from pathlib import Path

from lib.dataset import Dataset

from client.db_client import DBClient
from client.exchange_client import ExchangeClient

bitmex_exchange_client = ExchangeClient(
    "bitmex", Path("tradingbot/config.ini"))
mysql_client = DBClient("mysql", Path("tradingbot/config.ini"))

dataset_manager = Dataset(mysql_client, bitmex_exchange_client)

start_time = datetime.now() - timedelta(days=1000)
end_time = datetime.now()

dataset_manager.update_ohlcv("bitmex", start_time)
