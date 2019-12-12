from datetime import datetime, timedelta

from lib.create_dataset import CreateDataset
from client.exchange_client import ExchangeClient

bitmex = ExchangeClient("bitmex").client

create_dataset = CreateDataset(bitmex)

start_time = datetime.now() - timedelta(days=100)
end_time = datetime.now()

create_dataset.create_dataset(start_time=start_time, end_time=end_time)
create_dataset.export_to_csv("./csv/ohlcv_with_past.csv")
