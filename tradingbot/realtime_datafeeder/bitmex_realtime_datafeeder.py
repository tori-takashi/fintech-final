from client.exchange_ws_client import WSClient

import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from time import sleep


class BitmexRealtimeDatafeeder:
    def __init__(self, config_path):
        self.bitmex_wsclient = WSClient(config_path)

        pd.set_option('display.max_rows', 600)

        self.init_l1_orderbook()
        self.init_l2_orderbook()
        self.init_recent_trades()

    def init_l1_orderbook(self):
        self.latest_l1_orderbook = self.bitmex_wsclient.ws.get_ticker()
        self.latest_l1_orderbook_set = set()
        self.latest_l1_orderbook_df = pd.DataFrame(
            columns=["last", "buy", "sell", "mid"])

    def init_l2_orderbook(self):
        self.latest_l2_orderbook_list = []
        self.latest_l2_orderbook_df = pd.DataFrame(
            columns=["symbol", "id", "side", "size", "price", "timestamp"])

    def init_recent_trades(self):
        self.latest_recent_trades_set = set()
        self.latest_recent_trades_df = pd.DataFrame(columns=["timestamp", "symbol", "side", "size", "price",
                                                             "tickDirection", "trdMatchID", "grossValue", "homeNotional", "foreignNotional"])

    def run(self):
        ws = self.bitmex_wsclient.ws
        start_time = datetime.now()

        self.fetch_recent_trade(ws)
        while ((ws.ws.sock.connected) and (datetime.now() - start_time < timedelta(seconds=60))):
            self.fetch_l1_orderbook(ws)
            self.fetch_recent_trade(ws)

            sleep(0.01)

    def fetch_recent_trade(self, ws):
        self.latest_recent_trades_set |= set(
            [json.dumps(trade) for trade in ws.recent_trades()])

        if len(self.latest_recent_trades_set) > 10000:
            temp_recent_trade = pd.DataFrame(
                [json.loads(trade) for trade in self.latest_recent_trades_set])
            temp_recent_trade.timestamp = pd.to_datetime(
                temp_recent_trade.timestamp)
            temp_recent_trade.sort_values("timestamp")

            self.latest_recent_trades_df = pd.concat(
                [self.latest_recent_trades_df, temp_recent_trade], sort=False)
            self.latest_recent_trades_df.reset_index(inplace=True, drop=True)
            self.latest_recent_trades_set = set()

    def fetch_l1_orderbook(self, ws):
        current_ticker = ws.get_ticker()
        if current_ticker != self.latest_l1_orderbook:
            self.latest_l1_orderbook = current_ticker

            append_ticker = current_ticker.copy()
            append_ticker["timestamp"] = str(datetime.now(timezone.utc))
            self.latest_l1_orderbook_set.add(json.dumps(append_ticker))

        if len(self.latest_l1_orderbook_set) >= 100:
            temp_l1_orderbook = pd.DataFrame(
                [json.loads(l1_orderbook) for l1_orderbook in self.latest_l1_orderbook_set])
            temp_l1_orderbook.timestamp = pd.to_datetime(
                temp_l1_orderbook.timestamp)
            temp_l1_orderbook.sort_values("timestamp")

            self.latest_l1_orderbook_df = pd.concat(
                [self.latest_l1_orderbook_df, temp_l1_orderbook], sort=False)
            self.latest_l1_orderbook_df.reset_index(inplace=True, drop=True)
            self.latest_l1_orderbook_set = set()
