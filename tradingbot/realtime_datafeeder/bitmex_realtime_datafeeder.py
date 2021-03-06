from client.exchange_ws_client import WSClient
from client.db_client import DBClient

from model.bitmex_l1_orderbook import BitmexL1OrderBook
from model.bitmex_l2_orderbook import BitmexL2OrderBook
from model.bitmex_recent_trades import BitmexRecentOrders

from multiprocessing import Process, Pipe

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from time import sleep

from pprint import pprint


class BitmexRealtimeDatafeeder:
    def __init__(self, db_client):
        self.db_client = db_client
        self.second = 3600

        self.bitmex_wsclient = WSClient(self.db_client.config_path)

        self.latest_l1_orderbook = json.dumps(
            self.bitmex_wsclient.ws.get_ticker())
        self.latest_l2_orderbooks = json.dumps(
            self.bitmex_wsclient.ws.market_depth())
        self.latest_recent_trades = json.dumps(
            self.bitmex_wsclient.ws.recent_trades())

    def run(self):
        ws = self.bitmex_wsclient.ws
        start_time = datetime.now()
        self.updated_at = datetime.now()

        while (ws.ws.sock.connected) and (datetime.now() - start_time < timedelta(seconds=self.second)):
            self.fetch_data(ws)
            sleep(0.01)

        print("done")

    def fetch_data(self, ws):
        loop_start_time = datetime.now()

        l1_parent, l1_child = Pipe()
        l2_parent, l2_child = Pipe()
        recent_trades_parent, recent_trades_child = Pipe()

        p_l1_orderbook = Process(
            target=self.fetch_l1_orderbook,  args=(ws, l1_child, ))
        p_l2_orderbook = Process(
            target=self.fetch_l2_orderbooks, args=(ws, l2_child, ))
        p_recent_trades = Process(
            target=self.fetch_recent_trade, args=(ws, recent_trades_child, ))

        p_l1_orderbook.start()
        p_l2_orderbook.start()
        p_recent_trades.start()

        l1_orderbook_list = l1_parent.recv()
        l2_orderbook_list = l2_parent.recv()
        recent_trades_list = recent_trades_parent.recv()

        self.db_client.session.execute(
            BitmexRecentOrders.__table__.insert(), recent_trades_list)

        self.db_client.session.execute(
            BitmexL1OrderBook.__table__.insert(), l1_orderbook_list)

        self.db_client.session.execute(
            BitmexL2OrderBook.__table__.insert(), l2_orderbook_list)

        p_l1_orderbook.join()
        p_l2_orderbook.join()
        p_recent_trades.join()

        if (datetime.now() - self.updated_at).total_seconds() > 5:
            self.updated_at = datetime.now()
            Process(target=self.write_to_db, args=(self.db_client, )).start()
            print((datetime.now() - loop_start_time).total_seconds())

    def fetch_recent_trade(self, ws, conn):
        recent_trades = json.dumps(ws.recent_trades())
        if recent_trades != self.latest_recent_trades:
            self.recent_trades = recent_trades
            append_recent_trades = json.loads(recent_trades)
            append_recent_trades = [self.convert_timestamp(
                row) for row in append_recent_trades]
            conn.send(append_recent_trades)
        else:
            conn.send(None)
        conn.close()

    def fetch_l1_orderbook(self, ws, conn):
        current_ticker = json.dumps(ws.get_ticker())
        if current_ticker != self.latest_l1_orderbook:
            self.latest_l1_orderbook = current_ticker
            recent_l1_dict = json.loads(current_ticker)
            recent_l1_dict["timestamp"] = datetime.now(timezone.utc)
            conn.send([recent_l1_dict])
        else:
            conn.send(None)
        conn.close()

    def fetch_l2_orderbooks(self, ws, conn, wide_limit=35):
        l2_orderbooks = json.dumps(ws.market_depth())
        if l2_orderbooks != self.latest_l2_orderbooks:
            self.latest_l2_orderbooks = l2_orderbooks
            timestamp = datetime.now(timezone.utc)

            if wide_limit:
                last_price = ws.get_instrument()["lastPrice"]
                limit_range_top = last_price + wide_limit
                limit_range_bottom = last_price - wide_limit
                conn.send([self.purify_l2_orderbook(l2_orderbook, timestamp) for l2_orderbook in json.loads(l2_orderbooks)
                           if limit_range_bottom <= l2_orderbook["price"] <= limit_range_top])
            else:
                conn.send([self.purify_l2_orderbook(
                    l2_orderbook, timestamp) for l2_orderbook in json.loads(l2_orderbooks)])
        else:
            conn.send(None)
        conn.close()

    def convert_timestamp(self, row):
        row["timestamp"] = pd.to_datetime(row["timestamp"]).to_pydatetime()
        return row

    def purify_l2_orderbook(self, orderbook, timestamp):
        del orderbook["id"]
        orderbook["timestamp"] = timestamp
        return orderbook

    def write_to_db(self, db_client):
        db_client.session.commit()
