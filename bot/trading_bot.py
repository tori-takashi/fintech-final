import ccxt
import pandas as pd
import numpy as np

import logging
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, Float, Table, MetaData
from sqlalchemy import update
from sqlalchemy.orm import relationship, mapper

from alembic.migration import MigrationContext
from alembic.operations import Operations

from lib.pandamex import PandaMex
from lib.dataset import Dataset

from model.backtest_management import BacktestManagement
from model.backtest_summary import BacktestSummary
from model.backtest_transaction_log import BacktestTransactionLog


class TradingBot:
    def __init__(self, default_params, specific_params, db_client, exchange_client=None, is_backtest=False):
        # initialize status and settings of bot.
        # if you try backtest, db_client is in need.

        self.exchange_client = exchange_client
        self.db_client = db_client

        self.default_params = default_params
        self.extract_default_params(self.default_params)

        self.specific_params = specific_params

        self.combined_params = dict(**self.default_params, **self.specific_params)

        self.is_backtest = is_backtest
        
        if is_backtest:
            # for params table
            self.backtest_management_table_name = self.bot_name + "_backtest_management"

            # backtest configure
            self.initial_balance = 100.0  # USD
            self.account_currency = "USD"
        
            self.dataset_manipulator = Dataset(self.db_client, self.exchange_client)

            if self.db_client.is_table_exist(self.backtest_management_table_name) is not True:
                self.create_backtest_management_table()


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
        self.timeframe = default_params["timeframe"]
        self.close_position_on_do_nothing = default_params["close_position_on_do_nothing"]
        self.inverse_trading = default_params["inverse_trading"]

    def run(self, backtest_start_time=datetime.now() - timedelta(days=90), backtest_end_time=datetime.now()):
        self.ohlcv_df = self.dataset_manipulator.get_ohlcv(self.timeframe, backtest_start_time, backtest_end_time)
        self.ohlcv_with_metrics = self.calculate_metrics_for_backtest()

        if self.is_backtest:
            self.backtest_start_time = backtest_start_time
            self.backtest_end_time = backtest_end_time

            self.ohlcv_with_signals = self.calculate_signs_for_backtest()
            
            self.summary_id = self.init_summary()
            
            self.run_backtest()
            self.insert_params_management()

    def insert_params_management(self):
        backtest_management = self.backtest_management_table()

        self.combined_params["backtest_summary_id"] = int(self.summary_id)
        del self.combined_params["bot_name"]

        self.db_client.connector.execute(backtest_management.insert().values(self.combined_params))

    def set_specific_params(self):
        # need to be override
        pass

    def init_summary(self):
        summary = BacktestSummary()
        summary.bot_name = self.bot_name
        summary.initial_balance = self.initial_balance
        summary.account_currency = self.account_currency

        self.db_client.session.add(summary)
        self.db_client.session.commit()
        # [FIXME] only for single task processing, unable to parallel process
        return int(self.db_client.get_last_row("backtest_summary").index.array[0])
        
    def calculate_lot(self):
        return 1 # 100 %
        # if you need, you can override
        # default is invest all that you have

    def calculate_leverage(self):
        return 1 # 1 times
        # if you need, you can override

    def calculate_metric(self):
        return "metric"

    def calculate_metrics_for_backtest(self):
        return "ohlcv_with_metric_dataframe"
        # need to override

    def calculate_sign(self):
        return "signal"
        # need to override
        # return ["buy", "sell", "do_nothing"]

    def calculate_signs_for_backtest(self):
        return "ohlcv_with_signal_data"
        # need to override
        # return dataframe with ["buy", "sell", "do_nothing"]

    def run_backtest(self):
        # refer to signal then judge investment
        # keep one order at most

        position = None
        current_balance = self.initial_balance

        for row in self.ohlcv_with_signals.itertuples(): # self.ohlcv_with_signals should be dataframe
            if row.signal == "buy":
                if position is not None and position.order_type == "long":
                    # inverse => close position
                    if self.inverse_trading:
                        position.close_position(row)
                        position.add_transaction_log(self.db_client, self.summary_id)
                        current_balance = position.current_balance
                        position = None
                    # normal => still holding
                    else:
                        pass

                elif position is not None and position.order_type == "short":
                    # inverse => still holding
                    if self.inverse_trading:
                        pass
                    # normal => close position
                    else:
                        position.close_position(row)
                        position.add_transaction_log(self.db_client, self.summary_id)
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
                        position.add_transaction_log(self.db_client, self.summary_id)
                        current_balance = position.current_balance
                        position = None

                elif position is not None and position.order_type == "short":
                    # inverse => close position
                    if self.inverse_trading:
                        position.close_position(row)
                        position.add_transaction_log(self.db_client, self.summary_id)
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
                        position.add_transaction_log(self.db_client, self.summary_id)
                        current_balance = position.current_balance
                        position = None

        self.db_client.session.commit()
        # bulk insert transaction log to table


    def build_summary(self, closed_position):
        total_summary_series = self.build_total_summary()
        long_short_summary_series = self.build_long_short_summary()
        win_lose_summary_series = self.build_win_lose_summary()
        combined_summary_series = self.build_combined_summary()
        other_summary_seris = self.build_other_summary()


    def build_total_summary(self):
        total_summary_column = [
        "total_entries",
        "total_return",
        "total_average",
        "total_standard_deviation",
        "total_skewness",
        "total_kurtosis",
        "total_median",
        "total_return_percentage",
        "total_average_percentage",
        "total_standard_deviation_percentage",
        "total_skewness_percentage",
        "total_kurtosis_percentage",
        "total_median_percentage",
        "total_transaction_cost"
        ]

        total_entries = len(self.closed_positions_df)

        total_return  = self.closed_positions_df.profit_size.sum()
        total_average = self.closed_positions_df.profit_size.mean()
        total_standard_deviation  = self.closed_positions_df.profit_size.std()
        total_skewness = self.closed_positions_df.profit_size.skew()
        total_kurtosis = self.closed_positions_df.profit_size.kurt()
        total_median = self.closed_positions_df.profit_size.median()

        total_return_percentage  = self.closed_positions_df.profit_percentage.sum()
        total_average_percentage = self.closed_positions_df.profit_percentage.mean()
        total_standard_deviation_percentage  = self.closed_positions_df.profit_percentage.std()
        total_skewness_percentage = self.closed_positions_df.profit_percentage.skew()
        total_kurtosis_percentage = self.closed_positions_df.profit_percentage.kurt()
        total_median_percentage = self.closed_positions_df.profit_percentage.median()

        total_transaction_cost = self.closed_positions_df.transaction_cost.sum()

        total_summary_data = [
        total_entries,
        total_return,
        total_average,
        total_standard_deviation,
        total_skewness,
        total_kurtosis,
        total_median,
        total_return_percentage,
        total_average_percentage,
        total_standard_deviation_percentage,
        total_skewness_percentage,
        total_kurtosis_percentage,
        total_median_percentage,
        total_transaction_cost
        ]

        return pd.Series(total_summary_data, index=total_summary_column)

    def build_win_lose_summary(self):
        profit_statuses = ["win", "lose"]
        for profit_status in profit_statuses:
            win_lose_summary_columns = [
            profit_status + "_entry",
            profit_status + "_rate",
            profit_status + "_return",
            profit_status + "_average",
            profit_status + "_standard_deviation",
            profit_status + "_skewness",
            profit_status + "_kurtosis",
            profit_status + "_median",
            profit_status + "_return_percentage",
            profit_status + "_average_percentage",
            profit_status + "_standard_deviation_percentage",
            profit_status + "_skewness_percentage",
            profit_status + "_transaction_cost",
            profit_status + "_consecutive",
            profit_status + "_consecutive_max_entry",
            profit_status + "_consecutive_average_entry"
            ]

            win_lose_entries_condition = (self.closed_positions_df["profit_status"] == profit_status)
            win_lose_row = self.closed_positions_df[(win_lose_entries_condition)]

            win_lose_entry = len(win_lose_row)
            win_lose_rate = (win_lose_entry / len(self.closed_positions_df)) * 100

            win_lose_return  = win_lose_row.profit_size.sum()
            win_lose_average = win_lose_row.profit_size.mean()
            win_lose_standard_deviation  = win_lose_row.profit_size.std()
            win_lose_skewness = win_lose_row.profit_size.skew()
            win_lose_kurtosis = win_lose_row.profit_size.kurt()
            win_lose_median = win_lose_row.profit_size.median()

            win_lose_return_percentage  = win_lose_row.profit_percentage.sum()
            win_lose_average_percentage = win_lose_row.profit_percentage.mean()
            win_lose_standard_deviation_percentage  = win_lose_row.profit_percentage.std()
            win_lose_skewness_percentage = win_lose_row.profit_percentage.skew()
            win_lose_kurtosis_percentage = win_lose_row.profit_percentage.kurt()
            win_lose_median_percentage = win_lose_row.profit_percentage.median()

            win_lose_transaction_cost = win_lose_row.transaction_cost.sum()
            
            win_lose_consecutive = self.build_consecutive(profit_status)

            win_lose_consecutive_max_entry = win_lose_consecutive["consecutive_max_entry"]
            win_lose_consecutive_average_entry = win_lose_consecutive["consecutive_average_entry"]
            win_lose_consecutive_total_profit_loss = win_lose_consecutive["consecutive_df"].profit_size.sum()

            win_lose_summary_data = [
            win_lose_entry,
            win_lose_rate,
            win_lose_return,
            win_lose_average,
            win_lose_standard_deviation,
            win_lose_skewness,
            win_lose_kurtosis,
            win_lose_median,
            win_lose_return_percentage,
            win_lose_average_percentage,
            win_lose_standard_deviation_percentage,
            win_lose_skewness_percentage,
            win_lose_kurtosis_percentage,
            win_lose_median_percentage,
            win_lose_transaction_cost,
            win_lose_consecutive,
            win_lose_consecutive_max_entry,
            win_lose_consecutive_average_entry
            ]

            if profit_status == "win":
                win_max_profit = win_lose_row.profit_size.max()
                win_max_profit_percentage = win_lose_row.profit_percentage.max()
                
                win_lose_summary_columns.append([
                    profit_status + "_consecutive_total_profit",
                    "win_max_profit",
                    "win_max_profit_percentage"
                ])
                win_lose_summary_data.append([
                    win_lose_consecutive_total_profit_loss,
                    win_max_profit,
                    win_max_profit_percentage
                ])

            elif profit_status == "lose":
                lose_max_loss = win_lose_row.profit_size.min()
                lose_max_loss_percentage = win_lose_row.profit_percentage.min()

                win_lose_summary_columns.append([
                    profit_status + "_consecutive_total_loss",
                    "lose_max_loss",
                    "lose_max_loss_percentage"
                ])
                win_lose_summary_data.append([
                    win_lose_consecutive_total_profit_loss,
                    lose_max_loss,
                    lose_max_loss_percentage
                ])

        return pd.Series(win_lose_summary_data, index=win_lose_summary_columns)

    def build_consecutive(self, profit_status):
        current_start_index = 0
        current_end_index = 0

        max_start_index = 0
        max_end_index = 0

        consecutive_win_lose_entries = []

        profit_status_df = self.closed_positions_df.loc[:,["profit_status"]]
        profit_status_np = profit_status_df.to_numpy(copy=True)

        # for loop
        for row_id, row in enumerate(profit_status_np):
            if row[row_id] == profit_status:
                if current_start_index == 0:
                    current_start_index = row[0]
            else:
                current_end_index = row[0]
                consecutive_win_lose_entries.append(current_end_index - current_start_index)
                if current_end_index - current_start_index < max_end_index - max_start_index:
                    max_start_index = current_start_index
                    max_end_index = current_end_index

                current_start_index = 0
                current_end_index = 0

        consecutive_max_entry = np.max(consecutive_win_lose_entries)
        consecutive_average_entry = np.mean(consecutive_win_lose_entries)

        return_hash = {
            "consecutive_df": self.closed_positions_df.loc[max_start_index:max_end_index],
            "consecutive_max_entry": consecutive_max_entry,
            "consecutive_average_entry": consecutive_average_entry
        }

        return return_hash

    def build_long_short_summary(self):
        order_types = ["long", "short"]

        for order_type in order_types:
            long_short_entries_condition = (self.closed_positions_df["order_type"] == order_type)
            long_short_row = self.closed_positions_df[(long_short_entries_condition)]

            long_short_summary_columns = [
            order_type + "_entry",
            order_type + "_rate",
            order_type + "_return",
            order_type + "_average",
            order_type + "_standard_deviation",
            order_type + "_skewness",
            order_type + "_kurtosis",
            order_type + "_median",
            order_type + "_return_percentage",
            order_type + "_average_percentage",
            order_type + "_standard_deviation_percentage",
            order_type + "_skewness_percentage",
            order_type + "_max_profit",
            order_type + "_max_loss"
            ]

            long_short_entry = len(long_short_row)
            long_short_rate = (long_short_entry / len(self.closed_positions_df)) * 100

            long_short_return  = long_short_row.profit_size.sum()
            long_short_average = long_short_row.profit_size.mean()
            long_short_standard_deviation  = long_short_row.profit_size.std()
            long_short_skewness = long_short_row.profit_size.skew()
            long_short_kurtosis = long_short_row.profit_size.kurt()
            long_short_median = long_short_row.profit_size.median()

            long_short_return_percentage  = long_short_row.profit_percentage.sum()
            long_short_average_percentage = long_short_row.profit_percentage.mean()
            long_short_standard_deviation_percentage  = long_short_row.profit_percentage.std()
            long_short_skewness_percentage = long_short_row.profit_percentage.skew()
            long_short_kurtosis_percentage = long_short_row.profit_percentage.kurt()
            long_short_median_percentage = long_short_row.profit_percentage.median()
            
            long_short_max_profit = long_short_row.profit_size.max()
            long_short_max_profit_percentage = long_short_row.profit_percentage.max()

            long_short_max_loss = long_short_row.profit_size.min()
            long_short_max_loss_percentage = long_short_row.profit_percentage.min()

            long_short_summary_data = [
            long_short_entry,
            long_short_rate,
            long_short_return,
            long_short_average,
            long_short_standard_deviation,
            long_short_skewness,
            long_short_kurtosis,
            long_short_median,
            long_short_return_percentage,
            long_short_average_percentage,
            long_short_standard_deviation_percentage,
            long_short_skewness_percentage,
            long_short_kurtosis_percentage,
            long_short_median_percentage,
            long_short_max_profit,
            long_short_max_profit_percentage,
            long_short_max_loss,
            long_short_max_loss_percentage
            ]

            return pd.Series(long_short_summary_data, index=long_short_summary_columns)


    def build_combined_summary(self):
        order_types = ["long", "short"]
        profit_statuses = ["win", "lose"]
        for order_type in order_types:
            for profit_status in profit_statuses:
                win_lose_entries_condition = (self.closed_positions_df["profit_status"] == profit_status)
                long_short_entries_condition = (self.closed_positions_df["order_type"] == order_type)

                combined_row = self.closed_positions_df[
                    (long_short_entries_condition) & (win_lose_entries_condition)]

                combined_summary_column = [
                profit_status + "_" + order_type + "_entries",
                profit_status + "_" + order_type + "_return",
                profit_status + "_" + order_type + "_average",
                profit_status + "_" + order_type + "_standard_deviation",
                profit_status + "_" + order_type + "_skewness",
                profit_status + "_" + order_type + "_kurtosis",
                profit_status + "_" + order_type + "_median",
                profit_status + "_" + order_type + "_return_percentage",
                profit_status + "_" + order_type + "_average_percentage",
                profit_status + "_" + order_type + "_standard_deviation_percentage",
                profit_status + "_" + order_type + "_skewness_percentage",
                profit_status + "_" + order_type + "_kurtosis_percentage",
                profit_status + "_" + order_type + "_median_percentage",
                ]

                profit_order_entries = len(combined_row)

                profit_order_return  = combined_row.profit_size.sum()
                profit_order_average = combined_row.profit_size.mean()
                profit_order_standard_deviation  = combined_row.profit_size.std()
                profit_order_skewness = combined_row.profit_size.skew()
                profit_order_kurtosis = combined_row.profit_size.kurt()
                profit_order_median = combined_row.profit_size.median()

                profit_order_return_percentage  = combined_row.profit_percentage.sum()
                profit_order_average_percentage = combined_row.profit_percentage.mean()
                profit_order_standard_deviation_percentage  = combined_row.profit_percentage.std()
                profit_order_skewness_percentage = combined_row.profit_percentage.skew()
                profit_order_kurtosis_percentage = combined_row.profit_percentage.kurt()
                profit_order_median_percentage = combined_row.profit_percentage.median()

                combined_summary_data = [
                profit_order_entries,
                profit_order_return,
                profit_order_average,
                profit_order_standard_deviation,
                profit_order_skewness,
                profit_order_kurtosis,
                profit_order_median,
                profit_order_return_percentage,
                profit_order_average_percentage,
                profit_order_standard_deviation_percentage,
                profit_order_skewness_percentage,
                profit_order_kurtosis_percentage,
                profit_order_median_percentage
                ]

                return pd.Series(combined_summary_data, index=combined_summary_column)

    def other_summary_seris(self):
        other_column = [
        "bot_name",
        "initial_deposit",
        "account_currency",
        "profit_factor",
        "recovery_factor",
        "absolute_drawdown",
        "maximal_drawdown",
        "relative_drawdown"
        ]
        
        win_entries_condition = (self.closed_positions_df["profit_status"] == "win")
        win_row = self.closed_positions_df[(win_entries_condition)]
        
        lose_entries_condition = (self.closed_positions_df["profit_status"] == "lose")
        lose_row = self.closed_positions_df[(lose_entries_condition)]

        #bot_name = self.bot_name
        #initial_deposit
        #account_currency
        #profit_factor = win_row.profit_size.sum() / abs(lose_row.profit_size.sum())
        #recovery_factor
        #absolute_drawdown
        #maximal_drawdown
        #relative_drawdown
        


