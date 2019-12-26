from datetime import datetime, timedelta

from lib.dataset import Dataset

from client.db_client import DBClient
from client.exchange_client import ExchangeClient

bitmex_exchange_client = ExchangeClient("bitmex")
sqlite3_client = DBClient("sqlite3")
#mysql_client = DBClient("mysql")

dataset_manager = Dataset(sqlite3_client, bitmex_exchange_client)
#dataset_manager = Dataset(mysql_client, bitmex)

start_time = datetime.now() - timedelta(days=100)
end_time = datetime.now()

dataset_manager.update_ohlcv("bitmex", start_time)
