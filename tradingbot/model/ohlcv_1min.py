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

    # technical indicators
    # do not add indicators that need to designate any paramater
    ad = Column(Float)
    atr = Column(Float)
    obv = Column(Float)
    roc = Column(Float)
    rsi = Column(Float)
    psar = Column(Float)
    psar_trend = Column(String(10))
    slowk = Column(Float)
    slowd = Column(Float)
    williams_r = Column(Float)

    def __init__(self):
        self.timestamp = OHLCV_1min.timestamp
        self.open = OHLCV_1min.open
        self.high = OHLCV_1min.high
        self.low = OHLCV_1min.low
        self.close = OHLCV_1min.close
        self.volume = OHLCV_1min.volume

        # technical indicators
        self.ad = OHLCV_1min.ad
        self.atr = OHLCV_1min.atr
        self.obv = OHLCV_1min.obv
        self.roc = OHLCV_1min.roc
        self.rsi = OHLCV_1min.rsi
        self.psar = OHLCV_1min.psar
        self.psar_trend = OHLCV_1min.psar_trend
        self.slowk = OHLCV_1min.slowk
        self.slowd = OHLCV_1min.slowd
        self.williams_r = OHLCV_1min.williams_r
