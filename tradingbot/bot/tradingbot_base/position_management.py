from datetime import datetime, timedelta
from time import sleep

from .position import Position
from .position_leverage import PositionLeverage
from .position_lot import PositionLot

from .order_management import OrderManagement


class PositionManagement:
    def __init__(self, tradingbot):
        # current holding position
        self.position = None

        # prevent from pushing same order in one minutes
        self.processed_flag = False

        # option for open and close
        self.open_onetime_duration = 60
        self.close_onetime_duration = 60
        self.open_through_time = 600

        # for other helper methods
        self.tradingbot = tradingbot

        self.position_leverage = PositionLeverage(self.tradingbot, self)
        self.position_lot = PositionLot(self.tradingbot, self)

        self.order_management = OrderManagement(self)

        if not self.tradingbot.is_backtest:
            self.current_balance = self.tradingbot.exchange_client.client.fetch_balance()[
                "BTC"]["total"]

    def signal_judge(self, row):
        if self.position is None:
            return self.open_position(row) if row.signal == "buy" or row.signal == "sell" else None
        else:
            order_type = self.position.order_type
            inverse_trading = self.tradingbot.default_params["inverse_trading"]
            close_position_on_do_nothing = self.tradingbot.default_params[
                "close_position_on_do_nothing"]

            if (row.signal == "buy" and ((order_type == "long" and inverse_trading) or (order_type == "short" and not inverse_trading))) or\
               (row.signal == "sell" and ((order_type == "short" and inverse_trading) or (order_type == "long" and not inverse_trading))) or\
               (row.signal == "do_nothing" and close_position_on_do_nothing):

                self.close_position(row)
                return None

    def open_position(self, row):
        lot = self.position_lot.calculate_lot(row)
        leverage = self.position_leverage.calculate_leverage(row)

        # [FIXME] symbol is hardcoded, only for bitmex

        self.position = Position(row, self.tradingbot.is_backtest)

        self.position.current_balance = self.current_balance
        self.position.lot = lot
        self.position.leverage = leverage
        self.position.order_method = "limit"  # limit or market order
        self.position.order_type = self.get_order_type(row)

        self.execute_open_order(row)

    def get_order_type(self, row):
        inverse_trading = self.tradingbot.default_params["inverse_trading"]

        if row.signal == "buy":
            return "long" if not inverse_trading else "short"
        elif row.signal == "sell":
            return "short" if not inverse_trading else "long"

    def execute_open_order(self, row):
        if self.tradingbot.is_backtest:
            return self.position
        else:
            self.tradingbot.exchange_client.client.private_post_position_leverage(
                {"symbol": "XBTUSD", "leverage": str(self.position.leverage)})
            self.create_position(row)

    def close_position(self, row):
        if self.tradingbot.is_backtest:
            self.position.close_position(row)
            self.current_balance = self.position.current_balance
            return self.position
        else:
            self.position.order_method = "market"
            self.create_position(row)

    def clean_position(self):
        self.position = None

    def create_position(self, row):
        if self.position.order_status == "pass":
            self.try_open(row)

            if self.position.order_status == "pass":
                self.tradingbot.line.notify("all attempts are failed, skip")
                self.position.set_pass_log()
                self.tradingbot.db_client.influx_raw_connector.write_points(
                    [self.position.get_pass_log()])
                self.clean_position()

        elif self.position.order_status == "open":
            self.execute_close(row)
            self.clean_position()

    def try_open(self, row):
        attempted_time = 1
        order_start_time = datetime.now()

        while datetime.now() - order_start_time < timedelta(seconds=self.open_through_time):
            # loop until through time
            # success => return position
            # failed => increment attempted_time
            # all failed => skip
            self.position = self.attempt_position(row, self.open_onetime_duration, attempted_time,
                                                  order_start_time, through_time=self.open_through_time)

            if self.position.order_status == "open":
                break
            else:
                attempted_time += 1

    def execute_close(self, row):
        attempted_time = 1
        order_start_time = datetime.now()
        while True:
            self.position = self.attempt_position(row, self.close_onetime_duration, attempted_time,
                                                  order_start_time, through_time=None)
            if self.position.order_status == "closed":
                return
            else:
                attempted_time += 1

    def attempt_position(self, row, onetime_duration, attempted_time, order_start_time, through_time=None):
        order = self.order_management.send_order()
        sleep(onetime_duration)
        order_info = self.tradingbot.exchange_client.client.fetch_order(
            order["id"])

        if self.position.order_status == "pass":
            self.position.open_order_id = order["id"]
            return self.order_management.is_position_opened(row, order_start_time, attempted_time, order_info)
        elif self.position.order_status == "open":
            self.position.close_order_id = order["id"]
            return self.order_management.is_position_closed(row, order_start_time, attempted_time, order_info)
