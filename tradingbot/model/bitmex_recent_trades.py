
from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class BitmexRecentOrders(Base):
    __tablename__ = "bitmex_recent_trades"
    id = Column(Integer, primary_key=True)

    timestamp = Column(String(100))
    symbol = Column(String(20))
    side = Column(String(40))
    size = Column(Float)
    price = Column(Float)
    tickDirection = Column(String(30))
    trdMatchID = Column(String(50))
    grossValue = Column(Float)
    homeNotional = Column(String(20))
    foreignNotional = Column(String(20))

    def __init__(self):
        self.timestamp = BitmexRecentOrders.timestamp
        self.symbol = BitmexRecentOrders.symbol
        self.side = BitmexRecentOrders.side
        self.size = BitmexRecentOrders.size
        self.price = BitmexRecentOrders.price
        self.tickDirection = BitmexRecentOrders.tickDirection
        self.trdMatchID = BitmexRecentOrders.trdMatchID
        self.grossValue = BitmexRecentOrders.grossValue
        self.homeNotional = BitmexRecentOrders.homeNotional
        self.foreignNotional = BitmexRecentOrders.foreignNotional
