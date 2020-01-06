from talib import RSI, STOCH, WILLR, MACD, ROC, OBV, WMA, NATR
from sklearn.ensemble import RandomForestClassifier
import pickle


def normalizeDataframe(data_frame):
    normalize_df = data_frame.copy()
    for column in normalize_df.columns:
        min_value = min(normalize_df[column])
        max_value = max(normalize_df[column])
        normalize_df[column] = (normalize_df[column] -
                                min_value) / (max_value - min_value)
    return normalize_df


def binaryClassificationInThirtyMinutes(df):
    '''
    Predict the price of bitcoin in the next 30 minutes by a given df (dataframe)

    Example: 
        binaryClassificationInThirtyMinutes(df) = 0

    Parameters:
        df: a dataframe with df.columns = ['open', 'high', 'low', 'close', 'volume']
    Returns:
        prediction: int = a prediction by the model, 0 for down, 1 for same or up
    '''

    if len(df) != 30:
        raise Exception("Dataframe must have 30 rows")

    data = df.copy()

    rsi = RSI(data['close'])
    k, d = STOCH(data['high'], data['low'], data['close'])
    macd, macdsignal, macdhist = MACD(
        data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    williams_r = WILLR(data['high'], data['low'], data['close'])
    rate_of_change = ROC(data['close'])
    on_balance_volume = OBV(data['close'], data['volume'])
    weighted_moving_average = WMA(data['close'])
    normalized_average_true_range = NATR(
        data['high'], data['low'], data['close'])

    data['rsi'] = rsi
    data['k'] = k
    data['d'] = d
    data['macd'] = macd
    data['williams_r'] = williams_r
    data['rate_of_change'] = rate_of_change
    data['on_balance_volume'] = on_balance_volume
    data['weighted_moving_average'] = weighted_moving_average
    data['normalized_average_true_range'] = normalized_average_true_range

    data = data.dropna(axis=0)
    data = normalizeDataframe(data)
    with open("random_forest_params", "rb") as file:
        model = pickle.load(file)

    features = data.values
    prediction = model.predict(features)
    return prediction[0]
