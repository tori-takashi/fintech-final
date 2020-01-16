from datetime import datetime, timedelta
from pathlib import Path

from lib.dataset import Dataset

from client.db_client import DBClient
from client.exchange_client import ExchangeClient

bitmex_exchange_client = ExchangeClient(
    "bitmex", "config.ini")
mysql_client = DBClient("mysql", "config.ini")

dataset_manager = Dataset(mysql_client, bitmex_exchange_client, True)

start_time = datetime.now() - timedelta(days=200)
end_time = datetime.now()

dataset_manager.update_ohlcv("bitmex", start_time, with_ta=True)
