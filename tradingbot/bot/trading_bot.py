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

from alembic.migration import MigrationContext
from alembic.operations import Operations

from lib.pandamex import PandaMex
from lib.dataset import Dataset
from lib.line_notification import LineNotification

from model.backtest_management import BacktestManagement
from model.backtest_summary import BacktestSummary
from model.backtest_transaction_log import BacktestTransactionLog


class TradingBot:
    def __init__(self, default_params, specific_params, db_client, exchange_client=None, is_backtest=False):
        # initialize status and settings of bot.
        # if you try backtest, db_client is in need.
        self.exchange_client = exchange_client
        self.db_client = db_client
        self.is_backtest = is_backtest

        self.default_params = default_params
        self.extract_default_params(self.default_params)

        self.specific_params = specific_params
        self.combined_params = dict(**self.default_params, **self.specific_params)

        self.dataset_manipulator = Dataset(self.db_client, self.exchange_client)

        if is_backtest:
            # for params table
            self.backtest_management_table_name = self.bot_name + "_backtest_management"

            # backtest configure
            self.initial_balance = 0.1  # USD
            self.account_currency = "BTC"

            if self.db_client.is_table_exist(self.backtest_management_table_name) is not True:
                self.create_backtest_management_table()
            if self.db_client.is_table_exist("backtest_management") is True:
                # delete useless template table
                drop_query = "DROP TABLE backtest_management;"
                self.db_client.exec_sql(drop_query, return_df=False)

        else:
            self.line = LineNotification(db_client.config_path)

    def create_backtest_management_table(self):
        backtest_management_template = BacktestManagement
        table_def = backtest_management_template.__table__

        # add specific params columns
        table_def = self.append_specific_params_column(table_def)

        backtest_summary_id = Column("backtest_summary_id", Integer)
        table_def.relation = relationship("BacktestSummary")
        table_def.append_column(backtest_summary_id)

        table_def.name = self.backtest_management_table_name

        table_def.create(bind=self.db_client.connector)
        
       # add foreign key constraint

        ctx = MigrationContext.configure(self.db_client.connector)
        op = Operations(ctx)

        with op.batch_alter_table(self.bot_name + "_backtest_management") as batch_op:
            batch_op.create_foreign_key("fk_management_summary", "backtest_summary", ["backtest_summary_id"], ["id"])

    def backtest_management_table(self):
        return Table(self.backtest_management_table_name, MetaData(bind=self.db_client.connector),
            autoload=True, autoload_with=self.db_client.connector)

    def append_specific_params_column(self, table_def):
        return table_def
        # Need to be oberride
        # return table def

    def extract_default_params(self, default_params):
        # default_params = {
        #    "bot_name" : bot_name, # used in bot name builder for log
        #    "timeframe": integer,
        #    "close_position_on_do_nothing": close_position_on_do_nothing,
        #    "inverse_trading": inverse_trading
        # }
        self.bot_name = default_params["bot_name"]
        self.version = default_params["version"]
        self.timeframe = default_params["timeframe"]
        self.close_position_on_do_nothing = default_params["close_position_on_do_nothing"]
        self.inverse_trading = default_params["inverse_trading"]

    def run(self, ohlcv_df=None, ohlcv_start_time=datetime.now() - timedelta(days=90), ohlcv_end_time=datetime.now(),
            floor_time=True):

        if self.is_backtest is not True:
            self.line.notify({**self.default_params, **self.specific_params}.items())

            while True:
                download_start = datetime.now()
                self.dataset_manipulator.update_ohlcv("bitmex", start_time=datetime.now() - timedelta(days=1),
                asset_name="BTC/USD", with_ta=True)
                if datetime.now() - download_start < timedelta(seconds=29):
                    break

        if ohlcv_df is not None:
            self.ohlcv_df = ohlcv_df
        else:
            self.ohlcv_df = self.dataset_manipulator.get_ohlcv(self.timeframe, ohlcv_start_time, ohlcv_end_time)

        if self.is_backtest:
            self.ohlcv_with_metrics = self.calculate_metrics_for_backtest()
            # for summary
            if floor_time:
                ohlcv_start_time = self.dataset_manipulator.floor_datetime_to_ohlcv(ohlcv_start_time, "up")
                ohlcv_end_time = self.dataset_manipulator.floor_datetime_to_ohlcv(ohlcv_end_time, "down")
            
            self.ohlcv_start_time = ohlcv_start_time
            self.ohlcv_end_time = ohlcv_end_time
            
            self.ohlcv_with_signals = self.calculate_signs_for_backtest().dropna()
            
            self.summary_id = self.init_summary()
            self.insert_backtest_transaction_logs()
            self.insert_params_management()
            self.update_summary()

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
                    self.line.notify("Unknown Rrror, Retry after 15 seconds")
                    sleep(15)
                    self.line.notify("loop restart...")

    def attach_params(self, ohlcv_df_with_signals, default_params, specific_params):
        for tag, param in default_params.items():
            ohlcv_df_with_signals[tag] = param
        for tag, param in specific_params.items():
            ohlcv_df_with_signals[tag] = param

        return ohlcv_df_with_signals

    def execute_with_sec_0(self, interval=0.5):
        while datetime.now().second == 0:
            sleep(interval)
            break

    def signal_judge_for_real(self, row, position=None):
        if position is None:
            return self.open_position_for_real(row)
        else:
            if (row.signal == "buy" and\
                    ((position.order_type == "long"  and self.inverse_trading) or\
                     (position.order_type == "short" and self.inverse_trading is not True))) or\
               (row.signal == "sell" and\
                   ((position.order_type == "long"  and self.inverse_trading is not True) or\
                    (position.order_type == "short" and self.inverse_trading))) or\
               (row.signal == "do_nothing" and\
                   (position is not None and self.close_position_on_do_nothing)):

                    self.close_position_for_real(row, position)
                    return None

    def order_slide_slippage(self, best_price, total_loss_tolerance, onetime_loss_tolerance, onetime_duration,
        attempted_time, through_time=None):
        if through_time is None:
            through_time = onetime_duration
        return best_price*(0.0025*total_loss_tolerance*onetime_loss_tolerance*onetime_duration*attempted_time/through_time)

    def fetch_best_price(self, position):
        # open and close (long, short)
        
        # try open and limit order   => (bid, ask)
        # try close and market order => (bid, ask)

        # try open and market order  => (ask, bid)
        # try close and limit order  => (ask, bid)
        order_status = position.order_status
        order_method = position.order_method
        order_type   = position.order_type

        if (order_status == "pass" and order_method == "maker") or \
           (order_status == "open" and order_method == "taker"):
            price_type = "bid" if order_type == "long" else "ask"

        elif (order_status == "open" and order_method == "maker") or \
             (order_status == "pass" and order_method == "taker"):
             price_type = "ask" if order_type == "long" else "bid"

        return self.exchange_client.client.fetch_ticker(position.asset_name)[price_type]

    def send_position(self, position, total_loss_tolerance, onetime_loss_tolerance, onetime_duration, attempted_time, through_time=None):
        order_type = position.order_type
        order_status = position.order_status
        asset_name = position.asset_name
        lot = position.lot  # [FIXME] close all lot in the position
        leverage = position.leverage

        best_price = self.fetch_best_price(position)
        #slippage = self.order_slide_slippage(best_price, total_loss_tolerance, onetime_loss_tolerance,
        #    onetime_duration, attempted_time, through_time=through_time)
        
        if (order_status == "pass" and order_type == "long") or (order_status == "open" and order_type == "short"):
                order_price = best_price #- slippage
                side = "Buy"
        elif (order_status == "pass" and order_type == "short") or (order_status == "open" and order_type == "long"):
                order_price = best_price # + slippage
                side = "Sell"

        order_price_base = round(order_price)
        order_price_decimal = order_price - order_price_base

        order_price = order_price_base if order_price_decimal < 0.5 else order_price_base + 0.5

        # notification
        if order_status == "pass":
            self.line.notify("entry " + position.order_type + " order at : $" + str(order_price))
        elif order_status == "open":
            self.line.notify(
                "try closing " + position.order_type + " order at: $" + str(round(order_price, 1)) + \
                " lot: $" + str(lot) + " leverage: " + str(leverage) + "x")

            # make order
        return self.exchange_client.client.create_order(asset_name, "limit", side, lot, round(order_price,1) ,
            params = {'execInst': 'ParticipateDoNotInitiate'})

    def trade_loop_for_real(self, ohlcv_df, start_end_range):
        position = None
        self.line.notify("trade loop start")

        while True:
            self.execute_with_sec_0() 

            # load ohlcv
            ohlcv_df = self.dataset_manipulator.get_ohlcv(self.timeframe,
                datetime.now() - start_end_range, datetime.now(), exchange_name="bitmex",
                asset_name="BTC/USD", round=False)
        
            # calc metrics, judge buy or sell or donothing and params
            ohlcv_df_with_metrics = self.calculate_metrics_for_real(ohlcv_df)
            ohlcv_df_with_signals = self.calculate_signs_for_real(ohlcv_df_with_metrics)
            full_ohlcv_df = self.attach_params(ohlcv_df_with_signals, self.default_params, self.specific_params)

            # write newest ohlcv, signal and params into signals measurement
            self.db_client.append_to_table("signals", full_ohlcv_df)

            # follow the latest signal
            latest_row = ohlcv_df.tail(1).iloc[0,:]
            position = self.signal_judge_for_real(latest_row, position)


    def open_position_for_real(self, row):
        self.current_balance = self.exchange_client.client.fetch_balance()["BTC"]["total"]

        lot = self.calculate_lot(row) # fixed value
        leverage = self.calculate_leverage(row)  # fixed value

        # [FIXME] symbol is hardcoded, only for bitmex
        self.exchange_client.client.private_post_position_leverage({"symbol": "XBTUSD", "leverage": str(leverage)})

        position = OrderPosition(row)
        position.current_balance = self.current_balance
        position.lot = lot
        position.leverage = leverage
        position.order_method = "maker"

        position = self.create_order(row, position)

        # discard failed opening orders
        return position if position is not None and position.order_status == "open" else None

    def close_position_for_real(self, row, position):
        self.create_order(row, position)

    def create_order(self, row, position):
        if position.order_status == "pass":  # try to open
            return self.attempt_make_position(row, position, 1, 1, 50, 50)
        elif position.order_status == "open": # try to close
            return self.attempt_make_position(row, position, 1, 1, 40, None)

    def try_order(self, row, position, total_loss_tolerance, onetime_loss_tolerance,
        onetime_duration, attempted_time, order_start_time, through_time=None):

        order = self.send_position(position, total_loss_tolerance, onetime_loss_tolerance, onetime_duration,
            attempted_time, through_time=through_time)

        sleep(onetime_duration)

        order_info = self.exchange_client.client.fetch_order(order["id"])

        if position.order_status == "pass":
            position.open_order_id = order["id"]
            return self.is_position_opened(row, position, order_start_time, attempted_time, order_info)
        elif position.order_status == "open":
            position.close_order_id = order["id"]
            return self.is_position_closed(row, position, order_start_time, attempted_time, order_info)

    def cancel_failed_order(self, id):
        try:
            self.exchange_client.client.cancel_order(id)
        except:
            self.line.notify("order was deleted. retry")

    def attempt_make_position(self, row, position, total_loss_tolerance, onetime_loss_tolerance,
        onetime_duration, through_time):

        attempted_time = 1
        order_start_time = datetime.now()

        if position.order_status == "pass": # try open
            while datetime.now() - order_start_time < timedelta(seconds=through_time):
                order = self.try_order(row, position, total_loss_tolerance, onetime_loss_tolerance, onetime_duration,
                    attempted_time, order_start_time, through_time=through_time)
                if order:
                    return order
                else:
                    attempted_time += 1

            self.line.notify("all attempts are failed, skip")
            position.set_pass_log()
            self.db_client.influx_raw_connector.write_points([position.get_pass_log()])
            return None
                
        elif position.order_status == "open": # try close
            while True:
                order = self.try_order(row, position, total_loss_tolerance, onetime_loss_tolerance, onetime_duration,
                    attempted_time, order_start_time, through_time=None)
                if order:
                    return None
                else:
                    attempted_time += 1

    def is_position_opened(self, row, position, order_start_time, attempted_time, order_info):
        if order_info["status"] == "closed":
            position.order_status = "open"
            self.line.notify("entry order was successfully opened")
            open_log = {
                "open_attempt_time": attempted_time,
                "order_method": "maker"
            }
            position.set_open_log(open_log)
            return position

        elif order_info["status"] == "open":    # order failed
            self.line.notify("entry order failed, retrying. time:" + str(attempted_time))
            self.cancel_failed_order(order_info["id"])

    def is_position_closed(self, row, position, order_start_time, attempted_time, order_info):
        if order_info["status"] == "closed":  # order sucess
            updated_balance = self.exchange_client.client.fetch_balance()["BTC"]["total"]

            # notify
            self.line.notify("order was successfully closed.\n \
                current_balance: " + str(round(updated_balance, 5)) + "BTC\nasset moving : " + \
                str(round((updated_balance - self.current_balance) / self.current_balance*100, 5)) + "%")
    
            # send log to influxdb
            self.create_close_transaction_log_for_real(row, position, order_start_time,
                updated_balance, attempted_time, order_info)

            # update current balance
            self.current_balance = updated_balance
            return True

        else:  # order Failed
            self.line.notify("position closing failed. retry. total attempted time:" + str(attempted_time))
            self.cancel_failed_order(order_info["id"])
            return False


    def create_close_transaction_log_for_real(self, row, position, order_close_time, updated_balance, attempted_time, order_info):
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
                
        position.set_close_log(close_params)
        self.db_client.influx_raw_connector.write_points([position.get_combined_log()])

    def bulk_insert(self):
        self.db_client.session.commit()

    def reset_backtest_result_with_params(self, default_params, specific_params):
        # for loop and serach optimal metrics value
        self.ohlcv_with_metrics = None
        self.ohlcv_with_signals = None
        self.summary_id = None
        self.closed_positions_df = None

        self.default_params = default_params
        self.extract_default_params(self.default_params)
        self.specific_params = specific_params
        self.combined_params = dict(**self.default_params, **self.specific_params)

        backtest_management = self.backtest_management_table()

        self.combined_params["backtest_summary_id"] = int(self.summary_id)
        del self.combined_params["bot_name"]

        self.db_client.connector.execute(backtest_management.insert().values(self.combined_params))

    def init_summary(self):
        summary = BacktestSummary().__table__
        init_summary = {
            "bot_name": self.bot_name,
            "initial_balance": self.initial_balance,
            "account_currency": self.account_currency
        }

        self.db_client.connector.execute(summary.insert().values(init_summary))
        # [FIXME] only for single task processing, unable to parallel process
        return int(self.db_client.get_last_row("backtest_summary").index.array[0])
        
    def calculate_lot(self, row):
        return 60 # USD
        # if you need, you can override
        # default is invest all that you have

    def calculate_leverage(self, row):
        return 1 # 1 times
        # if you need, you can override

    def calculate_metrics_for_real(self, df):
        return "metric"

    def calculate_metrics_for_backtest(self):
        return "ohlcv_with_metric_dataframe"
        # need to override

    def calculate_signs_for_real(self, df):
        return "signal"
        # need to override
        # return ["buy", "sell", "do_nothing"]

    def calculate_signs_for_backtest(self):
        return "ohlcv_with_signal_data"
        # need to override
        # return dataframe with ["buy", "sell", "do_nothing"]

    def insert_backtest_transaction_logs(self):
        # refer to signal then judge investment
        # keep one order at most

        position = None
        current_balance = self.initial_balance

        transaction_logs = []

        for row in self.ohlcv_with_signals.itertuples(): # self.ohlcv_with_signals should be dataframe
            if row.signal == "buy":
                if position is not None and position.order_type == "long":
                    # inverse => close position
                    # backtest
                    if self.inverse_trading:
                        position.close_position(row)
                        transaction_logs.append(position.generate_transaction_log_for_backtest(self.db_client, self.summary_id))
                        current_balance = position.current_balance
                        position = None
                    # normal => still holding
                    else:
                        pass
                    # backtest end

                elif position is not None and position.order_type == "short":
                    # inverse => still holding
                    if self.inverse_trading:
                        pass
                    # normal => close position
                    else:
                        position.close_position(row)
                        transaction_logs.append(position.generate_transaction_log_for_backtest(self.db_client, self.summary_id))
                        current_balance = position.current_balance
                        position = None
                else:
                    lot = self.calculate_lot()
                    leverage = self.calculate_leverage()
                    # inverse => open short position
                    if self.inverse_trading:
                        position = OrderPosition(row, "short", current_balance, lot, leverage, is_backtest=True)
                    else:
                        # normal => open long position
                        position = OrderPosition(row, "long", current_balance, lot, leverage, is_backtest=True)

            elif row.signal == "sell":
                if position is not None and position.order_type == "long":
                    # inverse => still holding
                    if self.inverse_trading:
                        pass
                    # normal => close position
                    else:
                        position.close_position(row)
                        transaction_logs.append(position.generate_transaction_log_for_backtest(self.db_client, self.summary_id))
                        current_balance = position.current_balance
                        position = None

                elif position is not None and position.order_type == "short":
                    # inverse => close position
                    if self.inverse_trading:
                        position.close_position(row)
                        transaction_logs.append(position.generate_transaction_log_for_backtest(self.db_client, self.summary_id))
                        current_balance = position.current_balance
                        position = None

                    # normal => still holding
                    else:
                        pass

                else:
                    lot = self.calculate_lot()
                    leverage = self.calculate_leverage()
                    # inverse => open long position
                    if self.inverse_trading:
                        position = OrderPosition(row, "long",current_balance, lot, leverage, is_backtest=True)
                    else:
                        # normal => open short position
                        position = OrderPosition(row, "short",current_balance, lot, leverage, is_backtest=True)

            elif row.signal == "do_nothing":
                if self.close_position_on_do_nothing:
                    # if do nothing option is true
                    # and you get do nothing from signal, then close out the position
                    if position is not None:
                        # close position
                        position.close_position(row)
                        transaction_logs.append(position.generate_transaction_log_for_backtest(self.db_client, self.summary_id))
                        current_balance = position.current_balance
                        position = None

        # the processing time is propotionate to the number of transaction logs
        self.db_client.session.bulk_insert_mappings(BacktestTransactionLog, transaction_logs)

        self.closed_positions_df = pd.DataFrame(transaction_logs)
        self.closed_positions_df["holding_time"] = self.closed_positions_df["close_time"] - \
            self.closed_positions_df["entry_time"]

    def update_summary(self):
        win_entries_condition = (self.closed_positions_df["profit_status"] == "win")
        win_row = self.closed_positions_df[(win_entries_condition)]
        lose_entries_condition = (self.closed_positions_df["profit_status"] == "lose")
        lose_row = self.closed_positions_df[(lose_entries_condition)]

        long_entries_condition = (self.closed_positions_df["order_type"] == "long")
        long_row = self.closed_positions_df[(long_entries_condition)]
        short_entries_condition = (self.closed_positions_df["order_type"] == "short")
        short_row = self.closed_positions_df[(short_entries_condition)]

        win_long_row = self.closed_positions_df[(win_entries_condition) & (long_entries_condition)]
        win_short_row = self.closed_positions_df[(win_entries_condition) & (short_entries_condition)]
        lose_long_row = self.closed_positions_df[(lose_entries_condition) & (long_entries_condition)]
        lose_short_row = self.closed_positions_df[(lose_entries_condition) & (short_entries_condition)]

        total_return = float(self.closed_positions_df.profit_size.sum())

        if self.closed_positions_df.iloc[-1].current_balance > 0:
            total_return_percentage = float(100 * (self.closed_positions_df.iloc[-1].current_balance / self.initial_balance))
        else:
            total_return_percentage = \
                float(-100 * (abs(self.closed_positions_df.iloc[-1].current_balance) + self.initial_balance) / self.initial_balance)

        win_consecutive = self.build_consecutive("win")
        lose_consecutive = self.build_consecutive("lose")
    
        drawdowns = self.build_drawdowns()

        if drawdowns["maximal_drawdown"] == 0:
            recovery_factor = 0
        else:
            recovery_factor = total_return / drawdowns["maximal_drawdown"]

        # total
        summary_dict = {
        "id": self.summary_id,
        "total_entry": len(self.closed_positions_df),

        "total_max_holding_ms": self.closed_positions_df["holding_time"].max().to_pytimedelta(),
        "total_average_holding_ms": self.closed_positions_df["holding_time"].mean().to_pytimedelta(),
        "total_min_holding_ms": self.closed_positions_df["holding_time"].min().to_pytimedelta(),

        "total_return": total_return,
        "total_return_average": float(self.closed_positions_df.profit_size.mean()),
        "total_standard_deviation": float(self.closed_positions_df.profit_size.std()),
        "total_skewness": float(self.closed_positions_df.profit_size.skew()),
        "total_kurtosis": float(self.closed_positions_df.profit_size.kurt()),
        "total_median": float(self.closed_positions_df.profit_size.median()),

        "total_return_percentage": total_return_percentage,
        "total_return_average_percentage": float(self.closed_positions_df.profit_percentage.mean()),
        "total_standard_deviation_percentage": float(self.closed_positions_df.profit_percentage.std()),
        "total_skewness_percentage": float(self.closed_positions_df.profit_percentage.skew()),
        "total_kurtosis_percentage": float(self.closed_positions_df.profit_percentage.kurt()),
        "total_median_percentage": float(self.closed_positions_df.profit_percentage.median()),

        "total_transaction_cost": float(self.closed_positions_df.transaction_cost.sum()),

        # win
        "win_entry": len(win_row),
        "win_average_holding_ms": win_row["holding_time"].mean().to_pytimedelta(),
        "win_rate": (len(win_row) / len(self.closed_positions_df)) * 100,

        "win_return": float(win_row.profit_size.sum()),
        "win_return_average": float(win_row.profit_size.mean()),
        "win_standard_deviation": float(win_row.profit_size.std()),
        "win_skewness": float(win_row.profit_size.skew()),
        "win_kurtosis": float(win_row.profit_size.kurt()),
        "win_median": float(win_row.profit_size.median()),

        "win_return_average_percentage": float(win_row.profit_percentage.mean()),
        "win_standard_deviation_percentage": float(win_row.profit_percentage.std()),
        "win_skewness_percentage": float(win_row.profit_percentage.skew()),
        "win_kurtosis_percentage": float(win_row.profit_percentage.kurt()),
        "win_median_percentage": float(win_row.profit_percentage.median()),

        "win_transaction_cost": float(win_row.transaction_cost.sum()),
            
        "win_consecutive_max_entry": win_consecutive["consecutive_max_entry"],
        "win_consecutive_average_entry": win_consecutive["consecutive_average_entry"],
        "win_consecutive_max_profit": float(win_consecutive["consecutive_df"].profit_size.sum()),

        "win_max_profit": float(win_row.profit_size.max()),
        "win_max_profit_percentage": float(win_row.profit_percentage.max()),
                
        # lose
        "lose_entry": len(lose_row),
        "lose_rate": (len(lose_row) / len(self.closed_positions_df)) * 100,
        "lose_average_holding_ms": lose_row["holding_time"].mean().to_pytimedelta(),
  
        "lose_return": float(lose_row.profit_size.sum()),
        "lose_return_average": float(lose_row.profit_size.mean()),
        "lose_standard_deviation": float(lose_row.profit_size.std()),
        "lose_skewness": float(lose_row.profit_size.skew()),
        "lose_kurtosis": float(lose_row.profit_size.kurt()),
        "lose_median": float(lose_row.profit_size.median()),

        "lose_return_average_percentage": float(lose_row.profit_percentage.mean()),
        "lose_standard_deviation_percentage": float(lose_row.profit_percentage.std()),
        "lose_skewness_percentage": float(lose_row.profit_percentage.skew()),
        "lose_kurtosis_percentage": float(lose_row.profit_percentage.kurt()),
        "lose_median_percentage": float(lose_row.profit_percentage.median()),

        "lose_transaction_cost": float(lose_row.transaction_cost.sum()),
            
        "lose_consecutive_max_entry": lose_consecutive["consecutive_max_entry"],
        "lose_consecutive_average_entry": lose_consecutive["consecutive_average_entry"],
        "lose_consecutive_max_loss": float(lose_consecutive["consecutive_df"].profit_size.sum()),

        "lose_max_loss": float(lose_row.profit_size.min()),
        "lose_max_loss_percentage": float(lose_row.profit_percentage.min()),

        # long
        "long_entry": len(long_row),
        "long_rate": (len(long_row) / len(self.closed_positions_df)) * 100,
        "long_average_holding_ms": long_row["holding_time"].mean().to_pytimedelta(),

        "long_return": float(long_row.profit_size.sum()),
        "long_return_average": float(long_row.profit_size.mean()),
        "long_standard_deviation": float(long_row.profit_size.std()),
        "long_skewness": float(long_row.profit_size.skew()),
        "long_kurtosis": float(long_row.profit_size.kurt()),
        "long_median": float(long_row.profit_size.median()),

        "long_return_average_percentage": float(long_row.profit_percentage.mean()),
        "long_standard_deviation_percentage": float(long_row.profit_percentage.std()),
        "long_skewness_percentage": float(long_row.profit_percentage.skew()),
        "long_kurtosis_percentage": float(long_row.profit_percentage.kurt()),
        "long_median_percentage": float(long_row.profit_percentage.median()),
            
        "long_max_profit": float(long_row.profit_size.max()),
        "long_max_profit_percentage": float(long_row.profit_percentage.max()),

        "long_max_loss": float(long_row.profit_size.min()),
        "long_max_loss_percentage": float(long_row.profit_percentage.min()),

        #short
        "short_entry": len(short_row),
        "short_rate": (len(short_row) / len(self.closed_positions_df)) * 100,
        "short_average_holding_ms": short_row["holding_time"].mean().to_pytimedelta(),

        "short_return": float(short_row.profit_size.sum()),
        "short_return_average": float(short_row.profit_size.mean()),
        "short_standard_deviation": float(short_row.profit_size.std()),
        "short_skewness": float(short_row.profit_size.skew()),
        "short_kurtosis": float(short_row.profit_size.kurt()),
        "short_median": float(short_row.profit_size.median()),

        "short_return_average_percentage": float(short_row.profit_percentage.mean()),
        "short_standard_deviation_percentage": float(short_row.profit_percentage.std()),
        "short_skewness_percentage": float(short_row.profit_percentage.skew()),
        "short_kurtosis_percentage": float(short_row.profit_percentage.kurt()),
        "short_median_percentage": float(short_row.profit_percentage.median()),
            
        "short_max_profit": float(short_row.profit_size.max()),
        "short_max_profit_percentage": float(short_row.profit_percentage.max()),

        "short_max_loss": float(short_row.profit_size.min()),
        "short_max_loss_percentage": float(short_row.profit_percentage.min()),

        # win long
        "win_long_entry": len(win_long_row),
        "win_long_average_holding_ms": win_long_row["holding_time"].mean().to_pytimedelta(),

        "win_long_return": float(win_long_row.profit_size.sum()),
        "win_long_return_average": float(win_long_row.profit_size.mean()),
        "win_long_standard_deviation": float(win_long_row.profit_size.std()),
        "win_long_skewness": float(win_long_row.profit_size.skew()),
        "win_long_kurtosis": float(win_long_row.profit_size.kurt()),
        "win_long_median": float(win_long_row.profit_size.median()),

        "win_long_return_average": float(win_long_row.profit_size.mean()),
        "win_long_return_average_percentage": float(win_long_row.profit_percentage.mean()),
        "win_long_standard_deviation_percentage": float(win_long_row.profit_percentage.std()),
        "win_long_skewness_percentage": float(win_long_row.profit_percentage.skew()),
        "win_long_kurtosis_percentage": float(win_long_row.profit_percentage.kurt()),
        "win_long_median_percentage": float(win_long_row.profit_percentage.median()),

        # win short
        "win_short_entry": len(win_short_row),
        "win_short_average_holding_ms": win_short_row["holding_time"].mean().to_pytimedelta(),

        "win_short_return": float(win_short_row.profit_size.sum()),
        "win_short_return_average": float(win_short_row.profit_size.mean()),
        "win_short_standard_deviation": float(win_short_row.profit_size.std()),
        "win_short_skewness": float(win_short_row.profit_size.skew()),
        "win_short_kurtosis": float(win_short_row.profit_size.kurt()),
        "win_short_median": float(win_short_row.profit_size.median()),

        "win_short_return_average_percentage": float(win_short_row.profit_percentage.mean()),
        "win_short_standard_deviation_percentage": float(win_short_row.profit_percentage.std()),
        "win_short_skewness_percentage": float(win_short_row.profit_percentage.skew()),
        "win_short_kurtosis_percentage": float(win_short_row.profit_percentage.kurt()),
        "win_short_median_percentage": float(win_short_row.profit_percentage.median()),

        # lose long
        "lose_long_entry": len(lose_long_row),
        "lose_long_average_holding_ms": lose_long_row["holding_time"].mean().to_pytimedelta(),

        "lose_long_return": float(lose_long_row.profit_size.sum()),
        "lose_long_return_average": float(lose_long_row.profit_size.mean()),
        "lose_long_standard_deviation": float(lose_long_row.profit_size.std()),
        "lose_long_skewness": float(lose_long_row.profit_size.skew()),
        "lose_long_kurtosis": float(lose_long_row.profit_size.kurt()),
        "lose_long_median": float(lose_long_row.profit_size.median()),

        "lose_long_return_average_percentage": float(lose_long_row.profit_percentage.mean()),
        "lose_long_standard_deviation_percentage": float(lose_long_row.profit_percentage.std()),
        "lose_long_skewness_percentage": float(lose_long_row.profit_percentage.skew()),
        "lose_long_kurtosis_percentage": float(lose_long_row.profit_percentage.kurt()),
        "lose_long_median_percentage": float(lose_long_row.profit_percentage.median()),

        # lose short
        "lose_short_entry": len(lose_short_row),
        "lose_short_average_holding_ms": lose_short_row["holding_time"].mean().to_pytimedelta(),

        "lose_short_return": float(lose_short_row.profit_size.sum()),
        "lose_short_return_average": float(lose_short_row.profit_size.mean()),
        "lose_short_standard_deviation": float(lose_short_row.profit_size.std()),
        "lose_short_skewness": float(lose_short_row.profit_size.skew()),
        "lose_short_kurtosis": float(lose_short_row.profit_size.kurt()),
        "lose_short_median": float(lose_short_row.profit_size.median()),

        "lose_short_return_average_percentage": float(lose_short_row.profit_percentage.mean()),
        "lose_short_standard_deviation_percentage": float(lose_short_row.profit_percentage.std()),
        "lose_short_skewness_percentage": float(lose_short_row.profit_percentage.skew()),
        "lose_short_kurtosis_percentage": float(lose_short_row.profit_percentage.kurt()),
        "lose_short_median_percentage": float(lose_short_row.profit_percentage.median()),

        # other metrics
        "backtest_start_time": self.backtest_start_time,
        "backtest_end_time": self.backtest_end_time,

        "bot_name": self.bot_name,
        "initial_balance": self.initial_balance,
        "account_currency": self.account_currency,


        "absolute_drawdown": float(drawdowns["absolute_drawdown"]),
        "maximal_drawdown": float(drawdowns["maximal_drawdown"]),
        "relative_drawdown": float(drawdowns["relative_drawdown"]),

        "profit_factor": float(win_row.profit_size.sum() / abs(lose_row.profit_size.sum())),
        "recovery_factor": recovery_factor
        }

        self.db_client.session.bulk_update_mappings(BacktestSummary, [summary_dict])

    def build_drawdowns(self):
        if self.closed_positions_df.current_balance.min() < 0:
            absolute_drawdown = self.initial_balance + self.closed_positions_df.current_balance.min() 
        else:
            absolute_drawdown = self.initial_balance - self.closed_positions_df.current_balance.min() 

        current_drawdown = 0
        current_relative_drawdown = 0

        max_balance = self.initial_balance

        maximal_drawdown = 0
        relative_drawdown = 0

        for log in self.closed_positions_df.itertuples():
            if max_balance < log.current_balance:
                max_balance = log.current_balance
            else:

                if log.current_balance > 0:
                    current_drawdown = max_balance - log.current_balance
                else:
                    current_drawdown = max_balance + log.current_balance

                current_relative_drawdown = (abs(current_drawdown) / max_balance)*100

                if maximal_drawdown < current_drawdown:
                    maximal_drawdown = current_drawdown

                if relative_drawdown < current_relative_drawdown:
                    relative_drawdown = current_relative_drawdown
        
        result = {
            "absolute_drawdown" : absolute_drawdown,
            "maximal_drawdown": maximal_drawdown,
            "relative_drawdown" : relative_drawdown
        }

        return result

    def build_consecutive(self, profit_status):
        current_start_index = 0
        current_end_index = 0

        max_start_index = 0
        max_consecutive = 0
        max_end_index = 0

        consective_flag = False

        consecutive_win_lose_entries = []

        profit_status_df = self.closed_positions_df.loc[:,["profit_status"]]
        profit_status_np = profit_status_df.to_numpy(copy=True)

        # for loop
        for row_id, row in enumerate(profit_status_np):
            if row[0] == profit_status:
                if consective_flag is False:
                # consecutive count start
                    current_start_index = row_id
                    consective_flag = True
            else:
                if consective_flag:
                    current_end_index = row_id

                    if max_consecutive <= current_end_index - current_start_index:
                        max_start_index = current_start_index
                        max_end_index = current_end_index - 1
                        max_consecutive = current_end_index - current_start_index

                    consecutive_win_lose_entries.append(current_end_index - current_start_index)
                    consective_flag = False

        consecutive_max_entry = np.max(consecutive_win_lose_entries)
        consecutive_average_entry = np.mean(consecutive_win_lose_entries)

        return_hash = {
            "consecutive_df": self.closed_positions_df.loc[max_start_index:max_end_index],
            "consecutive_max_entry": int(consecutive_max_entry),
            "consecutive_average_entry": float(consecutive_average_entry)
        }

        return return_hash

