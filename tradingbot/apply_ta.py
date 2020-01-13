import pandas as pd

from technical_analysis.ad import TechnicalAnalysisAD
from technical_analysis.atr import TechnicalAnalysisATR
from technical_analysis.bollinger_band import TechnicalAnalysisBB
from technical_analysis.SAR import TechnicalAnalysisSAR
from technical_analysis.MACD import TechnicalAnalysisMACD

dataframe = pd.read_csv("csv/ohlcv_with_past_future.csv", index_col=0)


def get_technical_indicators(df):
    ta_ad = TechnicalAnalysisAD(df)
    ad_df = ta_ad.get_ad()

    ta_atr = TechnicalAnalysisATR(df)
    atr_df = ta_atr.get_atr()

    ta_sar = TechnicalAnalysisSAR(df)
    sar_df = ta_sar.get_psar_trend()

    ta_macd = TechnicalAnalysisMACD(df)
    ta_macd.generate_ema_macd()
    macd_df = ta_macd.get_ema_macd()

    ta_applied = pd.concat([df, ad_df, atr_df, sar_df, macd_df], axis=1)
    ta_applied.dropna(inplace=True)
    ta_applied.reset_index(inplace=True, drop=True)

    return ta_applied


ohlcv_ta_applied = get_technical_indicators(dataframe)
ohlcv_ta_applied.to_csv("csv/ta_applied_ohlcv_with_past_future.csv")
print(ohlcv_ta_applied)
