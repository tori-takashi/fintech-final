import pandas as pd
import talib as ta

data = pd.read_csv("ohlcv_with_future.csv")

high = data["high"]
low = data["low"]
close = data["close"]
volume = data["volume"]
data["timestamp"] = pd.to_datetime(data["timestamp"])

ta_AD = ta.AD(high, low, close, volume)
output = pd.DataFrame(
    data={
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "timestamp": data["timestamp"],
        "ta_AD": ta_AD}
)
output.reset_index(inplace=True, drop=True)
output.to_csv("ta_ad.csv")
