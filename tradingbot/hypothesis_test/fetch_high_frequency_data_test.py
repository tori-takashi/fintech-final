import matplotlib.pyplot as plt
import pandas as pd
import datetime
import time
from pprint import pprint

from client.exchange_ws_client import WSClient


class FetchHighFrequencyData:
    def __init__(self, bitmex_ws, duration=None):
        columns = ["last", "buy", "sell", "mid", "timestamp"]

        if duration is None:
            duration = datetime.timedelta(seconds=10)
        price_list = self.fetch_data(bitmex_ws, duration)

        price_df = pd.DataFrame(columns=columns, data=price_list)
        self.export_figure(price_df)

    def fetch_data(self, bitmex_ws, duration):
        start_time = datetime.datetime.now()
        end_time = start_time + duration
        price_list = []

        while (end_time > datetime.datetime.now() and bitmex_ws.ws.sock.connected):
            time.sleep(0.2)

            tick_data = bitmex_ws.get_ticker()
            # inject timestamp
            tick_data["timestamp"] = pd.Timestamp.now()

            price_list.append(tick_data)

        return price_list

    def export_figure(self, price_df):
        pass
        # 0.2second(200ms) price moving
        # 15 second price moving
