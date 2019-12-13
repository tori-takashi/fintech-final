import ccxt
import pandas as pd
import logging
from datetime import datetime, timedelta

from lib.pandamex import PandaMex


class TradingBot:
    def __init__(self, exchange_client, is_backtest=False, bot_name="trading_bot",
                 timeframe="1m", close_in_do_nothing=True, inverse_trading=False):
        # default hyperparameter
        self.timeframe = timeframe
        self.close_in_do_nothing = close_in_do_nothing
        self.inverse_trading = inverse_trading
        self.lot = 1

        if close_in_do_nothing:
            do_nothing_option = "_do_nothing"
        else:
            do_nothing_option = ""

        if inverse_trading:
            inverse_trading_option = "_inverse"
        else:
            inverse_trading_option = ""

        self.bot_name = bot_name + do_nothing_option + inverse_trading_option

        self.is_backtest = is_backtest

        self.exchange_client = exchange_client
        self.client = exchange_client.client

        # logger settings
        self.logger = logging.getLogger(self.bot_name)
        self.logger.setLevel(10)

        sh = logging.StreamHandler()
        self.logger.addHandler(sh)

        formatter_sh = logging.Formatter(
            '[%(levelname)s] %(message)s')
        sh.setFormatter(formatter_sh)

        logging.basicConfig(
            filename="./log/" + self.bot_name + ".log",
            filemode='a',
            level=logging.INFO
        )

        self.logger.info("default hyper parameters")
        self.logger.info("close_in_do_nothing : " +
                         str(self.close_in_do_nothing))
        self.logger.info("inverse_trading : " +
                         str(self.inverse_trading))
        self.logger.info("lot size : " + str(self.lot))

    def run(self, duration_days=None):
        if duration_days is not None:
            start_time = datetime.now() - timedelta(days=duration_days)
            end_time = datetime.now()
            self.ohlcv_df = self.init_ohlcv_data(
                start_time=start_time, end_time=end_time)
        else:
            self.ohlcv_df = self.init_ohlcv_data()

        self.calculate_metrics()
        if self.is_backtest:
            self.calculate_sign_backtest()
            self.run_backtest()
            self.aggregate_summary()

    def calculate_lot(self):
        return 1

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

    def init_ohlcv_data(self, start_time=datetime.now() - timedelta(days=30), end_time=datetime.now()):
        self.start_time = start_time
        self.end_time = end_time

        self.stock_duration = end_time - start_time

        if self.exchange_client.name == "bitmex":
            ohlcv_df = PandaMex(self.client).fetch_ohlcv(
                timeframe=self.timeframe, start_time=self.start_time, end_time=self.end_time)
            # fetch ohlcv data
            return PandaMex.to_timestamp(ohlcv_df)

    def run_backtest(self):
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
            "profit_size"
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
                    # still holding
                    pass
                elif position is not None and position.order_type == "short":
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
                    # close position
                    position.close_position(row)
                    self.closed_positions_df = self.closed_positions_df.append(
                        position.set_summary_df(), ignore_index=True)
                    self.logging_close(position)

                    position = None

                elif position is not None and position.order_type == "short":
                    # still holding
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
        self.logger.info("# Stategy Backtest Result")

        for order_type in order_types:
            self.logger.info("\n## entry " + order_type + " result")

            order_entries = (
                self.closed_positions_df["order_type"] == order_type).sum()

            order_winning_entries = ((self.closed_positions_df["order_type"] == order_type) & (
                self.closed_positions_df["profit_status"] == "win")).sum()
            order_winning_rate = (order_winning_entries / order_entries) * 100

            order_return = self.closed_positions_df[self.closed_positions_df["order_type"] == order_type].profit_size.sum(
            )
            order_win = self.closed_positions_df[(self.closed_positions_df["order_type"] == order_type) & (
                self.closed_positions_df["profit_status"] == "win")].profit_size.sum()
            order_lose = self.closed_positions_df[(self.closed_positions_df["order_type"] == order_type) & (
                self.closed_positions_df["profit_status"] == "lose")].profit_size.sum()

            order_average_return = order_return / order_entries
            self.logger.info(order_type + " order entry -> " +
                             str(order_entries) + " times")
            self.logger.info(order_type + " order winning rate -> " +
                             str(round(order_winning_rate, 2)) + "%")
            self.logger.info(
                order_type + " order return -> $" + str(order_return))
            self.logger.info(order_type + " order win -> $" + str(order_win))
            self.logger.info(order_type + " order lose -> $" + str(order_lose))
            self.logger.info(order_type + " order average return -> $" +
                             str(round(order_average_return, 2)))

        self.logger.info("\n## total record")
        total_entries = len(self.closed_positions_df)

        total_winning_entries = (
            self.closed_positions_df["profit_status"] == "win").sum()
        total_winning_rate = (total_winning_entries / total_entries) * 100

        total_return = self.closed_positions_df.profit_size.sum()
        total_win = self.closed_positions_df[self.closed_positions_df["profit_status"] == "win"].profit_size.sum(
        )
        total_lose = self.closed_positions_df[self.closed_positions_df["profit_status"] == "lose"].profit_size.sum(
        )

        total_average_return = total_return / total_entries
        self.logger.info("total entry -> " + str(total_entries) + " times")
        self.logger.info("total winning rate -> " +
                         str(round(total_winning_rate, 2)) + "%")
        self.logger.info("total return -> $" + str(total_return))
        self.logger.info("total win -> $" + str(total_win))
        self.logger.info("total lose -> $" + str(total_lose))
        self.logger.info("total average return -> $" +
                         str(round(total_average_return, 2)))


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
            "profit_size"
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
            self.profit_size
        ], index=record_column)
        return self.position
