import sys
from pathlib import Path
sys.path.append("../tradingbot")

from datetime import datetime, timedelta
from pprint import pprint

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from client.exchange_client import ExchangeClient
from client.db_client import DBClient
from client.exchange_ws_client import WSClient

from lib.pandamex import PandaMex
from lib.time_ms import TimeMS
from lib.dataset import Dataset

from bot.bottom_trend_follower import BottomTrendFollow

from model.backtest_management import BacktestManagement
from model.backtest_transaction_log import BacktestTransactionLog
from model.backtest_summary import BacktestSummary

# option settings
pd.set_option("display.max_columns", 250)
pd.set_option("display.max_rows", 250)
import warnings
warnings.filterwarnings('ignore')
plt.rcParams['figure.figsize'] = (10.0, 20.0)

bitmex_exchange_client = ExchangeClient(
    "bitmex", Path("../tradingbot/config.ini"))
mysql_client = DBClient("mysql", Path("../tradingbot/config.ini"))
dataset_manager = Dataset(mysql_client, bitmex_exchange_client)
dataset_manager.update_ohlcv("bitmex")
