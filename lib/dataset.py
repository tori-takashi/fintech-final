from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .pandamex import PandaMex


class Dataset:
    def __init__(self, bitmex, db_client=None):
        self.bitmex = bitmex
        self.db_client = db_client

        self.original_ohlcv_1min_column = self.bitmex.name + "_original_ohlcv_1min"

    def download_data(self, symbol, start_time, end_time):
        pdmex = PandaMex(self.bitmex)
        ohlcv_df = pdmex.fetch_ohlcv(
            "BTC/USD", symbol, start_time, end_time)

        # assign timestamp to ohlcv
        self.ohlcv_with_timestamp = PandaMex.to_timestamp(ohlcv_df)
        self.ohlcv_with_past_future = self.ohlcv_with_timestamp

        return self.ohlcv_with_timestamp

    def initialize_ohlcv(self, start_time):
        if self.db_client.is_table_exist(self.original_ohlcv_1min_column):
            pass
        else:
            create_table_query = """CREATE TABLE """ + self.original_ohlcv_1min_column + """ (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL
            );
                """
            self.db_client.exec_sql(
                self.original_ohlcv_1min_column, create_table_query, return_df=False)

        ohlcv = self.download_data(
            "1m", start_time, end_time=datetime.now())
        self.db_client.append_to_table(self.original_ohlcv_1min_column, ohlcv)

        ask = "SELECT * FROM " + self.original_ohlcv_1min_column + ";"
        print(self.db_client.exec_sql(self.original_ohlcv_1min_column, ask))

    def update_ohlcv(self):
        self.db_client
        self.db_client.append_to_table("original_ohlcv_1min")

    def append_past_future(self, before_mins=[1, 5, 10], future_mins=[1, 5, 10]):
        self.append_past(before_mins)
        self.append_future(future_mins)
        self.cut_empty_row(before_mins, future_mins)

    def append_past(self, before_mins):
        for min in before_mins:
            column_name = "before_" + str(min) + "min"
            self.ohlcv_with_past_future[column_name] = self.ohlcv_with_past_future["close"].shift(
                min)

    def append_future(self, future_mins):
        for min in future_mins:
            column_name = "after_" + str(min) + "min"
            self.ohlcv_with_past_future[column_name] = self.ohlcv_with_past_future["close"].shift(
                -min)

    def cut_empty_row(self, before_mins, after_mins):
        cut_before = max(before_mins)
        cut_after = max(after_mins)

        self.ohlcv_with_past_future.reset_index(inplace=True, drop=True)
        self.ohlcv_with_past_future.drop(
            self.ohlcv_with_past_future.index[[i for i in range(cut_before)]], inplace=True)
        self.ohlcv_with_past_future.drop(
            self.ohlcv_with_past_future.index[[-(i + 1) for i in range(cut_after)]], inplace=True)

        self.ohlcv_with_past_future.reset_index(inplace=True, drop=True)

    def export_to_csv(self, filename):
        self.ohlcv_with_past_future.to_csv(filename)
