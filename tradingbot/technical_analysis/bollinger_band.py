#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 00:55:30 2019

@author: punyapapoonapanont
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class TechnicalAnalysisBB:
    def __init__(self, df):
        self.df = df

        self.df.rename(columns={'timestamp': 'Date', 'open': 'Open', 'high': 'High',
                                'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        print("Data loaded:", len(self.df), "rows")
        self.df['Close'].plot(figsize=(9, 5))

    def plot_candles(self, lines=100):
        self.df['Bar'] = self.df['High'] - self.df['Low']
        self.df['Body'] = abs(self.df['Close'] - self.df['Open'])
        self.df['Up'] = self.df['Close'] > self.df['Open']
        self.df['Color'] = np.where(self.df['Up'], "g", "r")
        if lines > 0:
            db = self.df[-lines:].reset_index(drop=True).reset_index()
        else:
            db = self.df.reset_index(drop=True).reset_index()
        plt.figure(figsize=(9, 5))
        plt.bar(db['index'], bottom=db['Low'],
                height=db['Bar'], color="#000000", width=0.2)
        plt.bar(db['index'], bottom=np.where(db['Up'], db['Open'],
                                             db['Close']), height=db['Body'], color=db['Color'], width=0.9)
        plt.plot(db['OVB'], color="b")
        plt.plot(db['OVS'], color="b")
        plt.show()

    def get_stats(self, high_col="Close", low_col="Close", high_dev="OVB", low_dev="OVS", dev=2):
        total = len(self.df)
        inside = len(self.df[(self.df[high_col] <= self.df[high_dev]) & (
            self.df[low_col] >= self.df[low_dev])])
        upside = len(self.df[self.df[high_col] >= self.df[high_dev]])
        downside = len(self.df[self.df[low_col] <= self.df[low_dev]])
        i = np.round(inside / total * 100, 2)
        u = np.round(upside / total * 100, 2)
        d = np.round(downside / total * 100, 2)
        # Print the stats
        print("Total bars:", total)
        print("Deviation", dev)
        print("Inside: ", i, "%", sep="")
        print("Up side: ", u, "%", sep="")
        print("Down side: ", d, "%", sep="")

    def add_bb(self, dev=2, lb=20, col="Close"):
        self.df['MA'] = self.df[col].rolling(lb).mean()
        self.df['STD'] = self.df[col].rolling(lb).std()
        self.df['OVB'] = self.df['MA'] + self.df['STD'] * dev
        self.df['OVS'] = self.df['MA'] - self.df['STD'] * dev

    def show_summary(self, dev=2, lines=100):
        self.plot_candles(lines=lines)
        self.get_stats(dev=dev)

    def get_bb(self):
        return pd.concat([
            self.df['MA'],
            self.df['STD'],
            self.df['OVB'],
            self.df['OVS']
        ], axis=1)
