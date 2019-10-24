from datetime import datetime, timedelta

import pandas as pd

from lib.pandamex import PandaMex
from lib.time_ms import TimeMS
from client.db_client import DBClient


class HPriceMovePlobability:
    # H stands for hypothesis

    def __init__(self, bitmex, start_time=None, end_time=None):
        self.bitmex = bitmex

        db_path = "db/h_price_move_probability.sqlite3"
        db = DBClient("sqlite3", opt=db_path)
        self.db_client = db.client
        self.db_cursor = db.cursor

        self.initialize_duration(start_time, end_time)
        self.build_db()

    def initialize_duration(self, start_time, end_time):
        # default: validation from 1 week ago to now
        if len(start_time) == 0:
            self.start_time = datetime.now() - timedelta(days=7)
        else:
            self.start_time = start_time

        if len(end_time) == 0:
            self.end_time = datetime.now()
        else:
            self.end_time = end_time

    def build_db(self):
        pdmex = PandaMex(self.bitmex)
        ohlcv_df = pdmex.fetch_ohlcv(
            "BTC/USD", "1m", self.start_time, self.end_time)
        ohlcv_mod_timestamp = PandaMex.to_timestamp(ohlcv_df)

        ohlcv_mod_timestamp.to_sql(
            "ohlcv_data", self.db_client, if_exists="replace", index=None)
