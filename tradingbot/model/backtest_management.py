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
    timeframe = Column(Integer)
    version = Column(String(100))
    close_position_on_do_nothing = Column(Boolean)
    inverse_trading = Column(Boolean)

    def __init__(self):
        # default params
        self.backtest_summary_id = BacktestManagement.backtest_summary_id
        self.version = BacktestManagement.version
        self.timeframe = BacktestManagement.timeframe
        self.close_position_on_do_nothing = BacktestManagement.close_position_on_do_nothing
        self.inverse_trading = BacktestManagement.inverse_trading
