from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base


class OHLCV_1min(declarative_base()):
    __tablename__ = "orginal_ohlcv_1min"

    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    def __init__(self, timestamp, open, high, low, close, volume):
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def __repr__(self):
        return "<'%s'('%s','%s')>" % (OHLCV_1min.__tablename__, self.info_name, self.description)
