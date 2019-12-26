from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base


class OHLCV_1min(declarative_base()):
    __tablename__ = "orginal_ohlcv_1min"

    id = Column(Integer, primary_key=True)

    exchange_name = Column(String(100))
    asset_name = Column(String(200))

    timestamp = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    def __init__(self):
        self.timestamp = OHLCV_1min.timestamp
        self.open = OHLCV_1min.open
        self.high = OHLCV_1min.high
        self.low = OHLCV_1min.low
        self.close = OHLCV_1min.close
        self.volume = OHLCV_1min.volume

    def __repr__(self):
        return "<'%s'('%s','%s')>" % (OHLCV_1min.__tablename__, self.info_name, self.description)
