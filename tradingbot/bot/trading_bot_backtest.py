from model.backtest_transaction_log import BacktestTransactionLog

from . position_management import PositionManagement
from .trading_bot_backtest_db import TradingBotBacktestDB
from .ohlcv_tradingbot import OHLCV_tradingbot

class TradingBotBacktest():
    def __init__(self, tradingbot):
        self.tradingbot = tradingbot

        self.ohlcv_tradingbot = OHLCV_tradingbot(tradingbot.dataset_manipulator, tradingbot.default_params, tradingbot.specific_params)
        self.trading_bot_backtest_db = TradingBotBacktestDB(self, tradingbot.is_backtest)
        self.position_management = PositionManagement(tradingbot)

    def run(self, ohlcv_df, ohlcv_start_time, ohlcv_end_time, floor_time):
        # for summary
        if floor_time:
            self.ohlcv_tradingbot.ohlcv_start_time = self.tradingbot.dataset_manipulator.floor_datetime_to_ohlcv(ohlcv_start_time, "up")
            self.ohlcv_tradingbot.ohlcv_end_time = self.tradingbot.dataset_manipulator.floor_datetime_to_ohlcv(ohlcv_end_time, "down")
            
        ohlcv_df = self.ohlcv_tradingbot.get_ohlcv() if ohlcv_df is None else ohlcv_df
        ohlcv_with_metrics = self.tradingbot.calculate_metrics(ohlcv_df)
        self.ohlcv_with_signals = self.tradingbot.calculate_signals(ohlcv_with_metrics).dropna()

        self.write_to_backtest_database()

    def write_to_backtest_database(self):
        self.summary_id = self.trading_bot_backtest_db.init_summary()

        self.insert_backtest_transaction_logs()

        self.trading_bot_backtest_db.insert_params_management(self.summary_id)
        self.trading_bot_backtest_db.update_summary(self.transaction_logs, self.summary_id)
        
        self.position_management.clean_position()

    def insert_backtest_transaction_logs(self):
        signal_judge = self.position_management.signal_judge
        position = self.position_management.position
        # refer to signal then judge investment
        # keep one order at most
        self.transaction_logs = []
        
        for row in self.ohlcv_with_signals.itertuples(): # self.ohlcv_with_signals should be dataframe
            # get position = position with open or None
            signal_judge(row)
            # append close position
            if position is not None and position.order_status == "closed":
                position.generate_transaction_log_for_backtest(self.summary_id)
                self.transaction_logs.append(position)
                self.position_management.clean_position()

        self.tradingbot.db_client.session.bulk_insert_mappings(BacktestTransactionLog, self.transaction_logs)

    def set_params(self, default_params, specific_params):
        # for loop and serach optimal metrics value
        self.default_params = default_params
        self.specific_params = specific_params
        self.combined_params = dict(**self.default_params, **self.specific_params)

    def bulk_inser(self):
        self.trading_bot_backtest_db.bulk_insert()
