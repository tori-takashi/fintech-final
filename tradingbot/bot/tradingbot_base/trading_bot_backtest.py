from model.backtest_transaction_log import BacktestTransactionLog

from . position_management import PositionManagement
from .trading_bot_backtest_db import TradingBotBacktestDB
from .ohlcv_tradingbot import OHLCV_tradingbot


class TradingBotBacktest():
    def __init__(self, tradingbot):
        self.tradingbot = tradingbot

        self.initial_balance = 0.085
        self.account_currency = "BTC"

        self.ohlcv_tradingbot = OHLCV_tradingbot(
            tradingbot.dataset_manipulator, tradingbot.default_params, tradingbot.specific_params)
        self.trading_bot_backtest_db = TradingBotBacktestDB(
            self.tradingbot, self, tradingbot.is_backtest)

        self.position_management = PositionManagement(tradingbot)
        self.position_management.current_balance = self.initial_balance

    def run(self, ohlcv_df, ohlcv_start_time, ohlcv_end_time, floor_time):
        # for summary
        self.ohlcv_tradingbot.ohlcv_start_time = ohlcv_start_time
        self.ohlcv_tradingbot.ohlcv_end_time = ohlcv_end_time

        ohlcv_df = self.ohlcv_tradingbot.get_ohlcv(
            round=floor_time) if ohlcv_df is None else ohlcv_df
        ohlcv_with_metrics = self.tradingbot.calculate_metrics(ohlcv_df)
        self.ohlcv_with_signals = self.tradingbot.calculate_signals(
            ohlcv_with_metrics).dropna()

        self.write_to_backtest_database()

    def write_to_backtest_database(self):
        self.summary_id = self.trading_bot_backtest_db.init_summary()

        self.insert_backtest_transaction_logs()

        self.trading_bot_backtest_db.insert_params_management(self.summary_id)
        self.trading_bot_backtest_db.update_summary(
            self.transaction_logs, self.summary_id)

        self.position_management.clean_position()

    def insert_backtest_transaction_logs(self):
        signal_judge = self.position_management.signal_judge
        # refer to signal then judge investment
        # keep one order at most
        self.transaction_logs = []
        self.position_management.current_balance = self.initial_balance

        for row in self.ohlcv_with_signals.itertuples():  # self.ohlcv_with_signals should be dataframe
            # get position = position with open or None
            signal_judge(row)
            # append close position
            if self.position_management.position is not None and self.position_management.position.order_status == "closed":
                self.transaction_logs.append(
                    self.position_management.position.generate_transaction_log_for_backtest(self.summary_id))
                self.position_management.clean_position()

        self.tradingbot.db_client.session.bulk_insert_mappings(
            BacktestTransactionLog, self.transaction_logs)

    def set_params(self, default_params, specific_params):
        # for loop and serach optimal metrics value
        self.default_params = default_params
        self.specific_params = specific_params
        self.combined_params = dict(
            **self.default_params, **self.specific_params)

    def bulk_insert(self):
        self.trading_bot_backtest_db.bulk_insert()
