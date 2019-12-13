from datetime import datetime, timedelta
from time import sleep
import pandas as pd
import pprint

from client.exchange_client import ExchangeClient
from client.db_client import DBClient
from client.exchange_ws_client import WSClient
from lib.pandamex import PandaMex
from lib.time_ms import TimeMS

from hypothesis_test.fetch_high_frequency_data_test import FetchHighFrequencyData
from hypothesis_test.h_price_move_probability import HPriceMovePlobability
from hypothesis_test.volatility_dependent_offset_test import VolatilityDependentOffsetTest

from bot.bottom_trend_follower import BottomTrendFollow

bitmex_exchange_client = ExchangeClient("bitmex")
bot_bot = BottomTrendFollow(bitmex_exchange_client, is_backtest=True)
bot_bot.run()
