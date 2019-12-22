from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .pandamex import PandaMex

from model.ohlcv_1min import OHLCV_1min


class Dataset:
    def __init__(self, exchange_client, db_client):
        self.exchange_client = exchange_client
        self.db_client = db_client

        self.original_ohlcv_1min_column = self.exchange_client.name + "_original_ohlcv_1min"

    def download_ohlcv_data(self, symbol, start_time, end_time):
        pdmex = PandaMex(self.exchange_client)
        ohlcv_df = pdmex.fetch_ohlcv(
            "BTC/USD", symbol, start_time, end_time)

        # assign timestamp to ohlcv
        self.ohlcv_with_timestamp = PandaMex.to_timestamp(ohlcv_df)
        self.ohlcv_with_past_future = self.ohlcv_with_timestamp

        return self.ohlcv_with_timestamp

    def update_ohlcv(self, start_time=None):
        # if ohlcv table is existing, start time will be ignored
        if self.db_client.is_table_exist(self.original_ohlcv_1min_column):
            latest_row = self.db_client.get_last_row(
                self.original_ohlcv_1min_column)
            if latest_row is not False:
                latest_row_time = pd.to_datetime(
                    latest_row['timestamp']).dt.to_pydatetime()[0]

                # [FIXME] adhock solution to timezone problem
                append_offset = timedelta(minutes=1, seconds=30)
                print("[FIXME] adhock solution to timezone problem")
                print("[FIXME] fetching time would be wrong below")
                timezone_offset = timedelta(hours=8)

                start_time = latest_row_time + \
                    append_offset - timezone_offset
        else:
            ohlcv_1min_table = OHLCV_1min.__table__
            ohlcv_1min_table.name = self.original_ohlcv_1min_column
            ohlcv_1min_table.create(bind=self.db_client.connector)

        ohlcv = self.download_ohlcv_data(
            "1m", start_time, end_time=datetime.now())

        self.db_client.append_to_table(self.original_ohlcv_1min_column, ohlcv)

    def get_ohlcv(self, symbol_min=None, start_time=None, end_time=None, round=True):
        query = "SELECT * FROM " + self.original_ohlcv_1min_column + ";"

        all_data = self.db_client.exec_sql(query)
        all_data['timestamp'] = pd.to_datetime(all_data.timestamp)
        all_data.set_index('timestamp', inplace=True)

        if round:
            rounded_start_time = self.floor_datetime_to_ohlcv(start_time, "up")
            rounded_end_time = self.floor_datetime_to_ohlcv(end_time, "down")
            return all_data[rounded_start_time:rounded_end_time:symbol_min]
        else:
            return all_data[start_time:end_time:symbol_min]

    def floor_datetime_to_ohlcv(self, start_or_end_time, round_up_or_down):
        if round_up_or_down == "up":
            return (start_or_end_time.replace(second=0, microsecond=0, minute=0, hour=start_or_end_time.hour)
                    + timedelta(hours=1))
        elif round_up_or_down == "down":
            return start_or_end_time.replace(second=0, microsecond=0, minute=0, hour=start_or_end_time.hour)

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
