from datetime import datetime, timedelta
import os

import pandas as pd

from lib.pandamex import PandaMex
from lib.time_ms import TimeMS
from client.db_client import DBClient


class HPriceMovePlobability:
    # H stands for hypothesis

    def __init__(self, bitmex, symbol=None, start_time=None, end_time=None):
        self.bitmex = bitmex
        db_exisiting = False

        db_path = "db/h_price_move_probability.sqlite3"
        if os.path.exists(db_path):
            db_exisiting = True

        db = DBClient("sqlite3", opt=db_path)
        self.db_client = db.client
        self.db_cursor = db.cursor

        self.symbol = symbol
        self.continuity_valuation_min = [20]

        self.initialize_duration(start_time, end_time)
        if db_exisiting:
            self.ohlcv = self.df_all_records()
        else:
            self.fetch_data()
            self.setting_db()

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
        for i in range(1, adding_column_number+2):
            column_name = "close_" + str(i) + "min_ago"
            self.ohlcv[column_name] = self.ohlcv["close"].shift(i)

        # remove including NaN records from top i+1
        self.ohlcv = self.ohlcv.drop(index=range(0, adding_column_number+1))

        # create db
        self.ohlcv.to_sql(
            "ohlcv_data", self.db_client, if_exists="replace", index=None)

    def h_conditional_probability(self):
        # [FIXME] adhoc codes, designating column name directly
        condition_plus_1 = (
            self.ohlcv["close_1min_ago"] > self.ohlcv["close_2min_ago"]).sum()
        condition_stay_1 = (
            self.ohlcv["close_1min_ago"] == self.ohlcv["close_2min_ago"]).sum()
        condition_minus_1 = (
            self.ohlcv["close_1min_ago"] < self.ohlcv["close_2min_ago"]).sum()
        intersect_plus_1 = ((
            self.ohlcv["close"] > self.ohlcv["close_1min_ago"]) & (
            self.ohlcv["close_1min_ago"] > self.ohlcv["close_2min_ago"])).sum()
        intersect_stay_1 = ((
            self.ohlcv["close"] > self.ohlcv["close_1min_ago"]) & (
            self.ohlcv["close_1min_ago"] == self.ohlcv["close_2min_ago"])).sum()
        intersect_minus_1 = ((
            self.ohlcv["close"] > self.ohlcv["close_1min_ago"]) & (
            self.ohlcv["close_1min_ago"] < self.ohlcv["close_2min_ago"])).sum()

        condition_plus_5 = (
            self.ohlcv["close_5min_ago"] > self.ohlcv["close_10min_ago"]).sum()
        condition_stay_5 = (
            self.ohlcv["close_5min_ago"] == self.ohlcv["close_10min_ago"]).sum()
        condition_minus_5 = (
            self.ohlcv["close_5min_ago"] < self.ohlcv["close_10min_ago"]).sum()
        intersect_plus_5 = ((
            self.ohlcv["close"] > self.ohlcv["close_5min_ago"]) & (
            self.ohlcv["close_5min_ago"] > self.ohlcv["close_10min_ago"])).sum()
        intersect_stay_5 = ((
            self.ohlcv["close"] > self.ohlcv["close_5min_ago"]) & (
            self.ohlcv["close_5min_ago"] == self.ohlcv["close_10min_ago"])).sum()
        intersect_minus_5 = ((
            self.ohlcv["close"] > self.ohlcv["close_1min_ago"]) & (
            self.ohlcv["close_5min_ago"] < self.ohlcv["close_10min_ago"])).sum()

        condition_plus_10 = (
            self.ohlcv["close_10min_ago"] > self.ohlcv["close_20min_ago"]).sum()
        condition_stay_10 = (
            self.ohlcv["close_10min_ago"] == self.ohlcv["close_20min_ago"]).sum()
        condition_minus_10 = (
            self.ohlcv["close_10min_ago"] < self.ohlcv["close_20min_ago"]).sum()
        intersect_plus_10 = ((
            self.ohlcv["close"] > self.ohlcv["close_10min_ago"]) & (
            self.ohlcv["close_10min_ago"] > self.ohlcv["close_20min_ago"])).sum()
        intersect_stay_10 = ((
            self.ohlcv["close"] > self.ohlcv["close_10min_ago"]) & (
            self.ohlcv["close_10min_ago"] == self.ohlcv["close_20min_ago"])).sum()
        intersect_minus_10 = ((
            self.ohlcv["close"] > self.ohlcv["close_10min_ago"]) & (
            self.ohlcv["close_10min_ago"] < self.ohlcv["close_20min_ago"])).sum()

        print("conditional probability for 1 min")
        print("p(+|+) =>" + str(intersect_plus_1/condition_plus_1))
        print("p(+|0) =>" + str(intersect_stay_1/condition_stay_1))
        print("p(+|-) =>" + str(intersect_minus_1/condition_minus_1))
        print("\n")

        print("conditional probability for 5 min")
        print("p(+|+) =>" + str(intersect_plus_5/condition_plus_5))
        print("p(+|0) =>" + str(intersect_stay_5/condition_stay_5))
        print("p(+|-) =>" + str(intersect_minus_5/condition_minus_5))
        print("\n")

        print("conditional probability for 10 min")
        print("p(+|+) =>" + str(intersect_plus_10/condition_plus_10))
        print("p(+|0) =>" + str(intersect_stay_10/condition_stay_10))
        print("p(+|-) =>" + str(intersect_minus_10/condition_minus_10))
        print("\n")

    def df_all_records(self):
        return pd.read_sql_query("SELECT * FROM ohlcv_data", self.db_client)
