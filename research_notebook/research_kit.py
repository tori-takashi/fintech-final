import pandas as pd
from datetime import datetime, timedelta
from pprint import pprint
import sys
from pathlib import Path
sys.path.append("../tradingbot")

from client.exchange_client import ExchangeClient
from client.db_client import DBClient
from client.exchange_ws_client import WSClient
from lib.pandamex import PandaMex
from lib.time_ms import TimeMS
from lib.dataset import Dataset
from bot.bottom_trend_follower import BottomTrendFollow

bitmex_exchange_client = ExchangeClient(
    "bitmex", Path("../tradingbot/config.ini"))
mysql_client = DBClient("mysql", Path("../tradingbot/config.ini"))
dataset_manager = Dataset(mysql_client, bitmex_exchange_client)
dataset_manager.update_ohlcv("bitmex")
