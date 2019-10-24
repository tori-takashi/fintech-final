from datetime import datetime, timedelta

import pandas as pd

from lib.pandamex import PandaMex
from lib.time_ms import TimeMS
from client.db_client import DBClient


class HPriceMovePlobability:
    # H stands for hypothesis

    def __init__(self, bitmex, symbol=None, start_time=None, end_time=None):
        self.bitmex = bitmex

        db_path = "db/h_price_move_probability.sqlite3"
        db = DBClient("sqlite3", opt=db_path)
        self.db_client = db.client
        self.db_cursor = db.cursor

        self.symbol = symbol
        self.continuity_valuation_min = [1, 3]

        self.initialize_duration(start_time, end_time)
        self.fetch_data()
        self.setting_db()

        self.hypothesis_valuation()

    def __del__(self):
        self.db_client.close()

    def initialize_duration(self, start_time, end_time):
        # default: validation from 1 week ago to now
        if len(str(start_time)) == 0:
            self.start_time = datetime.now() - timedelta(days=7)
        else:
            self.start_time = start_time

        if len(str(end_time)) == 0:
            self.end_time = datetime.now()
        else:
            self.end_time = end_time

    def fetch_data(self):
        pdmex = PandaMex(self.bitmex)

        # default symbol ; 1 minutes
        if self.symbol == None:
            self.symbol = "1m"

        ohlcv_df = pdmex.fetch_ohlcv(
            "BTC/USD", self.symbol, self.start_time, self.end_time)

        # initialize ohlcv
        self.ohlcv = PandaMex.to_timestamp(ohlcv_df)

    def setting_db(self):
        # [FIXME]  use self.symbol for timeframe to evaluate
        # default 1 min and 3 min
        adding_column_number = max(self.continuity_valuation_min)

        # create close price at n min ago columns
        for i in range(1, adding_column_number+1):
            column_name = "close_" + str(i) + "min_ago"
            self.ohlcv[column_name] = self.ohlcv["close"].shift(i)

        # remove including NaN records
        self.ohlcv = self.ohlcv.drop(index=range(0, adding_column_number))

        # create db
        self.ohlcv.to_sql(
            "ohlcv_data", self.db_client, if_exists="replace", index=None)

    def hypothesis_valuation(self):
        pass

    def show_all_records(self):
        print(pd.read_sql_query(
            "SELECT * FROM ohlcv_data", self.db_client))
