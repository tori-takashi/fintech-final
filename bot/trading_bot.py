import ccxt
import pandas as pd
import numpy as np

import logging
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, Float, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relationship

from alembic.migration import MigrationContext
from alembic.operations import Operations

from lib.pandamex import PandaMex
from lib.dataset import Dataset

from model.backtest_params import BacktestParams
from model.backtest_summary import BacktestSummary
from model.backtest_transaction_log import BacktestTransactionLog


class TradingBot:
    def __init__(self, exchange_client, db_client, default_params, specific_params, is_backtest=False):
        # initialize status and settings of bot.
        # if you try backtest, db_client is in need.
        self.is_backtest = is_backtest

        self.exchange_client = exchange_client
        self.db_client = db_client
        self.dataset_manipulator = Dataset(self.exchange_client, self.db_client)

        self.default_params = default_params
        self.extract_default_params(self.default_params)

        self.specific_params = specific_params

        if self.is_backtest:
            if self.db_client.is_table_exist(self.bot_name + "_backtest_summary") is not True:
                self.create_backtest_summary()
            if self.db_client.is_table_exist(self.bot_name + "_backtest_params") is not True:
                self.create_backtest_params()
            if self.db_client.is_table_exist(self.bot_name + "_backtest_transaction_log") is not True:
                self.create_backtest_transaction_log()

        self.set_logger()

    def create_backtest_summary(self):
        table_def = BacktestSummary.__table__
        table_def.name = self.bot_name + "_backtest_summary"
        table_def.create(bind=self.db_client.connector)
        

    def create_backtest_params(self):
        table_def = BacktestParams
        table_def.relation = relationship("BacktestSummary")

        table_def = table_def.__table__

        # add specific params columns
        table_def = self.append_specific_params_column(table_def)
        backtest_summary_id = Column(self.bot_name + "_backtest_summary_id", Integer)
        table_def.append_column(backtest_summary_id)

        table_def.name = self.bot_name + "_backtest_params"
        table_def.create(bind=self.db_client.connector)

        # add foreign key constraint
        ctx = MigrationContext.configure(self.db_client.connector)
        op = Operations(ctx)

        with op.batch_alter_table(self.bot_name + "_backtest_params") as batch_op:
            batch_op.create_foreign_key(
                "fk_summary_params", self.bot_name + "_backtest_summary",
                [self.bot_name + "_backtest_summary_id"], ["id"]
            )


    def create_backtest_transaction_log(self):
        table_def = BacktestTransactionLog
        table_def.relation = relationship("BacktestSummary")

        table_def = table_def.__table__
        backtest_summary_id = Column(self.bot_name + "_backtest_summary_id", Integer)
        table_def.append_column(backtest_summary_id)

        table_def.name = self.bot_name + "_backtest_transaction_log"
        table_def.create(bind=self.db_client.connector)

        # add foreign key constraint
        ctx = MigrationContext.configure(self.db_client.connector)
        op = Operations(ctx)

        with op.batch_alter_table(self.bot_name + "_backtest_transaction_log") as batch_op:
            batch_op.create_foreign_key(
                "fk_summary_log", self.bot_name + "_backtest_summary",
                [self.bot_name + "_backtest_summary_id"], ["id"]
            )

        
    def append_specific_params_column(self, table_def):
        return table_def
        # Need to be oberride
        # return table def

    def extract_default_params(self, default_params):
        # default_params = {
        #    "bot_name" : bot_name, # used in bot name builder for log
        #    "timeframe": integer,
        #    "close_in_do_nothing": close_in_do_nothing,
        #    "inverse_trading": inverse_trading
        # }
        self.bot_name = default_params["bot_name"]
        self.timeframe = default_params["timeframe"]
        self.close_in_do_nothing = default_params["close_in_do_nothing"]
        self.inverse_trading = default_params["inverse_trading"]

    def run(self, duration_days=90):
        start_time = datetime.now() - timedelta(days=duration_days)
        end_time = datetime.now()

        self.ohlcv_df = self.dataset_manipulator.get_ohlcv(self.timeframe, start_time, end_time)

        self.calculate_metrics()
        if self.is_backtest:
            self.calculate_sign_backtest()
            self.run_backtest(csv_output=False)
            self.aggregate_summary()

    def set_logger(self):
        self.logger = logging.getLogger(self.bot_name)
        self.logger.setLevel(10)

        sh = logging.StreamHandler()
        self.logger.addHandler(sh)

        formatter_sh = logging.Formatter(
            '[%(levelname)s] %(message)s')
        sh.setFormatter(formatter_sh)

    def set_log_output_target(self, filename):
        logging.basicConfig(
            filename="./log/" + filename + ".log",
            filemode='a',
            level=logging.INFO
        )

    def log_params(self):
        self.logger.info("\n# hyper parameters")
        self.logger.info("default hyperparameters")
        for k, v in self.default_params.items():
            self.logger.info(k + " => " + str(v))

        self.logger.info("bot hyperparameters")
        for k, v in self.specific_params.items():
            self.logger.info(k + " => " + str(v))


    def calculate_lot(self):
        return 1
        # if you need, you can override

    def calculate_metrics(self):
        pass
        # need to override

    def calculate_sign(self):
        return "signal"
        # need to override
        # return ["buy", "sell", "do_nothing"]

    def calculate_sign_backtest(self):
        pass
        # need to override
        # return dataframe with ["buy", "sell", "do_nothing"]

    def run_backtest(self, csv_output=False, filename=""):
        record_column = [
            "entry_timestamp",
            "close_timestamp",
            "status",
            "order_type",
            "profit_status",
            "entry_price",
            "close_price",
            "lot",
            "transaction_cost",
            "profit_size",
            "profit_percentage"
        ]
        # [close_in_do_nothing option]
        # True  => close position when the [buy/sell] signal change to the [do_nothing/opposite] signal
        # False => close position when the [buy/sell] signal change to the opposite signal

        # refer to signal then calculate
        # having only one order

        position = None
        contain_signal_df = self.ohlcv_df

        self.closed_positions_df = pd.DataFrame(columns=record_column)

        for row in contain_signal_df.itertuples():
            self.logger.info(str(row.timestamp) + " : open price: $" +
                             str(row.open) + " close price: $" + str(row.close))

            if row.signal == "buy":
                if position is not None and position.order_type == "long":
                    # inverse => close position
                    if self.inverse_trading:
                        position.close_position(row)
                        self.closed_positions_df = self.closed_positions_df.append(
                            position.set_summary_df(), ignore_index=True)
                        self.logging_close(position)

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
                        self.closed_positions_df = self.closed_positions_df.append(
                            position.set_summary_df(), ignore_index=True)
                        self.logging_close(position)

                        position = None
                else:
                    lot = self.calculate_lot()
                    # inverse => open short position
                    if self.inverse_trading:
                        position = OrderPosition(
                            row, "short", lot, is_backtest=True)
                    else:
                        # normal => open long position
                        position = OrderPosition(
                            row, "long", lot, is_backtest=True)
                    self.logging_entry(position)

            elif row.signal == "sell":
                if position is not None and position.order_type == "long":
                    # inverse => still holding
                    if self.inverse_trading:
                        pass
                    # normal => close position
                    else:
                        position.close_position(row)
                        self.closed_positions_df = self.closed_positions_df.append(
                            position.set_summary_df(), ignore_index=True)
                        self.logging_close(position)

                        position = None

                elif position is not None and position.order_type == "short":
                    # inverse => close position
                    if self.inverse_trading:
                        position.close_position(row)
                        self.closed_positions_df = self.closed_positions_df.append(
                            position.set_summary_df(), ignore_index=True)
                        self.logging_close(position)

                        position = None

                    # normal => still holding
                    else:
                        pass

                else:
                    lot = self.calculate_lot()
                    # inverse => open long position
                    if self.inverse_trading:
                        position = OrderPosition(
                            row, "long", lot, is_backtest=True)
                    else:
                        # normal => open short position
                        position = OrderPosition(
                            row, "short", lot, is_backtest=True)
                    self.logging_entry(position)

            elif row.signal == "do_nothing":
                if self.close_in_do_nothing:
                    # if do nothing option is true
                    # and you get do nothing from signal, then close out the position
                    if position is not None and position.order_type == "long":
                        # close position
                        position.close_position(row)
                        self.closed_positions_df = self.closed_positions_df.append(
                            position.set_summary_df(), ignore_index=True)
                        self.logging_close(position)

                        position = None

                    elif position is not None and position.order_type == "short":
                        # close position
                        position.close_position(row)
                        self.closed_positions_df = self.closed_positions_df.append(
                            position.set_summary_df(), ignore_index=True)
                        self.logging_close(position)

                        position = None

        if csv_output:
            self.closed_positions_df.to_csv(
                "log/transaction_log_" + filename + ".csv")

    def logging_entry(self, position):
        self.logger.info("  Entry " + position.order_type +
                         " at $" + str(position.entry_price))

    def logging_close(self, position):
        self.logger.info("  Close " + position.order_type +
                         " position at $" + str(position.close_price))
        if position.profit_status == "win":
            self.logger.info(
                "  $" + str(abs(position.profit_size)) + " profit")
        else:
            self.logger.info(
                "  $" + str(abs(position.profit_size)) + " loss")

    def aggregate_summary(self):
        
        
        for profit_status in profit_statuses:
            
        for order_type in order_types:
            self.logger.info("\n## "+ order_type + " result")

            order = (self.closed_positions_df["order_type"] == order_type)
            order_col = self.closed_positions_df[order]
            
            # index
            order_entries = order.sum()

            order_sum  = order_col.profit_size.sum()
            order_mean = order_col.profit_size.mean()
            order_std = order_col.profit_size.std()
            
            order_average_return_percentage = order_col.profit_percentage.mean()

            self.logger.info(order_type + " entry -> " + str(order_entries) + " times")
            self.logger.info(order_type + " sum -> $" + str(round(order_sum, 2)))
            self.logger.info(order_type + " average -> $" + str(round(order_mean, 2)))
            self.logger.info(order_type + " standard deviation -> $" + str(round(order_std, 2)))
            self.logger.info(order_type + " average return percentage -> " + str(round(order_average_return_percentage, 2)) + "%")

            for profit_status in profit_statuses:
                self.logger.info("\n### " + order_type+ " & " + profit_status + " result")

                win_lose_entries = (self.closed_positions_df["profit_status"] == profit_status)
                order_win_lose_col = self.closed_positions_df[(order) & (win_lose_entries)]

                # index
                order_win_lose_entries = ((order) & (win_lose_entries)).sum()
                order_win_lose_rate = (order_win_lose_entries / order_entries) * 100

                order_win_lose_sum  = order_win_lose_col.profit_size.sum()
                order_win_lose_mean = order_win_lose_col.profit_size.mean()
                order_win_lose_std  = order_win_lose_col.profit_size.std()
                
                order_win_lose_mean_percentage = order_win_lose_col.profit_percentage.mean()
            
                self.logger.info(order_type + " " + profit_status + " entry -> " + str(order_win_lose_entries) + " times")
                self.logger.info(order_type + " " + profit_status + " rate -> " + str(round(order_win_lose_rate, 2)) + "%")
                self.logger.info(order_type + " " + profit_status + " sum -> $" + str(round(order_win_lose_sum, 2)))
                self.logger.info(order_type + " " + profit_status + " average -> $" + str(round(order_win_lose_mean, 2)))
                self.logger.info(order_type + " " + profit_status + " standard deviation -> $" + str(round(order_win_lose_std, 2)))
                self.logger.info(order_type + " " + profit_status + " average percentage -> " + str(round(order_win_lose_mean_percentage, 2)) + "%")

    def build_summary(self, closed_position):
        pass

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
            profit_status + "_standard_deviation".
            profit_status + "_skewness",
            profit_status + "_kurtosis",
            profit_status + "_median",
            profit_status + "_return_percentage",
            profit_status + "_average_percentage",
            profit_status + "_standard_deviation_percentage",
            profit_status + "_skewness_percentage",
            profit_status + "_transaction_cost",
            profit_status + "_consective",
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
            
            win_lose_consective = self.build_consecutive(profit_status)

            win_lose_consecutive_max_entry = win_lose_consective["consective_max_entry"]
            win_lose_consecutive_average_entry = win_lose_consective["consective_average_entry"]
            win_lose_consecutive_total_profit_loss = win_consective["consecutive_df"].profit_size.sum()

            win_lose_summary_data = [
            win_lose_entry,
            win_lose_rate,
            win_lose_return,
            win_lose_average,
            win_lose_standard_deviation.
            win_lose_skewness,
            win_lose_kurtosis,
            win_lose_median,
            win_lose_return_percentage,
            win_lose_average_percentage,
            win_lose_standard_deviation_percentage,
            win_lose_skewness_percentage,
            win_lose_transaction_cost,
            win_lose_consective,
            win_lose_consecutive_max_entry,
            win_lose_consecutive_average_entry,
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

    def build_consective(self, profit_status):
        current_start_index = 0
        current_end_index = 0

        max_start_index = 0
        max_end_index = 0

        consective_win_lose_entries = []

        profit_status_df = self.closed_positions_df.loc[:,["profit_status"]]
        profit_status_np = id_profit_status_df.to_numpy(copy=True)

        # for loop
        for row_id, row in enumrate(profit_status_np):
            if row[row_id] == profit_status:
                if current_start_index == 0:
                    current_start_index = row[0]
            else:
                current_end_index = row[0]
                consective_win_lose_entries.append(current_end_index - current_start_index)
                if current_end_index - current_start_index < max_end_index - max_start_index:
                    max_start_index = current_start_index
                    max_end_index = current_end_index

                current_start_index = 0
                current_end_index = 0

        consective_max_entry = np.max(consective_win_lose_entries)
        consective_average_entry = np.mean(consective_win_lose_entries)

        return_hash = {
            "consecutive_df": self.closed_positions_df.loc[max_start_index:max_end_index],
            "consecutive_max_entry": consective_max_entry,
            "consective_average_entry": consective_average_entry
        }

        return return_hash

    def build_long_short_summary(self):
        order_types = ["long", "short"]
        pass

    def build_combined_summary(self):
        combine_statuses = ["win_long", "win_short", "lose_long", "lose_short"]
        pass


class OrderPosition:
    def __init__(self, row, order_type, lot, is_backtest=False):
        self.transaction_fee_by_order = 0.0005
        self.status = "open"

        self.order_type = order_type
        # order_type = ["long", "short"]
        self.is_backtest = is_backtest
        self.lot = lot

        # for summary
        self.entry_price = row.close
        self.entry_timestamp = row.timestamp
        self.close_price = 0
        # self.close_timestamp

        self.open_position()

    def open_position(self):
        if self.is_backtest:
            pass

    def close_position(self, row_execution):
        # for summary
        self.close_price = row_execution.close
        self.close_timestamp = row_execution.timestamp

        self.transaction_cost = self.close_price * self.transaction_fee_by_order

        if self.order_type == "long":
            self.profit_size = ((self.close_price -
                                 self.entry_price) - self.transaction_cost) * self.lot
        elif self.order_type == "short":
            self.profit_size = ((self.entry_price -
                                 self.close_price) - self.transaction_cost) * self.lot

        if self.profit_size > 0:
            self.profit_status = "win"
        else:
            self.profit_status = "lose"

        self.status = "closed"
        if self.is_backtest:
            pass

    def set_summary_df(self):
        record_column = [
            "entry_timestamp",
            "close_timestamp",
            "status",
            "order_type",
            "profit_status",
            "entry_price",
            "close_price",
            "lot",
            "transaction_cost",
            "profit_size",
            "profit_percentage"
        ]
        self.position = pd.Series([
            self.entry_timestamp,
            self.close_timestamp,
            self.status,
            self.order_type,
            self.profit_status,
            self.entry_price,
            self.close_price,
            self.lot,
            self.transaction_cost,
            self.profit_size,
            (self.profit_size / self.entry_price)*100
        ], index=record_column)
        return self.position
