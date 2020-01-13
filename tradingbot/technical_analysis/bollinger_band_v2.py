import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('ohlcv_with_future.csv')
df.rename(columns={'timestamp': 'Date', 'open': 'Open', 'high': 'High',
                   'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
df.sort_values(by="Date", ascending=True, inplace=True)
print("Data loaded:", len(df), "rows")

df['Close'].plot(figsize=(9, 5))


def plot_candles(df, lines=100):
    df['Bar'] = df['High'] - df['Low']
    df['Body'] = abs(df['Close'] - df['Open'])
    df['Up'] = df['Close'] > df['Open']
    df['Color'] = np.where(df['Up'], "g", "r")
    if lines > 0:
        db = df[-lines:].reset_index(drop=True).reset_index()
    else:
        db = df.reset_index(drop=True).reset_index()
    plt.figure(figsize=(9, 5))
    plt.bar(db['index'], bottom=db['Low'],
            height=db['Bar'], color="#000000", width=0.2)
    plt.bar(db['index'], bottom=np.where(db['Up'], db['Open'],
                                         db['Close']), height=db['Body'], color=db['Color'], width=0.9)
    plt.plot(db['OVB'], color="b")
    plt.plot(db['OVS'], color="b")
    plt.show()


def get_stats(df, high_col="Close", low_col="Close", high_dev="OVB", low_dev="OVS", dev=2):
    total = len(df)
    inside = len(df[(df[high_col] <= df[high_dev])
                    & (df[low_col] >= df[low_dev])])
    upside = len(df[df[high_col] >= df[high_dev]])
    downside = len(df[df[low_col] <= df[low_dev]])
    i = np.round(inside / total * 100, 2)
    u = np.round(upside / total * 100, 2)
    d = np.round(downside / total * 100, 2)
    # Print the stats
    print("Total bars:", total)
    print("Deviation", dev)
    print("Inside: ", i, "%", sep="")
    print("Up side: ", u, "%", sep="")
    print("Down side: ", d, "%", sep="")


def add_bb(df, dev=2, lb=20, col="Close", lines=100):
    df['MA'] = df[col].rolling(lb).mean()
    df['STD'] = df[col].rolling(lb).std()
    df['OVB'] = df['MA'] + df['STD'] * dev
    df['OVS'] = df['MA'] - df['STD'] * dev
    plot_candles(df, lines=lines)
    get_stats(df, dev=dev)


dev = 2  # standard deviation
lb = 20  # simple moving average (SMA) of last 20 bars including the final bar
lines = 500  # plot last 500 bars only
add_bb(df, dev=dev, lb=lb, lines=lines)


# Add difference between upper band and lower band to table
df['Diff_OVB'] = df['OVB'] - df['Close']
df['Diff_OVS'] = df['Close'] - df['OVS']
