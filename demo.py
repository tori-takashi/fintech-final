from datetime import datetime, timedelta

import client.exchange_client as exchange_client
import client.db_client as db_client

from lib.time_ms import TimeMS
from lib.pandamex import PandaMex

from hypothesis_test.h_price_move_probability import HPriceMovePlobability

import pandas as pd

bitmex = exchange_client.ExchangeClient("bitmex").client

start_time = datetime.now() - timedelta(hours=2)
end_time = datetime.now()

h_price_move = HPriceMovePlobability(
    bitmex, start_time=start_time, end_time=end_time)
h_price_move.show_all_records()
