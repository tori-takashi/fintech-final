from datetime import datetime, timedelta
from time import sleep
import pandas as pd
import pprint

from client.exchange_client import ExchangeClient
from client.db_client import DBClient
from client.exchange_ws_client import WSClient
from lib.pandamex import PandaMex
from lib.time_ms import TimeMS

from hypothesis_test.spread_check import SpreadCheck
from hypothesis_test.h_price_move_probability import HPriceMovePlobability
from hypothesis_test.volatility_dependent_offset_test import VolatilityDependentOffsetTest

"""### test spread check ###

   bitmex_ws = WSClient().ws
   duration = timedelta(minutes=10)
   spread_check = SpreadCheck(bitmex_ws)
   """

# test volatility dependent offset

bitmex = ExchangeClient("bitmex").client
T = 5  # minutes
VolatilityDependentOffsetTest(bitmex, T)
