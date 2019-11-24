#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 10:32:33 2019

@author: chayanit
"""

import pandas as pd;
import talib as ta;
import matplotlib.pyplot as plt;
import csv;

data = pd.read_csv('ohlcv_with_future.csv');

high = data['high'];
low = data['low'];

ta_SAR = ta.SAR(high, low, 0.02, 0.2);

plt.title('PSAR');
plt.xlabel("Index");
plt.ylabel("Price");
plt.plot(data.index, high,'blue',label="High")
plt.plot(data.index, low,'green',label="Low")
plt.plot(data.index, ta_SAR, 'ro',label="SAR")
plt.legend();
plt.show();

with open('PSAR_data.csv','w') as file:
    fieldnames = ['index', 'timestamp', 'high', 'low','PSAR','trend']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for i in range(len(data.index)):
        trend = "";
        if(ta_SAR[i]>=high.iloc[i]):
            trend = "downtrend"
        elif(ta_SAR[i]<=low.iloc[i]):
            trend = "uptrend"
        writer.writerow({'index': i, 'timestamp': data['timestamp'].iloc[i],'high': high.iloc[i],'low': low.iloc[i],'PSAR':ta_SAR[i],'trend':trend})