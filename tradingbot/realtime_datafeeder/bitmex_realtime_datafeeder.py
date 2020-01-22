from client.exchange_ws_client import WSClient

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from time import sleep

from pprint import pprint


class BitmexRealtimeDatafeeder:
    def __init__(self, config_path, performance_output=False):
        self.performance_output = performance_output

        self.bitmex_wsclient = WSClient(config_path)

        self.init_l1_orderbook()
        self.init_l2_orderbooks()
        self.init_recent_trades()

        if performance_output:
            self.second = 60
            self.time_l1_list = []
            self.time_l2_list = []
            self.time_recent_trades_list = []
            self.oneloop_count_list = []

    def init_l1_orderbook(self):
        self.latest_l1_orderbook = self.bitmex_wsclient.ws.get_ticker()
        self.latest_l1_orderbook_set = set()
        self.latest_l1_orderbook_df = pd.DataFrame(
            columns=["last", "buy", "sell", "mid"])

    def init_l2_orderbooks(self):
        self.latest_l2_orderbooks = json.dumps(
            self.bitmex_wsclient.ws.market_depth())
        self.latest_l2_orderbooks_list = []
        self.latest_l2_orderbooks_df = pd.DataFrame(
            columns=["symbol", "side", "size", "price", "timestamp"])

    def init_recent_trades(self):
        self.latest_recent_trades_set = set()
        self.latest_recent_trades_df = pd.DataFrame(columns=["timestamp", "symbol", "side", "size", "price",
                                                             "tickDirection", "trdMatchID", "grossValue", "homeNotional", "foreignNotional"])

    def run(self):
        ws = self.bitmex_wsclient.ws
        start_time = datetime.now()

        if self.performance_output:
            while (ws.ws.sock.connected) and (datetime.now() - start_time < timedelta(seconds=self.second)):
                self.fetch_data(ws)
                sleep(0.01)
            self.output_summary()

        else:
            while ws.ws.sock.connected:
                self.fetch_data(ws)
                sleep(0.01)

    def fetch_data(self, ws):
        # while loop_condition:
        if self.performance_output:
            loop_start_time = datetime.now()
            checkpoint = datetime.now()

        self.fetch_l1_orderbook(ws)
        if self.performance_output:
            self.time_l1_list.append(
                (datetime.now() - checkpoint).total_seconds())
            checkpoint = datetime.now()

        self.fetch_l2_orderbooks(ws)
        if self.performance_output:
            self.time_l2_list.append(
                (datetime.now() - checkpoint).total_seconds())
            checkpoint = datetime.now()

        self.fetch_recent_trade(ws)
        if self.performance_output:
            self.time_recent_trades_list.append(
                (datetime.now() - checkpoint).total_seconds())
        self.oneloop_count_list.append(
            (datetime.now() - loop_start_time).total_seconds())

    def output_summary(self):
        # seems l2 is bottleneck
        print("total timeframes")
        print(len(self.latest_l2_orderbooks_df.timestamp.unique()))
        print("average downloading pace")
        print(self.second/len(self.latest_l2_orderbooks_df.timestamp.unique()))

        print("total l1 rows")
        print(self.latest_l1_orderbook_df.count())
        print("total l2 rows")
        print(self.latest_l2_orderbooks_df.count())
        print("total recent trades rows")
        print(self.latest_recent_trades_df.count())

        l1_summary = np.array(self.time_l1_list)
        l2_summary = np.array(self.time_l2_list)
        recent_trades_summary = np.array(self.time_recent_trades_list)
        oneloop_summary = np.array(self.oneloop_count_list)

        print("=l1 orderbook=")
        print("average processing time: " + str(l1_summary.mean()))
        print("max processing time: " + str(l1_summary.max()))

        print("=l2 orderbook=")
        print("average processing time: " + str(l2_summary.mean()))
        print("max processing time: " + str(l2_summary.max()))

        print("=recent trades=")
        print("average processing time: " + str(recent_trades_summary.mean()))
        print("max processing time: " + str(recent_trades_summary.max()))

        print("===oneloop===")
        print("average processing time: " + str(oneloop_summary.mean()))
        print("max processing time: " + str(oneloop_summary.max()))

        pd.DataFrame([l1_summary, l2_summary, recent_trades_summary, oneloop_summary]).T.to_csv(
            "bitmex_realtime_ws_performance_log.csv")

    def fetch_recent_trade(self, ws):
        count_start = datetime.now()

        self.latest_recent_trades_set |= set(
            [json.dumps(trade) for trade in ws.recent_trades()])

        if len(self.latest_recent_trades_set) > 10:

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

        if len(self.latest_l1_orderbook_set) >= 2:
            temp_l1_orderbook = pd.DataFrame(
                [json.loads(l1_orderbook) for l1_orderbook in self.latest_l1_orderbook_set])
            temp_l1_orderbook.timestamp = pd.to_datetime(
                temp_l1_orderbook.timestamp)
            temp_l1_orderbook.sort_values("timestamp")

            self.latest_l1_orderbook_df = pd.concat(
                [self.latest_l1_orderbook_df, temp_l1_orderbook], sort=False)
            self.latest_l1_orderbook_df.reset_index(inplace=True, drop=True)
            self.latest_l1_orderbook_set = set()

    def fetch_l2_orderbooks(self, ws, wide_limit=50):
        l2_orderbooks = json.dumps(ws.market_depth())
        if l2_orderbooks != self.latest_l2_orderbooks:
            self.latest_l2_orderbooks = l2_orderbooks
            timestamp = datetime.now(timezone.utc)

            if wide_limit:
                last_price = ws.get_instrument()["lastPrice"]
                limit_range_top = last_price + wide_limit
                limit_range_bottom = last_price - wide_limit
                self.latest_l2_orderbooks_list.extend([self.purify_l2_orderbook(
                    l2_orderbook, timestamp) for l2_orderbook in json.loads(l2_orderbooks)
                    if limit_range_bottom <= l2_orderbook["price"] <= limit_range_top])
            else:
                self.latest_l2_orderbooks_list.extend([self.purify_l2_orderbook(
                    l2_orderbook, timestamp) for l2_orderbook in json.loads(l2_orderbooks)])

        if len(self.latest_l2_orderbooks_list) > 10:
            temp_l2_orderbooks = pd.DataFrame(self.latest_l2_orderbooks_list)
            self.latest_l2_orderbooks_df = pd.concat(
                [self.latest_l2_orderbooks_df, temp_l2_orderbooks], sort=False)
            self.latest_l2_orderbooks_df.reset_index(inplace=True, drop=True)

    def purify_l2_orderbook(self, orderbook, timestamp):
        del orderbook["id"]
        orderbook["timestamp"] = timestamp
        return orderbook
