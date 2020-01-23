from client.exchange_ws_client import WSClient
from client.db_client import DBClient

from model.bitmex_l1_orderbook import BitmexL1OrderBook
from model.bitmex_l2_orderbook import BitmexL2OrderBook
from model.bitmex_recent_trades import BitmexRecentOrders

from multiprocessing import Process

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from time import sleep

from pprint import pprint


class BitmexRealtimeDatafeeder:
    def __init__(self, db_client, performance_output=False):
        self.performance_output = performance_output
        self.db_client = db_client

        self.bitmex_wsclient = WSClient(self.db_client.config_path)

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
        self.latest_recent_trades = json.dumps(
            self.bitmex_wsclient.ws.recent_trades())
        self.latest_recent_trades_list = []
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
        try:
            print(self.second/len(self.latest_l2_orderbooks_df.timestamp.unique()))
        except:
            print("No L1 data")

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

        self.latest_recent_trades_df.to_csv("latest_recent_trades.csv")

    def fetch_recent_trade(self, ws):
        recent_trades = json.dumps(ws.recent_trades())
        if recent_trades != self.latest_recent_trades:
            self.latest_recent_trades_list.extend(json.loads(recent_trades))
            self.recent_trades = recent_trades

        if len(self.latest_recent_trades_list) > 10000:
            Process(target=self.write_recent_trades_to_db,
                    args=(self.latest_recent_trades_list, self.db_client, )).start()
            self.latest_recent_trades_list = []

    def write_recent_trades_to_db(self, recent_trades_list, db_client):
        pd.DataFrame(recent_trades_list).to_csv(
            "recent_trades.csv", mode="a", header=False)

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

    def fetch_l2_orderbooks(self, ws, wide_limit=35):
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

        if len(self.latest_l2_orderbooks_list) > 40000:
            Process(target=self.write_l2_orderbook_to_db,
                    args=(self.latest_l2_orderbooks_list, self.db_client, )).start()
            self.latest_l2_orderbooks_list = []

    def write_l2_orderbook_to_db(self, l2_orderbooks_list, db_client):
        pd.DataFrame(l2_orderbooks_list).to_csv(
            "l2_orderbook.csv", mode="a", header=False)

    def purify_l2_orderbook(self, orderbook, timestamp):
        del orderbook["id"]
        orderbook["timestamp"] = timestamp
        return orderbook
