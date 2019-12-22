from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, Interval
from sqlalchemy.orm import relationship
from .base import Base


class BacktestTransactionLog(Base):
    # [Need to be edited]
    __tablename__ = "backtest_transaction_log"
    backtest_summary = relationship("BacktestSummary")
    #backtest_summary_id = Column(Integer, ForeignKey("backtest_summary.id"))

    # [No need to edit below]
    id = Column(Integer, primary_key=True)

    exchange_name = Column(String)
    asset_name = Column(String)

    initial_balance = Column(Float)
    current_balance = Column(Float)

    backtest_start_time = Column(DateTime)
    backtest_end_time = Column(DateTime)

    entry_time = Column(DateTime)
    holding_time = Column(Interval)
    close_time = Column(DateTime)

    order_status = Column(String)
    # open or close

    order_type = Column(String)
    # long or short

    profit_status = Column(String)
    # win or lose

    entry_price = Column(Float)
    price_difference = Column(Float)
    price_difference_percentage = Column(Float)
    close_price = Column(Float)

    leverage = Column(Float)
    lot = Column(Float)

    transaction_cost = Column(Float)
    profit_size = Column(Float)
    profit_percentage = Column(Float)

    def __init__(self):
        self.exchange_name = BacktestTransactionLog.exchange_name
        self.asset_name = BacktestTransactionLog.asset_name

        self.initial_balance = BacktestTransactionLog.initial_balance
        self.profit_percentage = BacktestTransactionLog.profit_percentage
        self.current_balance = BacktestTransactionLog.current_balance

        self.backtest_start_time = BacktestTransactionLog.backtest_start_time
        self.backtest_end_time = BacktestTransactionLog.backtest_end_time

        self.entry_time = BacktestTransactionLog.entry_time
        self.holding_time = BacktestTransactionLog.holding_time
        self.close_time = BacktestTransactionLog.close_time

        self.order_status = BacktestTransactionLog.order_status

        self.order_type = BacktestTransactionLog.order_type

        self.profit_status = BacktestTransactionLog.profit_status

        self.entry_price = BacktestTransactionLog.entry_price
        self.price_difference = BacktestTransactionLog.price_difference
        self.price_difference_percentage = BacktestTransactionLog.price_difference_percentage
        self.close_price = BacktestTransactionLog.close_price

        self.leverage = BacktestTransactionLog.leverage
        self.lot = BacktestTransactionLog.lot

        self.transaction_cost = BacktestTransactionLog.transaction_cost
        self.profit_size = BacktestTransactionLog.profit_size

    def __repr__(self):
        return "<'%s'('%s','%s')>" % (BacktestTransactionLog.__tablename__, self.info_name, self.description)
