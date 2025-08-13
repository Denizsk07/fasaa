"""Technical Indicators Module"""
import pandas as pd
import pandas_ta as ta
import numpy as np

class TechnicalAnalysis:
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df['ema_20'] = ta.ema(df['close'], length=20)
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['rsi'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'])
        if macd is not None:
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        stoch = ta.stoch(df['high'], df['low'], df['close'])
        if stoch is not None:
            df['stoch_k'] = stoch['STOCHk_14_3_3']
            df['stoch_d'] = stoch['STOCHd_14_3_3']
        return df
