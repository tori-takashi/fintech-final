from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .pandamex import PandaMex


class CreateDataset:
    def __init__(self, bitmex):
        self.bitmex = bitmex

    def create_dataset(self, start_time=datetime.now()-timedelta(days=1), end_time=datetime.now(), symbol="1m"):
        self.ohlcv_with_timestamp = self.download_data(
            symbol, start_time, end_time)

        before_mins = [1, 5, 10]
        future_mins = [1, 5, 10]

        self.ohlcv_with_past_future = self.ohlcv_with_timestamp
        self.append_past(before_mins)
        self.append_future(future_mins)
        self.cut_empty_row(before_mins, future_mins)

        return self.ohlcv_with_past_future

    def download_data(self, symbol, start_time, end_time):
        pdmex = PandaMex(self.bitmex)
        ohlcv_df = pdmex.fetch_ohlcv(
            "BTC/USD", symbol, start_time, end_time)

        # assign timestamp to ohlcv
        return PandaMex.to_timestamp(ohlcv_df)

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
