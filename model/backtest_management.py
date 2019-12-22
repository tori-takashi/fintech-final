from sqlalchemy import Column, Integer, Float, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base


class BacktestManagement(declarative_base()):
    # [Need to be edited]
    # append class and instance variable from outside for specific params
    __tablename__ = "backtest_management"

    # [No need to edit below]
    id = Column(Integer, primary_key=True)

    backtest_summary_id = Column(Integer, ForeignKey("backtest_summary.id"))
    backtest_summary = relationship(
        "BacktestSummary", backref=backref("backtest_summary.id", uselist=False))

    # default params
    timeframe = Column(Integer)
    close_position_on_do_nothing = Column(Boolean)
    inverse_trading = Column(Boolean)

    def __init__(self):
        # default params
        self.timeframe = BacktestManagement.timeframe
        self.close_position_on_do_nothing = BacktestManagement.close_position_on_do_nothing
        self.inverse_trading = BacktestManagement.inverse_trading

    def __repr__(self):
        return "<'%s'('%s','%s')>" % (BacktestManagement.__tablename__, self.info_name, self.description)
