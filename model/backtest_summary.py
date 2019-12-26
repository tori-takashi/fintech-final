from sqlalchemy import Column, Integer, Float, DateTime, String, Interval
from sqlalchemy.orm import relationship
from .base import Base


class BacktestSummary(Base):
    # [FIXME]
    # Add geometric mean

    __tablename__ = "backtest_summary"

    id = Column(Integer, primary_key=True)
    backtest_transaction_log = relationship(
        "BacktestTransactionLog", backref="backtest_summary")
    backtest_management = relationship(
        "BacktestManagement", back_populates="backtest_summary")

    backtest_start_time = Column(DateTime)
    backtest_end_time = Column(DateTime)

    # params
    bot_name = Column(String(300))
    initial_balance = Column(Float)
    account_currency = Column(String(200))

    # trade metrics
    total_entry = Column(Integer)

    total_max_holding_ms = Column(Interval)
    total_average_holding_ms = Column(Interval)
    total_min_holding_ms = Column(Interval)

    total_return = Column(Float)
    total_return_average = Column(Float)
    total_standard_deviation = Column(Float)
    total_skewness = Column(Float)
    total_kurtosis = Column(Float)
    total_median = Column(Float)

    total_return_percentage = Column(Float)
    total_return_average_percentage = Column(Float)
    total_standard_deviation_percentage = Column(Float)
    total_skewness_percentage = Column(Float)
    total_kurtosis_percentage = Column(Float)
    total_median = Column(Float)

    total_transaction_cost = Column(Float)

    # win
    win_entry = Column(Integer)
    win_rate = Column(Float)
    win_average_holding_ms = Column(Interval)

    win_return = Column(Float)
    win_return_average = Column(Float)
    win_standard_deviation = Column(Float)
    win_skewness = Column(Float)
    win_kurtosis = Column(Float)
    win_median = Column(Float)

    win_return_percentage = Column(Float)
    win_return_average_percentage = Column(Float)
    win_standard_deviation_percentage = Column(Float)
    win_skewness_percentage = Column(Float)
    win_kurtosis_percentage = Column(Float)
    win_median_percentage = Column(Float)

    win_max_profit = Column(Float)
    win_max_profit_percentage = Column(Float)

    win_consecutive_max_entry = Column(Integer)
    win_consecutive_average_entry = Column(Float)
    win_consecutive_max_profit = Column(Float)

    # lose
    lose_entry = Column(Integer)
    lose_rate = Column(Float)
    lose_average_holding_ms = Column(Interval)

    lose_return = Column(Float)
    lose_return_average = Column(Float)
    lose_standard_deviation = Column(Float)
    lose_skewness = Column(Float)
    lose_kurtosis = Column(Float)
    lose_median = Column(Float)

    lose_return_percentage = Column(Float)
    lose_return_average_percentage = Column(Float)
    lose_standard_deviation_percentage = Column(Float)
    lose_skewness_percentage = Column(Float)
    lose_kurtosis_percentage = Column(Float)
    lose_median_percentage = Column(Float)

    lose_max_loss = Column(Float)
    lose_max_loss_percentage = Column(Float)

    lose_consecutive_max_entry = Column(Integer)
    lose_consecutive_average_entry = Column(Float)
    lose_consecutive_max_loss = Column(Float)

    # long
    long_entry = Column(Integer)
    long_rate = Column(Float)
    long_average_holding_ms = Column(Interval)

    long_return = Column(Float)
    long_return_average = Column(Float)
    long_standard_deviation = Column(Float)
    long_skewness = Column(Float)
    long_kurtosis = Column(Float)

    long_return_percentage = Column(Float)
    long_return_average_percentage = Column(Float)
    long_standard_deviation_percentage = Column(Float)
    long_skewness_percentage = Column(Float)
    long_kurtosis_percentage = Column(Float)

    long_max_profit = Column(Float)
    long_max_profit_percentage = Column(Float)

    long_max_loss = Column(Float)
    long_max_loss_percentage = Column(Float)

    # short
    short_entry = Column(Integer)
    short_rate = Column(Float)
    short_average_holding_ms = Column(Interval)

    short_return = Column(Float)
    short_return_average = Column(Float)
    short_standard_deviation = Column(Float)
    short_skewness = Column(Float)
    short_kurtosis = Column(Float)

    short_return_percentage = Column(Float)
    short_return_average_percentage = Column(Float)
    short_standard_deviation_percentage = Column(Float)
    short_skewness_percentage = Column(Float)
    short_kurtosis_percentage = Column(Float)

    short_max_profit = Column(Float)
    short_max_profit_percentage = Column(Float)

    short_max_loss = Column(Float)
    short_max_loss_percentage = Column(Float)

    # win long
    win_long_entry = Column(Integer)
    win_long_average_holding_ms = Column(Interval)

    win_long_return = Column(Float)
    win_long_return_average = Column(Float)
    win_long_standard_deviation = Column(Float)
    win_long_skewness = Column(Float)
    win_long_kurtosis = Column(Float)
    win_long_median = Column(Float)

    win_long_return_percentage = Column(Float)
    win_long_return_average_percentage = Column(Float)
    win_long_standard_deviation_percentage = Column(Float)
    win_long_skewness_percentage = Column(Float)
    win_long_kurtosis_percentage = Column(Float)
    win_long_median_percentage = Column(Float)

    # win short
    win_short_entry = Column(Integer)
    win_short_average_holding_ms = Column(Interval)

    win_short_return = Column(Float)
    win_short_return_average = Column(Float)
    win_short_standard_deviation = Column(Float)
    win_short_skewness = Column(Float)
    win_short_kurtosis = Column(Float)
    win_short_median = Column(Float)

    win_short_return_percentage = Column(Float)
    win_short_return_average_percentage = Column(Float)
    win_short_standard_deviation_percentage = Column(Float)
    win_short_skewness_percentage = Column(Float)
    win_short_kurtosis_percentage = Column(Float)
    win_short_median_percentage = Column(Float)

    # lose long
    lose_long_entry = Column(Integer)
    lose_long_average_holding_ms = Column(Interval)

    lose_long_return = Column(Float)
    lose_long_return_average = Column(Float)
    lose_long_standard_deviation = Column(Float)
    lose_long_skewness = Column(Float)
    lose_long_kurtosis = Column(Float)
    lose_long_median = Column(Float)

    lose_long_return_percentage = Column(Float)
    lose_long_return_average_percentage = Column(Float)
    lose_long_standard_deviation_percentage = Column(Float)
    lose_long_skewness_percentage = Column(Float)
    lose_long_kurtosis_percentage = Column(Float)
    lose_long_median_percentage = Column(Float)

    # lose short
    lose_short_entry = Column(Integer)
    lose_short_average_holding_ms = Column(Interval)

    lose_short_return = Column(Float)
    lose_short_return_average = Column(Float)
    lose_short_standard_deviation = Column(Float)
    lose_short_skewness = Column(Float)
    lose_short_kurtosis = Column(Float)
    lose_short_median = Column(Float)

    lose_short_return_percentage = Column(Float)
    lose_short_return_average_percentage = Column(Float)
    lose_short_standard_deviation_percentage = Column(Float)
    lose_short_skewness_percentage = Column(Float)
    lose_short_kurtosis_percentage = Column(Float)
    lose_short_median_percentage = Column(Float)

    # important metrics
    profit_factor = Column(Float)
    recovery_factor = Column(Float)

    # https://www.metatrader5.com/ja/terminal/help/trading_advanced/history_report#drawdown
    absolute_drawdown = Column(Float)
    maximal_drawdown = Column(Float)
    relative_drawdown = Column(Float)

    def __init__(self):
        # other metrics
        self.backtest_start_time = BacktestSummary.backtest_start_time
        self.backtest_end_time = BacktestSummary.backtest_end_time

        # initial status and tag
        self.bot_name = BacktestSummary.bot_name
        self.initial_balance = BacktestSummary.initial_balance
        self.account_currency = BacktestSummary.account_currency
        # important metrics
        self.profit_factor = BacktestSummary.profit_factor
        self.recovery_factor = BacktestSummary.recovery_factor
        # https://www.metatrader5.com/ja/terminal/help/trading_advanced/history_report#drawdown
        self.absolute_drawdown = BacktestSummary.absolute_drawdown
        self.maximal_drawdown = BacktestSummary.maximal_drawdown
        self.relative_drawdown = BacktestSummary.relative_drawdown

        # trade metrics

        self.total_entry = BacktestSummary.total_entry

        self.total_max_holding_ms = BacktestSummary.total_max_holding_ms
        self.total_average_holding_ms = BacktestSummary.total_average_holding_ms
        self.total_min_holding_ms = BacktestSummary.total_min_holding_ms

        self.total_return = BacktestSummary.total_return
        self.total_return_average = BacktestSummary.total_return_average
        self.total_standard_deviation = BacktestSummary.total_standard_deviation
        self.total_skewness = BacktestSummary.total_skewness
        self.total_kurtosis = BacktestSummary.total_kurtosis

        self.total_return_percentage = BacktestSummary.total_return_percentage
        self.total_return_average_percentage = BacktestSummary.total_return_average_percentage
        self.total_standard_deviation_percentage = BacktestSummary.total_standard_deviation_percentage
        self.total_skewness_percentage = BacktestSummary.total_skewness_percentage
        self.total_kurtosis_percentage = BacktestSummary.total_kurtosis_percentage

        self.total_transaction_cost = BacktestSummary.total_transaction_cost

        # win
        self.win_entry = BacktestSummary.win_entry
        self.win_average_holding_ms = BacktestSummary.win_average_holding_ms

        self.win_return = BacktestSummary.win_return
        self.win_return_average = BacktestSummary.win_return_average
        self.win_standard_deviation = BacktestSummary.win_standard_deviation
        self.win_skewness = BacktestSummary.win_skewness
        self.win_kurtosis = BacktestSummary.win_kurtosis

        self.win_return_percentage = BacktestSummary.win_return_percentage
        self.win_return_average_percentage = BacktestSummary.win_return_average_percentage
        self.win_standard_deviation_percentage = BacktestSummary.win_standard_deviation_percentage
        self.win_skewness_percentage = BacktestSummary.win_skewness_percentage
        self.win_kurtosis_percentage = BacktestSummary.win_kurtosis_percentage

        self.win_max_profit = BacktestSummary.win_max_profit

        self.win_consecutive_max_entry = BacktestSummary.win_consecutive_max_entry
        self.win_consecutive_average_entry = BacktestSummary.win_consecutive_average_entry
        self.win_consecutive_max_profit = BacktestSummary.win_consecutive_max_profit

        # lose
        self.lose_entry = BacktestSummary.lose_entry
        self.lose_average_holding_ms = BacktestSummary.lose_average_holding_ms

        self.lose_return = BacktestSummary.lose_return
        self.lose_return_average = BacktestSummary.lose_return_average
        self.lose_standard_deviation = BacktestSummary.lose_standard_deviation
        self.lose_skewness = BacktestSummary.lose_skewness
        self.lose_kurtosis = BacktestSummary.lose_kurtosis

        self.lose_return_percentage = BacktestSummary.lose_return_percentage
        self.lose_return_average_percentage = BacktestSummary.lose_return_average_percentage
        self.lose_standard_deviation_percentage = BacktestSummary.lose_standard_deviation_percentage
        self.lose_skewness_percentage = BacktestSummary.lose_skewness_percentage
        self.lose_kurtosis_percentage = BacktestSummary.lose_kurtosis_percentage

        self.lose_max_loss = BacktestSummary.lose_max_loss

        self.lose_consecutive_max_entry = BacktestSummary.lose_consecutive_max_entry
        self.lose_consecutive_average_entry = BacktestSummary.lose_consecutive_average_entry
        self.lose_consecutive_max_loss = BacktestSummary.lose_consecutive_max_loss

        # long
        self.long_entry = BacktestSummary.long_entry
        self.long_average_holding_ms = BacktestSummary.long_average_holding_ms

        self.long_return = BacktestSummary.long_return
        self.long_return_average = BacktestSummary.long_return_average
        self.long_standard_deviation = BacktestSummary.long_standard_deviation
        self.long_skewness = BacktestSummary.long_skewness
        self.long_kurtosis = BacktestSummary.long_kurtosis

        self.long_return_percentage = BacktestSummary.long_return_percentage
        self.long_return_average_percentage = BacktestSummary.long_return_average_percentage
        self.long_standard_deviation_percentage = BacktestSummary.long_standard_deviation_percentage
        self.long_skewness_percentage = BacktestSummary.long_skewness_percentage
        self.long_kurtosis_percentage = BacktestSummary.long_kurtosis_percentage

        self.long_max_profit = BacktestSummary.long_max_profit
        self.long_max_profit_percentage = BacktestSummary.long_max_profit_percentage

        self.long_max_loss = BacktestSummary.long_max_loss
        self.long_max_loss_percentage = BacktestSummary.long_max_loss_percentage

        # short
        self.short_entry = BacktestSummary.short_entry
        self.short_average_holding_ms = BacktestSummary.short_average_holding_ms

        self.short_return = BacktestSummary.short_return
        self.short_return_average = BacktestSummary.short_return_average
        self.short_standard_deviation = BacktestSummary.short_standard_deviation
        self.short_skewness = BacktestSummary.short_skewness
        self.short_kurtosis = BacktestSummary.short_kurtosis

        self.short_return_percentage = BacktestSummary.short_return_percentage
        self.short_return_average_percentage = BacktestSummary.short_return_average_percentage
        self.short_standard_deviation_percentage = BacktestSummary.short_standard_deviation_percentage
        self.short_skewness_percentage = BacktestSummary.short_skewness_percentage
        self.short_kurtosis_percentage = BacktestSummary.short_kurtosis_percentage

        self.short_max_profit = BacktestSummary.short_max_profit
        self.short_max_profit_percentage = BacktestSummary.short_max_profit_percentage

        self.short_max_loss = BacktestSummary.short_max_loss
        self.short_max_loss_percentage = BacktestSummary.short_max_loss_percentage

        # win long
        self.win_long_entry = BacktestSummary.win_long_entry
        self.win_long_average_holding_ms = BacktestSummary.win_long_average_holding_ms

        self.win_long_return = BacktestSummary.win_long_return
        self.win_long_return_average = BacktestSummary.win_long_return_average
        self.win_long_standard_deviation = BacktestSummary.win_long_standard_deviation
        self.win_long_skewness = BacktestSummary.win_long_skewness
        self.win_long_kurtosis = BacktestSummary.win_long_kurtosis
        self.win_long_median = BacktestSummary.win_long_median

        self.win_long_return_percentage = BacktestSummary.win_long_return_percentage
        self.win_long_return_average_percentage = BacktestSummary.win_long_return_average_percentage
        self.win_long_standard_deviation_percentage = BacktestSummary.win_long_standard_deviation_percentage
        self.win_long_skewness_percentage = BacktestSummary.win_long_skewness_percentage
        self.win_long_kurtosis_percentage = BacktestSummary.win_long_kurtosis_percentage
        self.win_long_median_percentage = BacktestSummary.win_long_median_percentage

        # win short
        self.win_short_entry = BacktestSummary.win_short_entry
        self.win_short_average_holding_ms = BacktestSummary.win_short_average_holding_ms

        self.win_short_return = BacktestSummary.win_short_return
        self.win_short_return_average = BacktestSummary.win_short_return_average
        self.win_short_standard_deviation = BacktestSummary.win_short_standard_deviation
        self.win_short_skewness = BacktestSummary.win_short_skewness
        self.win_short_kurtosis = BacktestSummary.win_short_kurtosis
        self.win_short_median = BacktestSummary.win_short_median

        self.win_short_return_percentage = BacktestSummary.win_short_return_percentage
        self.win_short_return_average_percentage = BacktestSummary.win_short_return_average_percentage
        self.win_short_standard_deviation_percentage = BacktestSummary.win_short_standard_deviation_percentage
        self.win_short_skewness_percentage = BacktestSummary.win_short_skewness_percentage
        self.win_short_kurtosis_percentage = BacktestSummary.win_short_kurtosis_percentage
        self.win_short_median_percentage = BacktestSummary.win_short_median_percentage

        # lose long
        self.lose_long_entry = BacktestSummary.lose_long_entry
        self.lose_long_average_holding_ms = BacktestSummary.lose_long_average_holding_ms

        self.lose_long_return = BacktestSummary.lose_long_return
        self.lose_long_return_average = BacktestSummary.lose_long_return_average
        self.lose_long_standard_deviation = BacktestSummary.lose_long_standard_deviation
        self.lose_long_skewness = BacktestSummary.lose_long_skewness
        self.lose_long_kurtosis = BacktestSummary.lose_long_kurtosis
        self.lose_long_median = BacktestSummary.lose_long_median

        self.lose_long_return_percentage = BacktestSummary.lose_long_return_percentage
        self.lose_long_return_average_percentage = BacktestSummary.lose_long_return_average_percentage
        self.lose_long_standard_deviation_percentage = BacktestSummary.lose_long_standard_deviation_percentage
        self.lose_long_skewness_percentage = BacktestSummary.lose_long_skewness_percentage
        self.lose_long_kurtosis_percentage = BacktestSummary.lose_long_kurtosis_percentage
        self.lose_long_median_percentage = BacktestSummary.lose_long_median_percentage

        # lose short
        self.lose_short_entry = BacktestSummary.lose_short_entry
        self.lose_short_average_holding_ms = BacktestSummary.lose_short_average_holding_ms

        self.lose_short_return = BacktestSummary.lose_short_return
        self.lose_short_return_average = BacktestSummary.lose_short_return_average
        self.lose_short_standard_deviation = BacktestSummary.lose_short_standard_deviation
        self.lose_short_skewness = BacktestSummary.lose_short_skewness
        self.lose_short_kurtosis = BacktestSummary.lose_short_kurtosis
        self.lose_short_median = BacktestSummary.lose_short_median

        self.lose_short_return_percentage = BacktestSummary.lose_short_return_percentage
        self.lose_short_return_average_percentage = BacktestSummary.lose_short_return_average_percentage
        self.lose_short_standard_deviation_percentage = BacktestSummary.lose_short_standard_deviation_percentage
        self.lose_short_skewness_percentage = BacktestSummary.lose_short_skewness_percentage
        self.lose_short_kurtosis_percentage = BacktestSummary.lose_short_kurtosis_percentage
        self.lose_short_median_percentage = BacktestSummary.lose_short_median_percentage
