from sqlalchemy import Column, Integer, Float, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base


class BacktestParams(declarative_base()):
    # [Need to be edited]
    # append class and instance variable from outside for specific params
    __tablename__ = "backtest_params"

    # [No need to edit below]
    id = Column(Integer, primary_key=True)

    # default params
    bot_name = Column(String)
    timeframe = Column(Integer)
    close_in_do_nothing = Column(Boolean)
    inverse_trading = Column(Boolean)

    def __init__(self):
        # default params
        self.bot_name = BacktestParams.bot_name
        self.timeframe = BacktestParams.timeframe
        self.close_in_do_nothing = BacktestParams.close_in_do_nothing
        self.inverse_trading = BacktestParams.inverse_trading

    def __repr__(self):
        return "<'%s'('%s','%s')>" % (BacktestParams.__tablename__, self.info_name, self.description)
