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

        past_mins = [1, 5, 10]

        self.ohlcv_with_past = self.ohlcv_with_timestamp
        self.append_past(past_mins)
        self.cut_empty_row(past_mins)

        return self.ohlcv_with_past

    def download_data(self, symbol, start_time, end_time):
        pdmex = PandaMex(self.bitmex)
        ohlcv_df = pdmex.fetch_ohlcv(
            "BTC/USD", symbol, start_time, end_time)

        # assign timestamp to ohlcv
        return PandaMex.to_timestamp(ohlcv_df)

    def append_past(self, mins):
        for min in mins:
            column_name = "before_" + str(min) + "min"
            self.ohlcv_with_past[column_name] = self.ohlcv_with_past["close"].shift(
                min)

    def cut_empty_row(self, mins):
        cut_index = max(mins)
        self.ohlcv_with_past.reset_index(inplace=True, drop=True)
        self.ohlcv_with_past.drop(
            self.ohlcv_with_past.index[[i for i in range(cut_index)]], inplace=True)
        self.ohlcv_with_past.reset_index(inplace=True, drop=True)

    def export_to_csv(self, filename):
        self.ohlcv_with_past.to_csv(filename)
