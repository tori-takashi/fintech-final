import ccxt
import pandas as pd
import numpy as np

import random
from datetime import datetime, timedelta
from time import sleep
from ccxt import ExchangeNotAvailable, RequestTimeout, BaseError

from lib.pandamex import PandaMex
from lib.dataset import Dataset
from lib.line_notification import LineNotification

from model.backtest_management import BacktestManagement
from model.backtest_summary import BacktestSummary
from model.backtest_transaction_log import BacktestTransactionLog

from machine_learning.random_forest_prediction import RandomForestPredict30min

from .position import Position
from .position_management import PositionManagement
from .ohlcv_tradingbot import OHLCV_tradingbot

from .trading_bot_backtest import TradingBotBacktest

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

        self.set_params(default_params, specific_params)
        self.set_helper_libs()

        self.random_leverage_only_backtest = False
        self.random_forest_predict_30min = RandomForestPredict30min()

        self.initial_balance = 100  # BTC
        self.account_currency = "USD"
        
    def set_params(self, default_params, specific_params):
        self.default_params = default_params
        self.specific_params = specific_params
        self.combined_params = dict(**self.default_params, **self.specific_params)

    def set_helper_libs(self):
        self.dataset_manipulator = Dataset(self.db_client, self.exchange_client, self.is_backtest)
        self.ohlcv_tradingbot = OHLCV_tradingbot(self.dataset_manipulator, self.default_params, self.specific_params)
        self.position_management = PositionManagement(self)

        if self.is_backtest:
            self.trading_bot_backtest = TradingBotBacktest(self)
        else:
            self.line = LineNotification(self.db_client.config_path)


    ###### need to be override
    def append_specific_params_columns(self):
        return {}
        # return table def_keys
        # {"<column name>" : sqlalchemy column type (like Integer, String, Float....) }

    def calculate_lot(self, row):
        # {FIXME} backtest is the percentage but real is the real USD number
        return 1 # backtest
        #return 60 # real
        # default is invest all that you have

    def calculate_metrics(self, df):
        return df

    def calculate_signals(self, df):
        return df
        # return ["buy", "sell", "do_nothing"]
    #####

    def run(self, ohlcv_df=None, ohlcv_start_time=datetime.now() - timedelta(days=90), ohlcv_end_time=datetime.now(),
            floor_time=True):
        self.processed_flag = False

        self.ohlcv_tradingbot.ohlcv_start_time = ohlcv_start_time
        self.ohlcv_tradingbot.ohlcv_end_time = ohlcv_end_time

        self.ohlcv_tradingbot.update_ohlcv()
        
        if self.is_backtest:
            self.trading_bot_backtest.run_backtest(ohlcv_df, ohlcv_start_time, ohlcv_end_time, floor_time)

        else:
            self.line.notify({**self.default_params, **self.specific_params}.items())
            self.ohlcv_df = self.ohlcv_tradingbot.get_ohlcv() if ohlcv_df is None else ohlcv_df
            # for real environment
            # [FIXME] having only one position 

            while True:
                try:
                    self.trade_loop_for_real(ohlcv_df)
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

    def trade_loop_for_real(self, ohlcv_df):
        self.current_balance = self.exchange_client.client.fetch_balance()["BTC"]["total"]
        self.line.notify("trade loop start")

        while True:
            self.position_management.execute_with_time()

            latest_row = self.ohlcv_tradingbot.generate_latest_row(self.calculate_metrics, self.calculate_signals)
            self.line.notify(latest_row)
            self.position = self.signal_judge(latest_row)
            self.processed_flag = True



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


