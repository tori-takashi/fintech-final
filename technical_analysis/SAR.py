#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 10:32:33 2019

@author: chayanit
"""

import pandas as pd
import talib as ta
import matplotlib.pyplot as plt
import csv


class TechnicalAnalysisSAR:
    def __init__(self, df):
        self.df = df
        self.high = df['high']
        self.low = df['low']

        self.ta_SAR = ta.SAR(self.high, self.low, 0.02, 0.2)
        self.df["psar"] = self.ta_SAR
        self.df["trend"] = None
        self.df.loc[self.df["psar"] >= self.df["close"], "trend"] = "downtrend"
        self.df.loc[~(self.df["psar"] >= self.df["close"]),
                    "trend"] = "uptrend"

    def show_summary(self):
        plt.title('PSAR')
        plt.xlabel("Index")
        plt.ylabel("Price")
        plt.plot(self.df.index, self.high, 'blue', label="High")
        plt.plot(self.df.index, self.low, 'green', label="Low")
        plt.plot(self.df.index, self.ta_SAR, 'ro', label="SAR")
        plt.legend()
        plt.show()

    def get_psar_treand(self):
        return pd.DataFrame(self.ta_SAR)
