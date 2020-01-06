import warnings
from model.backtest_summary import BacktestSummary
from model.backtest_transaction_log import BacktestTransactionLog
from model.backtest_management import BacktestManagement
from bot.bottom_trend_follower import BottomTrendFollow
from lib.dataset import Dataset
from lib.time_ms import TimeMS
from lib.pandamex import PandaMex
from client.exchange_ws_client import WSClient
from client.db_client import DBClient
from client.exchange_client import ExchangeClient
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn import linear_model
from pprint import pprint
from datetime import datetime, timedelta
import sys
from pathlib import Path

# fix to adjust your directory
tradingbot_dir = "../../tradingbot"
config_ini = tradingbot_dir + "/config.ini"

sys.path.append(tradingbot_dir)


# option settings
pd.set_option("display.max_columns", 250)
pd.set_option("display.max_rows", 250)
warnings.filterwarnings('ignore')
plt.rcParams['figure.figsize'] = (10.0, 20.0)

bitmex_exchange_client = ExchangeClient(
    "bitmex", Path(config_ini))
mysql_client = DBClient("mysql", Path(config_ini))
dataset_manager = Dataset(mysql_client, bitmex_exchange_client, True)
dataset_manager.update_ohlcv("bitmex")
