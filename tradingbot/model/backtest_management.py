from sqlalchemy import Column, Integer, Float, ForeignKey, Boolean, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from .base import Base


class BacktestManagement(Base):
    # [Need to be edited]
    # append class and instance variable from outside for specific params
    __tablename__ = "backtest_management"

    # [No need to edit below]
    id = Column(Integer, primary_key=True)

    backtest_summary_id = Column(Integer, ForeignKey("backtest_summary.id"))
    backtest_summary = relationship(
        "BacktestSummary", foreign_keys=[backtest_summary_id],
        primaryjoin="BacktestManagement.backtest_summary_id == BacktestSummary.id", uselist=False, viewonly=True)

    # default params
    bot_name = Column(String(100))
    timeframe = Column(Integer)
    version = Column(String(100))
    close_position_on_do_nothing = Column(Boolean)
    inverse_trading = Column(Boolean)
    random_leverage = Column(Boolean)
    random_forest_leverage_adjust = Column(Boolean)

    def __init__(self):
        # default params
        self.bot_name = BacktestManagement.bot_name
        self.backtest_summary_id = BacktestManagement.backtest_summary_id
        self.version = BacktestManagement.version
        self.timeframe = BacktestManagement.timeframe
        self.close_position_on_do_nothing = BacktestManagement.close_position_on_do_nothing
        self.inverse_trading = BacktestManagement.inverse_trading
        self.random_leverage = BacktestManagement.random_leverage
        self.random_forest_leverage_adjust = BacktestManagement.random_forest_leverage_adjust
