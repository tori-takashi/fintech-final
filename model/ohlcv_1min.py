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
    Volume = Column(Float)
