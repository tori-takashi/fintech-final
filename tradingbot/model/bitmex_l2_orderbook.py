
from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class BitmexL2OrderBook(Base):
    __tablename__ = "bitmex_l2_orderbook"
    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime)
    symbol = Column(String(20))
    side = Column(String(40))
    size = Column(Float)
    price = Column(Float)

    def __init__(self):
        self.timestamp = BitmexL2OrderBook.timestamp
        self.symbol = BitmexL2OrderBook.symbol
        self.side = BitmexL2OrderBook.size
        self.price = BitmexL2OrderBook.price
