# bitmex wrapper with pandas
import time
import pandas as pd

from . import time_ms


class PandaMex:
    timeframe_sec = {"1m": 60, "5m": 60*5, "1h": 60*60, "1d": 60*60*24}

    def __init__(self, bitmex):
        self.bitmex = bitmex

    def fetch_ohlcv(self, symbol, timeframe="1m", start_time=None, end_time=None, count=500, reverse=True):
        # o => open price
        # h => high price
        # l => low price
        # c => close price
        # v => volume

        ohlcv_columns = ["timestamp", "open", "high", "low", "close", "volume"]

        iterations = self.calc_iterations(
            timeframe, start_time, end_time, count)
        fetch_data_onetime = self.timeframe_sec[timeframe] * count

        ohlcv_df = pd.DataFrame(data=None, columns=ohlcv_columns)

        for i in range(0, iterations):
            current_start = start_time.timestamp() + i * fetch_data_onetime
            current_end = start_time.timestamp() + (i + 1) * fetch_data_onetime

            # condition of continuing
            if current_start < end_time.timestamp():
                time.sleep(2)
                print(str(i*100/iterations) + "% completed")

                # cut surplus in final iteration
                if current_end > end_time.timestamp():
                    current_end = end_time.timestamp()

                # create paramater with current start and enc
                params = self.params_builder(
                    reverse, count, current_start, current_end)

                # at first, converting to dataframe to adjust the columns
                ohlcv_rawdata = self.bitmex.fetch_ohlcv(
                    symbol, timeframe, params=params)
                ohlcv_df_part = pd.DataFrame(
                    ohlcv_rawdata, columns=ohlcv_columns)
                ohlcv_df = ohlcv_df.append(ohlcv_df_part)

        return ohlcv_df

    @classmethod
    def to_timestamp(self, df):
        target = df
        target["timestamp"] = target["timestamp"].apply(
            lambda t: time_ms.TimeMS.fromtimestamp(t))
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
