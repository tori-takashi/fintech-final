import pandas as pd
import numpy as np


class TechnicalAnalysisMACD:

    def __init__(self, df, fast_period=12, slow_period=16, signal_period=9):
        self.df = df

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def append_sma_close(self, ma_period):
        sma = self.df['close'].rolling(ma_period).mean()
        self.df['sma_{}'.format(ma_period)] = sma
        return self.df['sma_{}'.format(ma_period)]

    def generate_sma_macd(self):
        self.append_sma_close(self.fast_period)
        self.append_sma_close(self.slow_period)

        fast_minus_slow = self.df['sma_{}'.format(self.fast_period)] - \
            self.df['sma_{}'.format(self.slow_period)]

        self.df['fast_line'] = fast_minus_slow
        self.df['slow_line'] = self.df['fast_line'].rolling(
            self.signal_period).mean()

    def append_ema_close(self, ma_period):
        ema_sum = self.df['close'].rolling(ma_period).sum() + self.df['close']
        ema = ema_sum / (ma_period + 1)
        self.df['ema_{}'.format(ma_period)] = ema
        return self.df['ema_{}'.format(ma_period)]

    def generate_ema_macd(self):
        self.append_ema_close(self.fast_period)
        self.append_ema_close(self.slow_period)

        fast_minus_slow = self.df['ema_{}'.format(self.fast_period)] - \
            self.df['ema_{}'.format(self.slow_period)]

        self.df['fast_line'] = fast_minus_slow
        self.df['slow_line'] = self.df['fast_line'].rolling(
            self.signal_period).mean()

    def get_sma_macd(self):
        return pd.concat([
            self.df['sma_{}'.format(self.fast_period)],
            self.df['sma_{}'.format(self.slow_period)],
            self.df['fast_line'],
            self.df['slow_line']
        ], axis=1)

    def get_ema_macd(self):
        return pd.concat([
            self.df['ema_{}'.format(self.fast_period)],
            self.df['ema_{}'.format(self.slow_period)],
            self.df['fast_line'],
            self.df['slow_line']
        ], axis=1)
