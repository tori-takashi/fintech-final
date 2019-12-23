from datetime import datetime, timedelta
from configparser import SafeConfigParser
import pandas as pd
import numpy as np

from .pandamex import PandaMex

from model.ohlcv_1min import OHLCV_1min


class Dataset:
    def __init__(self, data_provider_client, db_client):
        # data_provider_client should have exchange name
        self.config = SafeConfigParser()

        # config.ini should be same place to executing file
        self.config.read("config.ini")

        self.data_provider_client = data_provider_client
        self.db_client = db_client

        self.original_ohlcv_1min_table = self.data_provider_client.name + "_original_ohlcv_1min"

    def download_ohlcv_data_from_bitmex_with_asset_name(self, asset_name, start_time, end_time):
        print("downloading " + asset_name + "data on bitmex")
        pdmex = PandaMex(self.data_provider_client)
        ohlcv_df = pdmex.fetch_ohlcv(
            symbol=asset_name, start_time=start_time, end_time=end_time)

        ohlcv_df["exchange_name"] = "bitmex"
        ohlcv_df["asset_name"] = asset_name

        return ohlcv_df

    def download_ohlcv_data_from_bitmex(self, symbol, start_time, end_time):
        asset_names = eval(self.config['bitmex_asset_names']['asset_names'])

        ohlcv_df_list = []
        for asset_name in asset_names:
            ohlcv_df_list.append(self.download_ohlcv_data_from_bitmex_with_asset_name(
                asset_name, start_time, end_time))

        return pd.concat(ohlcv_df_list)

    def update_ohlcv(self, data_provider_name, asset_name=None, start_time=None):
        # if ohlcv table is existing, start time will be ignored
        if self.db_client.is_table_exist(self.original_ohlcv_1min_table):
            latest_row = self.db_client.get_last_row(
                self.original_ohlcv_1min_table)
            if latest_row:
                start_time = self.calc_fetch_start_time(latest_row)

        else:
            self.build_ohlcv_1min_table()

        if data_provider_name == "bitmex":
            ohlcv_df = self.download_ohlcv_data_from_bitmex(
                "1m", start_time, end_time=datetime.now())

        self.db_client.append_to_table(
            self.original_ohlcv_1min_table, ohlcv_df)

    def build_ohlcv_1min_table(self):
        ohlcv_1min_table = OHLCV_1min.__table__
        ohlcv_1min_table.name = self.original_ohlcv_1min_table
        ohlcv_1min_table.create(bind=self.db_client.connector)

    def calc_fetch_start_time(self, latest_row):
        print("[FIXME] adhock solution to timezone problem")
        print("[FIXME] start time to fetch would be wrong below")

        latest_row_time = pd.to_datetime(
            latest_row['timestamp']).dt.to_pydatetime()[0]
        # convert to datetime array, then convert to pydatetime
        # [FIXME] adhock solution to timezone problem
        append_offset = timedelta(minutes=1, seconds=30)
        timezone_offset = timedelta(hours=8)

        start_time = latest_row_time + \
            append_offset - timezone_offset

        return start_time

    def update_all_ohlcv(self, start_time=None):
        data_provider_names = eval(
            self.config['data_providers']['data_providers'])
        for data_provider_name in data_provider_names:
            self.update_ohlcv(data_provider_name)

    def get_ohlcv(self, timeframe=None, start_time=None, end_time=None, round=True):
        query = "SELECT * FROM " + self.original_ohlcv_1min_table + ";"

        all_data = self.db_client.exec_sql(query)
        all_data['timestamp'] = pd.to_datetime(all_data.timestamp)
        all_data.set_index('timestamp', inplace=True)

        if round:
            rounded_start_time = self.floor_datetime_to_ohlcv(start_time, "up")
            rounded_end_time = self.floor_datetime_to_ohlcv(end_time, "down")
            return all_data[rounded_start_time:rounded_end_time:timeframe]
        else:
            return all_data[start_time:end_time:timeframe]

    def floor_datetime_to_ohlcv(self, start_or_end_time, round_up_or_down):
        if round_up_or_down == "up":
            return (start_or_end_time.replace(second=0, microsecond=0, minute=0, hour=start_or_end_time.hour)
                    + timedelta(hours=1))
        elif round_up_or_down == "down":
            return start_or_end_time.replace(second=0, microsecond=0, minute=0, hour=start_or_end_time.hour)

    def attach_past_futures_to_ohlcv_df(self, ohlcv_df, append_past=False, append_past_mins=None,
                                        append_future=False, append_future_mins=None):

        # assign timestamp to ohlcv
        ohlcv_df = PandaMex.to_timestamp(ohlcv_df)

        if append_past:
            ohlcv_df = self.append_past(ohlcv_df, append_past_mins)
            ohlcv_df = self.cut_empty_row(ohlcv_df, "past", append_past_mins)

        if append_future:
            ohlcv_df = self.append_future(ohlcv_df, append_future_mins)
            ohlcv_df = self.cut_empty_row(
                ohlcv_df, "future", append_future_mins)

        return ohlcv_df

    def append_past(self, ohlcv_df, past_mins=[1, 5, 10]):
        for min in past_mins:
            column_name = "past_" + str(min) + "min"
            ohlcv_df[column_name] = ohlcv_df["close"].shift(min)
        return ohlcv_df

    def append_future(self, ohlcv_df, future_mins=[1, 5, 10]):
        for min in future_mins:
            column_name = "after_" + str(min) + "min"
            ohlcv_df[column_name] = ohlcv_df["close"].shift(-min)
        return ohlcv_df

    def cut_empty_row(self, ohlcv_df, mode, mins=[1, 5, 10]):
        cut_num = max(mins)

        ohlcv_df.reset_index(inplace=True, drop=True)

        if mode == "past":
            ohlcv_df.drop(
                ohlcv_df.index[[i for i in range(cut_num)]], inplace=True)
        elif mode == "future":
            ohlcv_df.drop(ohlcv_df.index[[-(i + 1)
                                          for i in range(cut_num)]], inplace=True)

        ohlcv_df.reset_index(inplace=True, drop=True)
        return ohlcv_df
