# bitmex wrapper with pandas
from datetime import datetime, timedelta
import time
import math
import pandas as pd

from . import time_ms


class PandaMex:
    timeframe_sec = {"1m": 60, "5m": 60*5, "1h": 60*60, "1d": 60*60*24}
    ohlcv_columns = ["timestamp", "open", "high", "low", "close", "volume"]

    def __init__(self, bitmex):
        self.bitmex = bitmex

    def fetch_ohlcv(self, symbol="BTC/USD", timeframe="1m", start_time=None, end_time=None, count=500, reverse=True, no_index=False):
        # start time and end time are datetime

        # o => open price
        # h => high price
        # l => low price
        # c => close price
        # v => volume

        # seconds for duration calculating per downloading
        duration_sec_per_download = self.timeframe_sec[timeframe] * count

        current_start_time = start_time
        ohlcv_df = pd.DataFrame(data=None, columns=self.ohlcv_columns)

        iterations = self.calc_iterations(
            timeframe, start_time, end_time, count)

        i = 0
        while i < iterations:
            time.sleep(1.05)

            current_start_time = start_time + timedelta(seconds=i *
                                                        duration_sec_per_download)
            current_end_time = current_start_time + \
                timedelta(seconds=duration_sec_per_download)

            if end_time < current_end_time:
                # cut surplus in final iteration
                current_end_time = end_time

            params = self.params_builder(
                reverse, count, round(current_start_time.timestamp()), round(current_end_time.timestamp()))

            # download ohlcv data
            print("downloading " + str(current_start_time) +
                  " ~ " + str(current_end_time) + " data")
            ohlcv_rawdata = self.bitmex.client.fetch_ohlcv(
                symbol, timeframe, params=params)

            if not ohlcv_rawdata:
                print("No data downloaded")
                break

            # convert into dataframe
            ohlcv_df_part = pd.DataFrame(
                ohlcv_rawdata, columns=self.ohlcv_columns)
            # append to return dataframe
            ohlcv_df = ohlcv_df.append(ohlcv_df_part)

            # update to current_start time
            # get last row timestamp
            # increment count
            latest_row = pd.Series(
                ohlcv_df_part.iat[0, 0], index=ohlcv_df_part.columns)

            current_start_time = pd.Timestamp(latest_row.timestamp, unit="ms")
            i += 1

            print(str(round((i)*100/iterations, 1)) + "% completed")

        if no_index:
            return ohlcv_df.drop(columns=ohlcv_df.columns[[0]])

        return ohlcv_df

    @classmethod
    def to_timestamp(self, df, timestamp_ms_column="timestamp", timestamp_str_column=None):
        target = df
        if timestamp_ms_column and timestamp_str_column is None:
            target[timestamp_ms_column] = target[timestamp_ms_column].apply(
                lambda t: time_ms.TimeMS.fromtimestamp(t))
        elif timestamp_str_column:
            pass
        return target

    def params_builder(self, reverse, count, start_time, end_time):
        # limit is deprecated. we need to use count
        # appending optional paramaters
        params = {"reverse": reverse}

        if start_time == None:
            raise ValueError("unset start time")
        if count != None:
            params["count"] = count

        filter_param = r'{"startTime":"' + str(start_time) + r'"'
        if end_time == None:
            filter_param += r'}'
        else:
            filter_param += r',"endTime":"' + str(end_time) + r'"}'

        params["filter"] = filter_param

        return params

    def calc_iterations(self, timeframe, start_time, end_time, count):
        duration = end_time.timestamp() - start_time.timestamp()
        sec = self.timeframe_sec[timeframe]

        fetch_data_onetime = sec * count
        iteration = duration / fetch_data_onetime

        return int(iteration) + 1
