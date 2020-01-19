from datetime import datetime


class Position:
    def __init__(self, row_open, is_backtest=False):
        self.is_backtest = is_backtest
        self.common_log(row_open)

        if self.is_backtest:
            self.transaction_fee_by_order = 0.0015  # 0.15 = 0.075% * 2 market order
            # because transaction fee is charged for both open and close order.
            self.order_status = "open"
            self.order_method = "market"

            self.entry_price = row_open.close
            self.entry_time = row_open.Index

        else:
            # for real environment
            self.order_status = "pass"

            # for open
            self.entry_position_id = None
            self.entry_judged_price = row_open.close
            self.entry_judged_time = datetime.now()

            self.entry_price = None
            self.entry_price_difference = None
            self.entry_time = None

            self.entry_attempt_time = None
            self.entry_attempt_period = None

            self.entry_order_method = None  # limit or market
            self.entry_transaction_cost = None

            # for close
            self.closed_position_id = None
            self.close_judged_price = None
            self.close_judged_time = None

            self.close_price = None
            self.close_price_difference = None
            self.close_time = None

            self.close_attempt_time = None
            self.close_attempt_period = None

            self.close_order_method = None  # maker or taker
            self.close_transaction_cost = None

            self.total_transaction_cost = None

        # for transaction log

        self.open_position(row_open)

    def common_log(self, row_open):
        self.exchange_name = row_open.exchange_name
        self.asset_name = row_open.asset_name
        self.order_type = None

        self.current_balance = None
        self.lot = None
        self.leverage = None

    def open_position(self, row_open):
        # back test
        if self.is_backtest:
            self.order_status = "open"

    def close_position(self, row_close):
        # for summary backtest
        self.close_price = row_close.close
        self.close_time = row_close.Index

        self.price_difference = self.close_price - self.entry_price
        self.price_difference_percentage = (
            (self.close_price / self.entry_price) - 1)*10

        self.transaction_cost = (
            self.lot / self.close_price) * self.transaction_fee_by_order

        if self.order_type == "long":
            self.gross_profit = ((self.close_price - self.entry_price)
                                 * self.lot * self.leverage) / self.close_price
            self.profit_size = self.gross_profit - self.transaction_cost
        elif self.order_type == "short":
            self.gross_profit = ((self.entry_price - self.close_price)
                                 * self.lot * self.leverage) / self.close_price
            self.profit_size = self.gross_profit - self.transaction_cost

        self.profit_status = "win" if self.profit_size > 0 else "lose"

        if self.current_balance > 0:
            self.profit_percentage = (
                (self.profit_size / self.current_balance) + 1)*100
        elif self.current_balance == 0:
            self.profit_percentage = None
        else:
            profit_percentage = (
                abs(self.profit_size + self.current_balance) / abs(self.current_balance))
            self.profit_percentage = profit_percentage if self.profit_status == "win" else - \
                1 * profit_percentage

        self.profit_percentage = (
            ((self.current_balance + self.profit_size) / self.current_balance) - 1)*100
        self.current_balance += self.profit_size

        self.order_status = "closed"

    def get_pass_log(self):
        return self.pass_log

    def get_combined_log(self):
        combined_fields = {
            **self.open_log["fields"], **self.close_log["fields"]}
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
                "entry_attempt_time": self.entry_attempt_time,
                "entry_attempt_period": str(self.entry_attempt_period),
                "order_cancel_time": str(self.order_cancel_time)
            },
            'measurement': "real_transaction_log",
            'tags': {
                "entry_position_id": self.entry_position_id,
                "exchange_name": self.exchange_name,
                "asset_name": self.asset_name,
                "order_type": self.order_type,
                "order_status": self.order_status,
            }
        }

    def set_open_log(self, open_log):
        self.entry_time = datetime.now()
        self.order_status = "open"

        self.entry_attempt_time = open_log["entry_attempt_time"]
        self.entry_attempt_period = self.entry_time - self.entry_judged_time

        self.entry_order_method = open_log["order_method"]
        if self.entry_order_method == "limit":
            self.open_transaction_fee = -0.0025  # both open and close are limit order
        elif self.entry_order_method == "market":
            self.open_transaction_fee = 0.0005

        self.entry_transaction_cost = self.open_transaction_fee * self.lot

        self.open_log = {
            'fields': {
                "lot": self.lot,
                "leverage": self.leverage,
                "entry_judged_price": float(self.entry_judged_price),
                "entry_judged_time": str(self.entry_judged_time),
                "entry_time": str(self.entry_time),
                "entry_attempt_time": self.entry_attempt_time,
                "entry_attempt_period": str(self.entry_attempt_period),
                "entry_transaction_cost": float(self.entry_transaction_cost)
            },
            'tags': {
                "entry_position_id": self.entry_position_id,
                "exchange_name": self.exchange_name,
                "asset_name": self.asset_name,
                "order_type": self.order_type,
                "order_status": self.order_status,
                "entry_order_method": self.entry_order_method,  # limit or market
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

        # limit or market
        self.close_order_method = close_log["close_order_method"]
        if self.close_order_method == "limit":
            self.close_transaction_fee = -0.0025  # both open and close are limit order
        elif self.close_order_method == "market":
            self.close_transaction_fee = 0.0005

        self.close_transaction_cost = self.close_transaction_fee * self.lot

        self.total_transaction_cost = self.entry_transaction_cost + \
            self.close_transaction_cost  # unit is BTC
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
                "close_judged_time": str(self.close_judged_time),
                "close_price": float(self.close_price),
                "close_price_difference": float(self.close_price_difference),
                "close_time": str(self.close_time),
                "close_attempt_time": self.close_attempt_time,
                "close_attempt_period": str(self.close_attempt_period),
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

    def generate_transaction_log_for_backtest(self, summary_id):
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
            "profit_percentage": float(self.profit_percentage)
        }
        return log_dict
