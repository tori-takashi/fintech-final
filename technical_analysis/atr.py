import pandas as pd
import talib as ta

data = pd.read_csv("ohlcv_with_future.csv")

high = data["high"]
low = data["low"]
close = data["close"]
data["timestamp"] = pd.to_datetime(data["timestamp"])

ta_ATR = ta.ATR(high, low, close)
output = pd.DataFrame(
    data={
        "high": high,
        "low": low,
        "close": close,
        "timestamp": data["timestamp"],
        "ta_ATR": ta_ATR}
)
output.reset_index(inplace=True, drop=True)
output.to_csv("ta_atr.csv")
