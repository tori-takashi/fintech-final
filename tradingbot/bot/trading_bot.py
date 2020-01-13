import ccxt
import pandas as pd
import numpy as np

import logging
from datetime import datetime, timedelta
from time import sleep
from ccxt import ExchangeNotAvailable, RequestTimeout, BaseError

from sqlalchemy import Column, Integer, Float, Table, MetaData
from sqlalchemy import update
from sqlalchemy.orm import relationship, mapper

import random

from lib.pandamex import PandaMex
from lib.dataset import Dataset
from lib.line_notification import LineNotification

from model.backtest_management import BacktestManagement
from model.backtest_summary import BacktestSummary
from model.backtest_transaction_log import BacktestTransactionLog

from .position import Position
from .trading_bot_backtest_db import TradingBotBacktestDB

from machine_learning.random_forest_prediction import RandomForestPredict30min

        # default_params = {
        #    "bot_name" : string, bot name
        #    "version" : string version
        #    "timeframe": integer, timeframe
        #    "close_position_on_do_nothing": bool, close_position_on_do_nothing,
        #    "inverse_trading": bool, inverse_trading
        #    "random_forest_leverage_adjust"
        # }

class TradingBot:
    def __init__(self, default_params, specific_params, db_client, exchange_client=None, is_backtest=False):
        # initialize status and settings of bot.
        # if you try backtest, db_client is in need.
        self.is_backtest = is_backtest

        self.exchange_client = exchange_client
        self.db_client = db_client

        self.default_params = default_params
        self.specific_params = specific_params
        self.combined_params = dict(**self.default_params, **self.specific_params)

        self.dataset_manipulator = Dataset(self.db_client, self.exchange_client, self.is_backtest)
        
        self.random_leverage_only_backtest = False
        
        self.random_forest_predict_30min = RandomForestPredict30min()

        self.initial_balance = 100  # BTC
        self.account_currency = "USD"
        
        self.position = None

        if not is_backtest:
            self.line = LineNotification(db_client.config_path)
        else:
            self.trading_bot_backtest_db = TradingBotBacktestDB(self, is_backtest)

    def append_specific_params_columns(self):
        return {}
        # need to be override
        # return table def_keys
        # {"<column name>" : sqlalchemy column type (like Integer, String, Float....) }


    def run(self, ohlcv_df=None, ohlcv_start_time=datetime.now() - timedelta(days=90), ohlcv_end_time=datetime.now(),
            floor_time=True):
        self.processed_flag = False

        if self.is_backtest is not True:
            self.line.notify({**self.default_params, **self.specific_params}.items())
            self.fetch_latest_ohlcv(ohlcv_start_time)

        if ohlcv_df is not None:
            self.ohlcv_df = ohlcv_df
        else:
            self.ohlcv_df = self.dataset_manipulator.get_ohlcv(self.default_params["timeframe"], ohlcv_start_time, ohlcv_end_time)

        if self.is_backtest:
            self.ohlcv_with_metrics = self.calculate_metrics(self.ohlcv_df)
            # for summary
            if floor_time:
                ohlcv_start_time = self.dataset_manipulator.floor_datetime_to_ohlcv(ohlcv_start_time, "up")
                ohlcv_end_time = self.dataset_manipulator.floor_datetime_to_ohlcv(ohlcv_end_time, "down")
            
            self.ohlcv_start_time = ohlcv_start_time
            self.ohlcv_end_time = ohlcv_end_time
            
            self.ohlcv_with_signals = self.calculate_signals(self.ohlcv_with_metrics).dropna()

            self.write_to_backtest_database()
            

        else:
            # for real environment
            start_end_range = ohlcv_end_time - ohlcv_start_time
            # [FIXME] having only one position 

            while True:
                try:
                    self.trade_loop_for_real(ohlcv_df, start_end_range)
                except ExchangeNotAvailable:
                    self.line.notify("Exchange Not Available Error, Retry after 15 seconds")
                    sleep(15)
                    self.line.notify("loop restart...")
                except RequestTimeout:
                    self.line.notify("Request Time out, Retry after 15 seconds")
                    sleep(15)
                    self.line.notify("loop restart...")
                except BaseError:                    
                    self.line.notify("Unknown Error, Retry after 15 seconds")
                    sleep(15)
                    self.line.notify("loop restart...")

    def write_to_backtest_database(self):
        self.summary_id = self.trading_bot_backtest_db.init_summary()
        self.insert_backtest_transaction_logs()
        self.trading_bot_backtest_db.insert_params_management(self.summary_id)
        self.trading_bot_backtest_db.update_summary(self.transaction_logs, self.summary_id)

    def fetch_latest_ohlcv(self, ohlcv_start_time):
        while True:
            download_start = datetime.now()
            self.dataset_manipulator.update_ohlcv("bitmex", start_time=ohlcv_start_time,
            asset_name="BTC/USD", with_ta=True)
            if datetime.now() - download_start < timedelta(seconds=29):
                break

    def attach_params(self, ohlcv_df_with_signals, default_params, specific_params):
        for tag, param in default_params.items():
            ohlcv_df_with_signals[tag] = param
        for tag, param in specific_params.items():
            ohlcv_df_with_signals[tag] = param

        return ohlcv_df_with_signals

    def execute_with_time(self, interval=0.5):
        while True:
            # [FIXME] corner case, if the timeframe couldn't divide by 60, it's wrong behavior
            if (self.processed_flag is not True) and (datetime.now().minute % self.default_params["timeframe"] == 0):
                    break
            else:
                self.processed_flag = False
            sleep(interval)

    def signal_judge(self, row):
        if self.position is None:
            self.line.notify(self.position)
            return self.open_position(row)
        else:
            if (row.signal == "buy" and\
                    ((self.position.order_type == "long"  and self.default_params["inverse_trading"]) or\
                     (self.position.order_type == "short" and self.default_params["inverse_trading"] is not True))) or\
               (row.signal == "sell" and\
                   ((self.position.order_type == "long"  and self.default_params["inverse_trading"] is not True) or\
                    (self.position.order_type == "short" and self.default_params["inverse_trading"]))) or\
               (row.signal == "do_nothing" and\
                   (self.position is not None and self.default_params["close_position_on_do_nothing"])):

                    self.close_position(row)
                    return None

    def order_slide_slippage(self, best_price, total_loss_tolerance, onetime_loss_tolerance, onetime_duration,
        attempted_time, through_time=None):
        if through_time is None:
            through_time = onetime_duration
        return best_price*(0.0025*total_loss_tolerance*onetime_loss_tolerance*onetime_duration*attempted_time/through_time)

    def fetch_best_price(self):
        # open and close (long, short)
        
        # try open and limit order   => (bid, ask)
        # try close and market order => (bid, ask)

        # try open and market order  => (ask, bid)
        # try close and limit order  => (ask, bid)
        order_status = self.position.order_status
        order_method = self.position.order_method
        order_type   = self.position.order_type

        if (order_status == "pass" and order_method == "maker") or \
           (order_status == "open" and order_method == "taker"):
            price_type = "bid" if order_type == "long" else "ask"

        elif (order_status == "open" and order_method == "maker") or \
             (order_status == "pass" and order_method == "taker"):
             price_type = "ask" if order_type == "long" else "bid"

        return self.exchange_client.client.fetch_ticker(self.position.asset_name)[price_type]

    def send_position(self, total_loss_tolerance, onetime_loss_tolerance, onetime_duration, attempted_time, through_time=None):
        order_type = self.position.order_type
        order_status = self.position.order_status
        asset_name = self.position.asset_name
        lot = self.position.lot  # [FIXME] close all lot in the position
        leverage = self.position.leverage

        best_price = self.fetch_best_price()
        # slippage =  0.5 # taker
        slippage = -0.5 # maker

        if (order_status == "pass" and order_type == "long") or (order_status == "open" and order_type == "short"):
                order_price = best_price + slippage
                side = "Buy"
        elif (order_status == "pass" and order_type == "short") or (order_status == "open" and order_type == "long"):
                order_price = best_price - slippage
                side = "Sell"
                
        order_price_base = round(order_price)
        order_price_decimal = order_price - order_price_base

        order_price = order_price_base if order_price_decimal < 0.5 else order_price_base + 0.5

        # notification
        if order_status == "pass":
            self.line.notify("entry " + self.position.order_type + " order at : $" + str(order_price))
        elif order_status == "open":
            self.line.notify(
                "try closing " + self.position.order_type + " order at: $" + str(round(order_price, 1)) + \
                " lot: $" + str(lot) + " leverage: " + str(leverage) + "x")

            # make order
        return self.exchange_client.client.create_order(asset_name, "limit", side, lot, round(order_price,1),
            params = {'execInst': 'ParticipateDoNotInitiate'})

            # taker order
        #return self.exchange_client.client.create_order(asset_name, "limit", side, lot)#, round(order_price,1)),
            #params = {'execInst': 'ParticipateDoNotInitiate'})

    def trade_loop_for_real(self, ohlcv_df, start_end_range):
        self.current_balance = self.exchange_client.client.fetch_balance()["BTC"]["total"]
        self.line.notify("trade loop start")

        while True:
            self.execute_with_time()

            # load ohlcv
            self.dataset_manipulator.update_ohlcv("bitmex", asset_name="BTC/USD", with_ta=True)
            ohlcv_df = self.dataset_manipulator.get_ohlcv(self.default_params["timeframe"],
                datetime.now() - start_end_range, datetime.now(), exchange_name="bitmex",
                asset_name="BTC/USD", round=False)
        
            # calc metrics, judge buy or sell or donothing and params
            ohlcv_df_with_metrics = self.calculate_metrics(ohlcv_df)
            ohlcv_df_with_signals = self.calculate_signals(ohlcv_df_with_metrics)
            full_ohlcv_df = self.attach_params(ohlcv_df_with_signals, self.default_params, self.specific_params)

            # write newest ohlcv, signal and params into signals measurement
            self.db_client.append_to_table( self.default_params["bot_name"] + "_signals", full_ohlcv_df)

            # follow the latest signal
            latest_row = ohlcv_df.tail(1).iloc[0,:]
            self.position = self.signal_judge(latest_row)
            
            self.processed_flag = True


    def open_position(self, row):
        lot = self.calculate_lot(row) # fixed value
        leverage = self.calculate_leverage(row)  # fixed value

        # [FIXME] symbol is hardcoded, only for bitmex

        self.position = Position(row, self.is_backtest)
        self.position.current_balance = self.current_balance
        self.position.lot = lot
        self.position.leverage = leverage
        self.position.order_method = "maker"
        
        if (row.signal == "buy" and self.default_params["inverse_trading"] is not True) or (row.signal == "sell" and self.default_params["inverse_trading"]):
            self.position.order_type = "long"
        else:
            self.position.order_type = "short"

        if self.is_backtest:
            if (row.signal == "buy" and self.default_params["inverse_trading"] is not True) or (row.signal == "sell" and self.default_params["inverse_trading"]):
                self.position.order_type = "long"
            else:
                self.position.order_type = "short"
            return self.position
        else:
            self.exchange_client.client.private_post_position_leverage({"symbol": "XBTUSD", "leverage": str(leverage)})
            self.position = self.create_order(row)
            # discard failed opening orders
            return self.position if self.position is not None and self.position.order_status == "open" else None

    def close_position(self, row):
        if self.is_backtest:
            self.position.close_position(row)
            self.transaction_logs.append(self.position.generate_transaction_log_for_backtest(self.db_client, self.summary_id))
            self.current_balance = self.position.current_balance
        else:
            self.create_order(row)

    def create_order(self, row):
        if self.position.order_status == "pass":  # try to open
            return self.attempt_make_position(row, 1, 1, 60, 600)
        elif self.position.order_status == "open": # try to close
            return self.attempt_make_position(row, 1, 1, 40, None)

    def try_order(self, row, total_loss_tolerance, onetime_loss_tolerance,
        onetime_duration, attempted_time, order_start_time, through_time=None):

        order = self.send_position(total_loss_tolerance, onetime_loss_tolerance, onetime_duration,
            attempted_time, through_time=through_time)

        sleep(onetime_duration)

        order_info = self.exchange_client.client.fetch_order(order["id"])

        if self.position.order_status == "pass":
            self.position.open_order_id = order["id"]
            return self.is_position_opened(row, order_start_time, attempted_time, order_info)
        elif self.position.order_status == "open":
            self.position.close_order_id = order["id"]
            return self.is_position_closed(row, order_start_time, attempted_time, order_info)

    def cancel_failed_order(self, id):
        try:
            self.exchange_client.client.cancel_order(id)
        except:
            self.line.notify("order was deleted. retry")

    def attempt_make_position(self, row, total_loss_tolerance, onetime_loss_tolerance,
        onetime_duration, through_time):

        attempted_time = 1
        order_start_time = datetime.now()

        if self.position.order_status == "pass": # try open
            while datetime.now() - order_start_time < timedelta(seconds=through_time):
                order = self.try_order(row, total_loss_tolerance, onetime_loss_tolerance, onetime_duration,
                    attempted_time, order_start_time, through_time=through_time)
                if order:
                    return order
                else:
                    attempted_time += 1

            self.line.notify("all attempts are failed, skip")
            self.position.set_pass_log()
            self.db_client.influx_raw_connector.write_points([self.position.get_pass_log()])
            return None
                
        elif self.position.order_status == "open": # try close
            while True:
                order = self.try_order(row, total_loss_tolerance, onetime_loss_tolerance, onetime_duration,
                    attempted_time, order_start_time, through_time=None)
                if order:
                    return None
                else:
                    attempted_time += 1

    def is_position_opened(self, row, order_start_time, attempted_time, order_info):
        if order_info["status"] == "closed":
            self.position.order_status = "open"
            self.line.notify("entry order was successfully opened")
            open_log = {
                "open_attempt_time": attempted_time,
                "order_method": "maker"
            }
            self.position.set_open_log(open_log)
            return self.position

        elif order_info["status"] == "open":    # order failed
            self.line.notify("entry order failed, retrying. time:" + str(attempted_time))
            self.cancel_failed_order(order_info["id"])

    def is_position_closed(self, row, order_start_time, attempted_time, order_info):
        if order_info["status"] == "closed":  # order sucess
            updated_balance = self.exchange_client.client.fetch_balance()["BTC"]["total"]

            # notify
            self.line.notify("order was successfully closed.\n \
                current_balance: " + str(round(updated_balance, 5)) + "BTC\nasset moving : " + \
                str(round((updated_balance - self.current_balance) / self.current_balance*100, 5)) + "%")
    
            # send log to influxdb
            self.create_close_transaction_log_for_real(row, order_start_time,
                updated_balance, attempted_time, order_info)

            # update current balance
            self.current_balance = updated_balance
            return True

        else:  # order Failed
            self.line.notify("position closing failed. retry. total attempted time:" + str(attempted_time))
            self.cancel_failed_order(order_info["id"])
            return False


    def create_close_transaction_log_for_real(self, row, order_close_time, updated_balance, attempted_time, order_info):
        close_params = {
            "close_position_id": order_info["id"],
            "close_judged_price": row.close,
            "close_judged_time": row.index,
            "close_price": order_info["price"],
            "close_attempt_time": attempted_time,
            "close_attempt_period": datetime.now() - order_close_time,
            "close_order_method": "maker",
            "current_balance": updated_balance
        }
                
        self.position.set_close_log(close_params)
        self.db_client.influx_raw_connector.write_points([self.position.get_combined_log()])

    def bulk_insert(self):
        self.db_client.session.commit()

    def reset_backtest_result_with_params(self, default_params, specific_params):
        # for loop and serach optimal metrics value
        self.ohlcv_with_metrics = None
        self.ohlcv_with_signals = None
        self.closed_positions_df = None

        self.default_params = default_params
        self.specific_params = specific_params
        self.combined_params = dict(**self.default_params, **self.specific_params)


    def calculate_lot(self, row):
        # {FIXME} backtest is the percentage but real is the real USD number
        return 1 # backtest
        #return 60 # real
        
        # if you need, you can override
        # default is invest all that you have

    def set_random_leverage_only_backtest(self, random_leverage):
        self.random_leverage_only_backtest = random_leverage

    def calculate_leverage(self, row, leverage=1):
        # if you need, you can override
        leverage = leverage
        if self.is_backtest and self.random_leverage_only_backtest:
            return self.random_leverage_test([1,2])

        predict_seed = self.predict_seed_generator(row)
        if self.default_params["random_forest_leverage_adjust"]:
            random_forest_prediction = self.random_forest_predict_30min.binaryClassificationInThirtyMinutes(predict_seed)
            if self.default_params["inverse_trading"]:
                if (row.signal == "buy" and random_forest_prediction == "downtrend") or\
                        (row.signal == "sell" and random_forest_prediction == "uptrend"):
                    leverage *= 2
            else:
                if (row.signal == "buy" and random_forest_prediction == "uptrend") or\
                        (row.signal == "sell" and random_forest_prediction == "downtrend"):
                    leverage *= 2

        return leverage

    def random_leverage_test(self, samples):
        return random.choice(samples) 

    def random_forest_predict(self, predict_seed):
        prediction = int(self.random_forest_predict_30min.binaryClassificationInThirtyMinutes(
            predict_seed[["open", "high", "low", "close", "volume"]]))
        return "downtrend" if prediction == 0 else "uptrend"

    def predict_seed_generator(self, row, data_range=75):
        if self.is_backtest:
            entry_time = pd.to_datetime(row.Index).to_pydatetime()
        else:
            entry_time = pd.to_datetime(row.name).to_pydatetime()
        predict_seed = self.dataset_manipulator.get_ohlcv(timeframe=1,
            start_time=entry_time - timedelta(minutes=75), end_time=entry_time, round=False)
        return predict_seed


    def calculate_metrics(self, df):
        return df
        # need to override

    def calculate_signals(self, df):
        return df
        # need to override
        # return ["buy", "sell", "do_nothing"]

    def insert_backtest_transaction_logs(self):
        # refer to signal then judge investment
        # keep one order at most
        self.position = None
        self.current_balance = self.initial_balance
        self.transaction_logs = []

        for row in self.ohlcv_with_signals.itertuples(): # self.ohlcv_with_signals should be dataframe
            self.position = self.signal_judge(row, position=self.position)

        self.db_client.session.bulk_insert_mappings(BacktestTransactionLog, self.transaction_logs)

