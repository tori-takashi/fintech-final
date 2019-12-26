from datetime import datetime, timedelta
from time import sleep
import pandas as pd
import pprint
from pathlib import Path

from client.exchange_client import ExchangeClient
from client.db_client import DBClient
from client.exchange_ws_client import WSClient
from lib.pandamex import PandaMex
from lib.time_ms import TimeMS
from lib.dataset import Dataset

from hypothesis_test.fetch_high_frequency_data_test import FetchHighFrequencyData
from hypothesis_test.h_price_move_probability import HPriceMovePlobability
from hypothesis_test.volatility_dependent_offset_test import VolatilityDependentOffsetTest

from bot.bottom_trend_follower import BottomTrendFollow

bitmex_exchange_client = ExchangeClient(
    "bitmex", Path("tradingbot/config.ini"))

# influx_client = DBClient("influxdb")
# print(influx_client.connector.get_list_database())

mysql_client = DBClient("mysql", Path("tradingbot/config.ini"))

# update database
dataset_manager = Dataset(mysql_client, bitmex_exchange_client)
download_start_time = datetime.now() - timedelta(days=1000)
dataset_manager.update_ohlcv("bitmex", download_start_time)

bot_bot = BottomTrendFollow(
    db_client=mysql_client, exchange_client=bitmex_exchange_client, is_backtest=True)
bot_bot.run()
