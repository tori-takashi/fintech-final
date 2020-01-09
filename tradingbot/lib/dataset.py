from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

from .pandamex import PandaMex

from model.ohlcv_1min import OHLCV_1min

from technical_analysis.ad import TechnicalAnalysisAD
from technical_analysis.atr import TechnicalAnalysisATR
from technical_analysis.bollinger_band import TechnicalAnalysisBB
from technical_analysis.MACD import TechnicalAnalysisMACD
from technical_analysis.SAR import TechnicalAnalysisSAR
from technical_analysis.obv import TechnicalAnalysisOBV
from technical_analysis.roc import TechnicalAnalysisROC
from technical_analysis.rsi import TechnicalAnalysisRSI
from technical_analysis.so import TechnicalAnalysisSTOCH
from technical_analysis.williamsr import TechnicalAnalysisWilliamsR
from technical_analysis.wma import TechnicalAnalysisWMA


class Dataset:
    def __init__(self, db_client, data_provider_client=None, is_backtest=False):
        # data_provider_client should have exchange name
        self.is_backtest = is_backtest
        self.data_provider_client = data_provider_client
        self.db_client = db_client

        self.original_ohlcv_1min_table = self.data_provider_client.name + "_original_ohlcv_1min"

    def download_ohlcv_data_from_bitmex_with_asset_name(self, asset_name, start_time, end_time):
        print("downloading " + asset_name + " data on bitmex")
        pdmex = PandaMex(self.data_provider_client)
        ohlcv_df = pdmex.fetch_ohlcv(
            symbol=asset_name, start_time=start_time, end_time=end_time)

        ohlcv_df["exchange_name"] = "bitmex"
        ohlcv_df["asset_name"] = asset_name

        return PandaMex.to_timestamp(ohlcv_df)

    def download_ohlcv_data_from_bitmex(self, symbol, start_time, end_time):
        asset_names = eval(
            self.db_client.config['bitmex_asset_names']['asset_names'])

        ohlcv_df_list = []
        for asset_name in asset_names:
            ohlcv_df_list.append(self.download_ohlcv_data_from_bitmex_with_asset_name(
                asset_name, start_time, end_time))

        return pd.concat(ohlcv_df_list)

    def update_ohlcv(self, data_provider_name, start_time=None, asset_name=None, with_ta=False):
        # if ohlcv table is existing, start time will be ignored
        if self.db_client.is_mysql():
            if self.db_client.is_table_exist(self.original_ohlcv_1min_table):
                latest_row = self.db_client.get_last_row(
                    self.original_ohlcv_1min_table)
                if latest_row.empty is not True:
                    start_time = self.calc_fetch_start_time(latest_row)
            else:
                self.build_ohlcv_1min_table()

        if self.db_client.is_influxdb():
            # {FIXME} Hard coding
            if self.db_client.is_table_exist("OHLCV_data"):
                latest_row = self.db_client.get_last_row_with_tags(
                    "OHLCV_data", {"exchange_name": "bitmex", "asset_name": "BTC/USD"})
                start_time = self.calc_fetch_start_time(latest_row)

        if data_provider_name == "bitmex":
            ohlcv_df = self.download_ohlcv_data_from_bitmex(
                "1m", start_time, end_time=datetime.now())

        if with_ta and ohlcv_df.empty is not True:
            if self.db_client.is_influxdb() and self.db_client.is_table_exist("OHLCV_data"):
                padding_df = self.get_ohlcv(timeframe=1, start_time=datetime.now() - timedelta(minutes=200),
                                            end_time=datetime.now(), round=False)

                ohlcv_df["timestamp"] = ohlcv_df["timestamp"].dt.tz_localize(
                    timezone.utc)
                ohlcv_df.set_index('timestamp', inplace=True)

                concatnated_df = pd.concat(
                    [padding_df, ohlcv_df], axis=0, sort=False)
                concatnated_df.index = concatnated_df.index.map(np.datetime64)

                ohlcv_df = self.add_technical_statistics_to_ohlcv_df(
                    concatnated_df)

            elif self.db_client.is_mysql() and self.db_client.is_table_exist(self.original_ohlcv_1min_table):
                padding_df = self.get_ohlcv(timeframe=1, start_time=start_time - timedelta(minutes=60),
                                            end_time=start_time, round=False)

                if padding_df is not None and not padding_df.empty:
                    ohlcv_df.set_index('timestamp', inplace=True)

                    concatnated_df = pd.concat(
                        [padding_df, ohlcv_df], axis=0, sort=False)

                    ohlcv_df = self.add_technical_statistics_to_ohlcv_df(
                        concatnated_df)

                ohlcv_df = self.add_technical_statistics_to_ohlcv_df(
                    ohlcv_df)
                ohlcv_df = ohlcv_df[start_time:]
            else:  # ?
                ohlcv_df = self.add_technical_statistics_to_ohlcv_df(
                    ohlcv_df)

        if self.db_client.is_mysql():
            self.db_client.append_to_table(
                self.original_ohlcv_1min_table, ohlcv_df)

        if self.db_client.is_influxdb():
            if self.db_client.is_table_exist("OHLCV_data") is not True:
                ohlcv_df.set_index('timestamp', inplace=True)

            self.db_client.append_to_table(
                "OHLCV_data", ohlcv_df
            )

    def add_technical_statistics_to_ohlcv_df(self, df):
        ta_ad = TechnicalAnalysisAD(df)
        ad_df = ta_ad.get_ad()

        ta_atr = TechnicalAnalysisATR(df)
        atr_df = ta_atr.get_atr()

        ta_sar = TechnicalAnalysisSAR(df)
        ta_sar.get_psar_trend()
        # already append these cols

        ta_obv = TechnicalAnalysisOBV(df)
        obv_df = ta_obv.get_obv()

        ta_roc = TechnicalAnalysisROC(df)
        roc_df = ta_roc.get_roc()

        ta_rsi = TechnicalAnalysisRSI(df)
        rsi_df = ta_rsi.get_rsi()

        ta_so = TechnicalAnalysisSTOCH(df)
        so_df = ta_so.get_so()

        ta_williamsr = TechnicalAnalysisWilliamsR(df)
        williamsr_df = ta_williamsr.get_williams_r()

        if self.is_backtest:
            tas = pd.concat([df, ad_df, atr_df, obv_df, roc_df,
                             rsi_df, so_df, williamsr_df], axis=1)
            tas.dropna(inplace=True)
            return tas

    def build_ohlcv_1min_table(self):
        ohlcv_1min_table = OHLCV_1min.__table__
        ohlcv_1min_table.name = self.original_ohlcv_1min_table
        ohlcv_1min_table.create(bind=self.db_client.connector)

    def calc_fetch_start_time(self, latest_row):
        if self.db_client.is_mysql():
            latest_row_time = pd.to_datetime(
                latest_row['timestamp']).dt.to_pydatetime()[0]
        elif self.db_client.is_influxdb():
            latest_row_time = pd.to_datetime(
                latest_row.index.values[0]).to_pydatetime()

        append_offset = timedelta(minutes=1, seconds=30)
        start_time = latest_row_time + append_offset

        return start_time

    def update_all_ohlcv(self, start_time=None):
        data_provider_names = eval(
            self.db_client.config['data_providers']['data_providers'])
        for data_provider_name in data_provider_names:
            self.update_ohlcv(data_provider_name)

    def get_ohlcv(self, timeframe=None, start_time=None, end_time=None, exchange_name=None, asset_name=None, round=True):
        if self.db_client.is_mysql():
            print("Loading OHLCV data from " +
                  self.original_ohlcv_1min_table + " now...")
            ohlcv_1min_model = OHLCV_1min()
            ohlcv_1min_model.__table__.name = self.original_ohlcv_1min_table

            all_data_models = self.db_client.session.query(OHLCV_1min).filter(
                start_time < ohlcv_1min_model.timestamp).filter(
                    ohlcv_1min_model.timestamp < end_time).all()
            if not all_data_models:
                return None

            all_data = self.db_client.model_to_dataframe(all_data_models)
            all_data.set_index('timestamp', inplace=True)

        if self.db_client.is_influxdb():
            # [FIXME] Hard coding
            print("Loading OHLCV_data now...")
            all_data_default_dict = self.db_client.exec_sql(
                "SELECT * FROM OHLCV_data WHERE exchange_name='bitmex' and asset_name='BTC/USD'")
            all_data = self.db_client.default_dict_to_dataframe(
                "OHLCV_data", all_data_default_dict)
            print("Done")

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
