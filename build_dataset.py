from datetime import datetime, timedelta

from lib.dataset import Dataset
from client.exchange_client import ExchangeClient

bitmex = ExchangeClient("bitmex").client

create_dataset = Dataset(bitmex)

start_time = datetime.now() - timedelta(days=100)
end_time = datetime.now()

create_dataset.download_data(
    symbol="1m", start_time=start_time, end_time=end_time)
create_dataset.attach_past_future()
create_dataset.export_to_csv("./csv/ohlcv_with_past_future.csv")
