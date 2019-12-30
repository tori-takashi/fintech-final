import sys
from pathlib import Path

# fix to adjust your directory
tradingbot_dir = "../../tradingbot"
config_ini = tradingbot_dir + "/config.ini"

sys.path.append(tradingbot_dir)

from datetime import datetime, timedelta
from pprint import pprint

from sklearn import linear_model
from scipy import stats

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
    "bitmex", Path(config_ini))
mysql_client = DBClient("mysql", Path(config_ini))
dataset_manager = Dataset(mysql_client, bitmex_exchange_client)
dataset_manager.update_ohlcv("bitmex")
