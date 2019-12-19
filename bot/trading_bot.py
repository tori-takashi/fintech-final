import ccxt
import pandas as pd
import logging
from datetime import datetime, timedelta

from lib.pandamex import PandaMex
from lib.dataset import Dataset

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

        self.bot_name_with_option = self.build_bot_name(
            self.default_params, self.specific_params)

        if self.is_backtest:
            if self.db_client.is_table_exist(self.bot_name + "_backtest_summary") is not True:
                self.create_backtest_summary()
            if self.db_client.is_table_exist(self.bot_name + "_backtest_params") is not True:
                self.create_backtest_params()
            if self.db_client.is_table_exist(self.bot_name + "_backtest_transaction_log") is not True:
                self.create_backtest_transaction_log()

        self.set_logger()

    def create_backtest_summary(self):
        pass

    def create_backtest_params(self):
        pass

    def create_backtest_transaction_log(self):
        pass

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
            filename = str(duration_days) + "days_" + self.bot_name_with_option
            self.set_log_output_target(filename)

            self.log_params()

            self.calculate_sign_backtest()
            self.run_backtest(csv_output=True, filename=filename)
            self.aggregate_summary()

    def build_bot_name(self, default_params, specific_params):
        # default params
        if self.close_in_do_nothing:
            do_nothing_option = "_do_nothing"
        else:
            do_nothing_option = ""

        if self.inverse_trading:
            inverse_trading_option = "_inverse"
        else:
            inverse_trading_option = ""

        # bot params
        specific_params_option = ""
        for param in list(specific_params.values()):
            specific_params_option += "_" + str(param)

        return default_params["bot_name"] + "_" + default_params["timeframe"] + \
            specific_params_option + do_nothing_option + inverse_trading_option

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
        order_types = ["long", "short"]
        profit_statuses = ["win", "lose"]
        
        self.logger.info("# Stategy Backtest Result")        
        self.log_params()

        self.logger.info("\n## total result")

        total_entries = len(self.closed_positions_df)

        total_sum  = self.closed_positions_df.profit_size.sum()
        total_mean = self.closed_positions_df.profit_size.mean()
        total_std  = self.closed_positions_df.profit_size.std()

        total_average_return_percentage = self.closed_positions_df.profit_percentage.mean()

        total_transaction_cost = self.closed_positions_df.transaction_cost.sum()
        
        self.logger.info("total entry -> " + str(total_entries) + " times")
        self.logger.info("total sum -> $" + str(round(total_sum, 2)))
        self.logger.info("total average -> $" + str(round(total_mean, 2)))
        self.logger.info("total standard deviation -> $" + str(round(total_std, 2)))

        self.logger.info("total average return percentage -> " + str(round(total_average_return_percentage, 2)) + "%")

        self.logger.info("total transaction cost -> $" + str(round(total_transaction_cost, 2)))

        for profit_status in profit_statuses:
            self.logger.info("\n## "+ profit_status + " result")

            entries = len(self.closed_positions_df)
            win_lose_entries = (self.closed_positions_df["profit_status"] == profit_status)
            win_lose_entries_size = win_lose_entries.sum()
            win_lose_col = self.closed_positions_df[(win_lose_entries)]

            # index
            win_lose_rate = (win_lose_entries_size / entries) * 100

            win_lose_sum  = win_lose_col.profit_size.sum()
            win_lose_mean = win_lose_col.profit_size.mean()
            win_lose_std  = win_lose_col.profit_size.std()
                
            win_lose_mean_percentage = win_lose_col.profit_percentage.mean()
            
            self.logger.info(profit_status + " entry -> " + str(win_lose_entries_size) + " times")
            self.logger.info(profit_status + " rate -> " + str(round(win_lose_rate, 2)) + "%")
            self.logger.info(profit_status + " sum -> $" + str(round(win_lose_sum, 2)))
            self.logger.info(profit_status + " average -> $" + str(round(win_lose_mean, 2)))
            self.logger.info(profit_status + " standard deviation -> $" + str(round(win_lose_std, 2)))
            self.logger.info(profit_status + " average return percentage -> " + str(round(win_lose_mean_percentage, 2)) + "%")


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
