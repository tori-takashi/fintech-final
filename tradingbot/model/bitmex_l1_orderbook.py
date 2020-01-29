
from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class BitmexL1OrderBook(Base):

    __tablename__ = "bitmex_l1_orderbook"

    id = Column(Integer, primary_key=True)

    timestamp = Column(String(100))
    last = Column(Float)
    buy = Column(Float)
    sell = Column(Float)
    mid = Column(Float)

    def __init__(self):
        self.timestamp = BitmexL1OrderBook.timestamp
        self.last = BitmexL1OrderBook.last
        self.buy = BitmexL1OrderBook.buy
        self.sell = BitmexL1OrderBook.sell
        self.mid = BitmexL1OrderBook.mid
