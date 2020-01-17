from datetime import datetime
from time import sleep
from ccxt import ExchangeNotAvailable, RequestTimeout, InvalidOrder, OrderNotFound, DDoSProtection

from .position_management import PositionManagement


class TradingBotReal():
    def __init__(self, tradingbot):
        self.tradingbot = tradingbot
        self.position_management = PositionManagement(self.tradingbot)
        self.processed_flag = False

    def run(self):
        while True:
            try:
                self.trade_loop_for_real()
            except ExchangeNotAvailable:
                self.tradingbot.line.notify(
                    "Exchange Not Available Error, Retry after 15 seconds")
                sleep(15)
                self.tradingbot.line.notify("loop restart...")
            except RequestTimeout:
                self.tradingbot.line.notify(
                    "Request Time out, Retry after 15 seconds")
                sleep(15)
                self.tradingbot.line.notify("loop restart...")
            except InvalidOrder:
                self.tradingbot.line.notify(
                    "Invalid Order, Retry after 15 seconds")
                sleep(15)
                self.tradingbot.line.notify("loop restart...")
            except OrderNotFound:
                self.tradingbot.line.notify(
                    "Order Not Found, Reset Position and Retry")
                self.position_management.position = None
                self.tradingbot.line.notify("loop restart...")
            except DDoSProtection:
                self.tradingbot.line.notify(
                    "DDoS protection triggered, stop process")
                raise

    def trade_loop_for_real(self):
        self.tradingbot.line.notify("trade loop start")

        while True:
            self.current_minutes = datetime.now().minute
            self.execute_with_timeframe()

            latest_row = self.tradingbot.ohlcv_tradingbot.generate_latest_row(
                self.tradingbot.calculate_metrics, self.tradingbot.calculate_signals, round=True)

            self.tradingbot.line.notify(latest_row)
            self.position_management.signal_judge(latest_row)

    def execute_with_timeframe(self, interval=0.5):
        while True:
            # [FIXME] corner case, if the timeframe couldn't divide by 60, it's wrong behavior
            if (datetime.now().minute != self.current_minutes) and (datetime.now().minute % self.tradingbot.default_params["timeframe"] == 1):
                break
            sleep(interval)
