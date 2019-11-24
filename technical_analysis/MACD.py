import pandas as pd
import numpy as np

data = pd.read_csv("ohlcv_with_future.csv")
patt = pd.read_csv("PSAR_data.csv")


def sma_close(period):
    sma = data['close'].rolling(period).mean()
    data['sma_' + str(period)] = sma


def sma_temp(period):
    sma = data['Fast_Line'].rolling(period).mean()
    data['Slow_Line_' + str(period)] = sma


def macd(a, b, c):
    sma_close(a)
    sma_close(b)
    temp = data['sma_' + str(a)] - data['sma_' + str(b)]
    data['Fast_Line'] = temp
    sma_temp(c)


macd(12, 26, 9)

PSAR = patt['PSAR']
trend = patt['trend']

data['PSAR'] = PSAR
data['trend'] = trend


data.to_csv("ohlcv_with_future.csv")
