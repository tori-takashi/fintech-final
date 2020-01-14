from datetime import datetime, timedelta

class OHLCV_tradingbot:
    def __init__(self, dataset_manipulator, default_params, specific_params):
        self.dataset_manipulator = dataset_manipulator
        self.start_end_range = None

        self.default_params  = default_params
        self.specific_params = specific_params

    def fetch_latest_ohlcv(self, ohlcv_start_time):
        while True:
            download_start = datetime.now()
            self.dataset_manipulator.update_ohlcv("bitmex", start_time=ohlcv_start_time,
            asset_name="BTC/USD", with_ta=True)
            if datetime.now() - download_start < timedelta(seconds=29):
                break

    def generate_latest_row(self, calculate_metrics, calculate_signals):
        self.dataset_manipulator.update_ohlcv("bitmex", asset_name="BTC/USD", with_ta=True)
        ohlcv_df = self.dataset_manipulator.get_ohlcv(self.default_params["timeframe"],
            datetime.now() - self.start_end_range, datetime.now(), exchange_name="bitmex",
            asset_name="BTC/USD", round=False)

        ohlcv_df_with_metrics = calculate_metrics(ohlcv_df)
        ohlcv_df_with_signals = calculate_signals(ohlcv_df_with_metrics)
        full_ohlcv_df = self.attach_params(ohlcv_df_with_signals, self.default_params, self.specific_params)

        latest_row = full_ohlcv_df.tail(1).iloc[0,:]

        # write data to database
        self.dataset_manipulator.db_client.append_to_table( self.default_params["bot_name"] + "_signals", full_ohlcv_df)

        return latest_row

    def attach_params(self, ohlcv_df_with_signals, default_params, specific_params):
        for tag, param in default_params.items():
            ohlcv_df_with_signals[tag] = param
        for tag, param in specific_params.items():
            ohlcv_df_with_signals[tag] = param

        return ohlcv_df_with_signals