class OrderPosition:
    def __init__(self, row_open, order_type, current_balance, lot, leverage, is_backtest=False):
        self.is_backtest = is_backtest

        self.transaction_fee_by_order = 0.0005 # profit * transaction fee
        
        # for transaction log
        self.order_status = "open"

        self.exchange_name = row_open.exchange_name
        self.asset_name = row_open.asset_name
        self.current_balance = current_balance

        self.entry_price = row_open.close
        self.entry_time = row_open.Index

        self.order_type = order_type
        self.lot = lot
        self.leverage = leverage

        self.open_position()

    def open_position(self):
        if self.is_backtest:
            pass

    def close_position(self, row_close):
        # for summary
        self.close_price = row_close.close
        self.close_time = row_close.Index

        self.price_difference = self.close_price - self.entry_price
        self.price_difference_percentage = ((self.close_price - self.entry_price) / self.entry_price) - 1

        self.transaction_cost = self.close_price * self.transaction_fee_by_order

        if self.order_type == "long":
            self.profit_size = ((self.close_price -
                                 self.entry_price) - self.transaction_cost) * self.lot * self.leverage
        elif self.order_type == "short":
            self.profit_size = ((self.entry_price -
                                 self.close_price) - self.transaction_cost) * self.lot * self.leverage

        self.current_balance += self.profit_size
        self.profit_percentage = ((self.current_balance + self.profit_size) / self.current_balance) - 1

        if self.profit_size > 0:
            self.profit_status = "win"
        else:
            self.profit_status = "lose"

        self.order_status = "closed"
        if self.is_backtest:
            pass

    def add_transaction_log(self, db_client, summary_id):
        log = BacktestTransactionLog()

        log.backtest_summary_id = int(summary_id)

        log.exchange_name = self.exchange_name
        log.asset_name = self.asset_name
        log.current_balance = float(self.current_balance)

        log.entry_time = self.entry_time.to_pydatetime()
        log.holding_time = self.close_time - self.entry_time
        log.close_time = self.close_time.to_pydatetime()

        log.order_status = self.order_status
        log.order_type = self.order_type
        log.profit_status = self.profit_status

        log.entry_price = float(self.entry_price)
        log.price_difference = float(self.price_difference)
        log.price_difference_percentage = float(self.price_difference_percentage)
        log.close_price = float(self.close_price)

        log.leverage = float(self.leverage)
        log.lot = float(self.lot)

        log.transaction_cost = float(self.transaction_cost)
        log.profit_size = float(self.profit_size)
        log.profit_percentage = float(self.profit_percentage)

        db_client.session.add(log)