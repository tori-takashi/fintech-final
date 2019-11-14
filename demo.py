from datetime import datetime, timedelta
import pandas as pd

from client.exchange_client import ExchangeClient
from client.db_client import DBClient
from lib.time_ms import TimeMS
from lib.pandamex import PandaMex

from hypothesis_test.h_price_move_probability import HPriceMovePlobability

bitmex = ExchangeClient("bitmex").client

start_time = datetime.now() - timedelta(days=200)
end_time = datetime.now()
