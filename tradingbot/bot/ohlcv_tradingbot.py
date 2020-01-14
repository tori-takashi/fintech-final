from datetime import datetime, timedelta

class OHLCV_tradingbot:
    def __init__(self, dataset_manipulator):
        self.dataset_manipulator = dataset_manipulator

    def fetch_latest_ohlcv(self, ohlcv_start_time):
        while True:
            download_start = datetime.now()
            self.dataset_manipulator.update_ohlcv("bitmex", start_time=ohlcv_start_time,
            asset_name="BTC/USD", with_ta=True)
            if datetime.now() - download_start < timedelta(seconds=29):
                break