class OrderPosition:
    def __init__(self, row_open, is_backtest=False):
        self.is_backtest = is_backtest
        self.common_log(row_open)

        if self.is_backtest:
            self.transaction_fee_by_order = 0.0005  # profit * transaction fee, please update to 2 times 
            # because transaction fee is charged for both open and close order.
            self.order_status = "open"

            self.entry_price = row_open.close
            self.entry_time = row_open.Index

        else:
            # for real environment
            self.order_status = "pass"

            # for open
            self.open_position_id = None
            self.entry_judged_price = row_open.close
            self.entry_judged_time = datetime.now()

            self.entry_price = None
            self.entry_price_difference = None
            self.entry_time = None

            self.open_attempt_time = None
            self.open_attempt_period = None

            self.entry_order_method = None # maker or taker
            self.open_transaction_cost = None

            # for close
            self.closed_position_id = None
            self.close_judged_price = None
            self.close_judged_time = None

            self.close_price = None
            self.close_price_difference = None
            self.close_time = None

            self.close_attempt_time = None
            self.close_attempt_period = None

            self.close_order_method = None # maker or taker
            self.close_transaction_cost = None

            self.total_transaction_cost = None

        # for transaction log

        self.open_position()

    def common_log(self, row_open):
        self.exchange_name = row_open.exchange_name
        self.asset_name = row_open.asset_name

        if row_open.signal == "buy":
            self.order_type = "long"
        elif row_open.signal == "sell":
            self.order_type = "short"
        
        self.current_balance = None
        self.lot = None
        self.leverage = None

    def open_position(self):
        if self.is_backtest:
            pass

    def get_pass_log(self):
        return self.pass_log
    
    def get_combined_log(self):
        combined_fields = {**self.open_log["fields"], **self.close_log["fields"]}
        combined_tags = {**self.open_log["tags"], **self.close_log["tags"]}
        self.combined_log = {
            "fields": combined_fields,
            "measurement": "real_transaction_log",
            "tags": combined_tags
        }

        return self.combined_log

    def set_pass_log(self):
        self.order_cancel_time = datetime.now()
        self.pass_log = {
        'fields': {
            "current_balance": float(self.current_balance),
            "lot": self.lot,
            "leverage": self.leverage,
            "entry_judged_price": float(self.entry_judged_price),
            "entry_judged_time": str(self.entry_judged_time),
            "open_attempt_time": self.open_attempt_time,
            "open_attempt_period": str(self.open_attempt_period),
            "order_cancel_time": str(self.order_cancel_time)
            },
        'measurement': "real_transaction_log",
        'tags': {
            "open_position_id": self.open_position_id,
            "exchange_name": self.exchange_name,
            "asset_name": self.asset_name,
            "order_type": self.order_type,
            "order_status": self.order_status,
            }
        }

    def set_open_log(self, open_log):
        self.entry_time = datetime.now()
        self.order_status = "open"

        self.open_attempt_time = open_log["open_attempt_time"]
        self.open_attempt_period = self.entry_time - self.entry_judged_time

        self.entry_order_method = open_log["order_method"]
        if self.entry_order_method == "maker":
            self.open_transaction_fee = -0.0025  # both open and close are limit order
        elif self.entry_order_method == "taker":
            self.open_transaction_fee = 0.0005

        self.open_transaction_cost = self.open_transaction_fee * self.lot

        self.open_log = {
        'fields': {
            "lot": self.lot,
            "leverage": self.leverage,
            "entry_judged_price": float(self.entry_judged_price),
            "entry_judged_time": str(self.entry_judged_time),
            "entry_time": str(self.entry_time),
            "open_attempt_time": self.open_attempt_time,
            "open_attempt_period": str(self.open_attempt_period),
            "open_transaction_cost": float(self.open_transaction_cost)
            },
        'tags': {
            "open_position_id": self.open_position_id,
            "exchange_name": self.exchange_name,
            "asset_name": self.asset_name,
            "order_type": self.order_type,
            "order_status": self.order_status,
            "order_method": self.entry_order_method, # maker or taker
            }
        }

    def set_close_log(self, close_log):
        # close paramaters is a hash
        self.close_position_id = close_log["close_position_id"]
        self.close_judged_price = close_log["close_judged_price"]
        self.close_judged_time = close_log["close_judged_time"]

        self.close_price = close_log["close_price"]
        self.close_price_difference = self.close_price - self.close_judged_price
        self.close_time = datetime.now()

        self.close_attempt_time = close_log["close_attempt_time"]
        self.close_attempt_period = close_log["close_attempt_period"]

        self.close_order_method = close_log["close_order_method"] # maker or taker
        if self.close_order_method == "maker":
            self.close_transaction_fee = -0.0025  # both open and close are limit order
        elif self.close_order_method == "taker":
            self.close_transaction_fee = 0.0005

        self.close_transaction_cost = self.close_transaction_fee * self.lot
        
        self.total_transaction_cost = self.open_transaction_cost + self.close_transaction_cost  # unit is BTC
        self.open_close_price_difference = self.close_price - self.entry_judged_price
        self.open_close_price_difference_percentage = \
            self.open_close_price_difference / self.entry_judged_price * 100

        self.profit_size = close_log["current_balance"] - self.current_balance

        if self.profit_size > 0:
            self.profit_status = "win"
        else:
            self.profit_status = "lose"

        self.profit_percentage = (self.profit_size / self.current_balance)*100
        
        self.current_balance = close_log["current_balance"]
        self.order_status = "closed"

        self.close_log = {
        'fields': {
            "close_judged_price": float(self.close_judged_price),
            "close_judged_time": str(self.close_judged_time) ,
            "close_price": float(self.close_price),
            "close_price_difference": float(self.close_price_difference), 
            "close_time": str(self.close_time),
            "close_attempt_time": self.close_attempt_time,
            "close_attempt_period" : str(self.close_attempt_period), 
            "profit_size": float(self.profit_size),
            "profit_percentage": float(self.profit_percentage),
            "current_balance": float(self.current_balance),
            },
        'tags': {
            "close_position_id": self.close_position_id,
            "profit_status": self.profit_status,
            "order_status": self.order_status
            }
         }

    def close_position(self, row_close):
        # for summary
        self.close_price = row_close.close
        self.close_time = row_close.Index

        self.price_difference = self.close_price - self.entry_judged_price
        self.price_difference_percentage = ((self.close_price / self.entry_judged_price) - 1)*100

        if self.order_type == "long":
            self.gross_profit = self.close_price - self.entry_judged_price * self.lot * self.leverage
            self.transaction_cost = (self.close_price - self.entry_judged_price) * self.transaction_fee_by_order * self.lot * self.leverage
            self.profit_size = self.gross_profit - self.transaction_cost
        elif self.order_type == "short":
            self.gross_profit = self.entry_judged_price - self.close_price * self.lot * self.leverage
            self.transaction_cost = (self.entry_judged_price - self.close_price) * self.transaction_fee_by_order * self.lot * self.leverage
            self.profit_size = self.gross_profit - self.transaction_cost

        if self.profit_size > 0:
            self.profit_status = "win"
        else:
            self.profit_status = "lose"

        if self.current_balance > 0:
            self.profit_percentage = ((self.profit_size / self.current_balance) + 1 )*100
        elif self.current_balance == 0:
            self.profit_percentage = None
        else:
            profit_percentage = (abs(self.profit_size + self.current_balance) / abs(self.current_balance))
            if self.profit_status == "win":
                self.profit_percentage = profit_percentage
            else:
                self.profit_percentage = -1 * profit_percentage


        self.profit_percentage = (((self.current_balance + self.profit_size) / self.current_balance) - 1)*100
        self.current_balance += self.profit_size

        self.order_status = "closed"

    def generate_transaction_log_for_backtest(self, db_client, summary_id):
        log_dict = {
            "backtest_summary_id": int(summary_id),
            "exchange_name": self.exchange_name,
            "asset_name": self.asset_name,
            "current_balance": float(self.current_balance),
            "entry_time": self.entry_time.to_pydatetime(),
            "close_time": self.close_time.to_pydatetime(),
            "order_status": self.order_status,
            "order_type": self.order_type,
            "profit_status": self.profit_status,
            "entry_price": float(self.entry_price),
            "price_difference": float(self.price_difference),
            "price_difference_percentage": float(self.price_difference_percentage),
            "close_price": float(self.close_price),
            "leverage": float(self.leverage),
            "lot": float(self.lot),
            "transaction_cost": float(self.transaction_cost),
            "profit_size": float(self.profit_size),
            "profit_percentage" : float(self.profit_percentage)
        }
        return log_dict
