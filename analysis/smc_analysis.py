"""Smart Money Concepts Analysis"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional

class SMCAnalysis:
    def find_order_blocks(self, df: pd.DataFrame) -> List[Tuple[float, float]]:
        order_blocks = []
        for i in range(10, len(df)-1):
            if df.iloc[i]['close'] > df.iloc[i]['open']:
                if df.iloc[i+1]['close'] < df.iloc[i]['low']:
                    order_blocks.append(('bearish', df.iloc[i]['high'], df.iloc[i]['low']))
            elif df.iloc[i]['close'] < df.iloc[i]['open']:
                if df.iloc[i+1]['close'] > df.iloc[i]['high']:
                    order_blocks.append(('bullish', df.iloc[i]['high'], df.iloc[i]['low']))
        return order_blocks[-5:] if order_blocks else []
    
    def find_liquidity_zones(self, df: pd.DataFrame) -> List[float]:
        zones = []
        for i in range(20, len(df)-20):
            window = df.iloc[i-20:i+20]
            if df.iloc[i]['high'] == window['high'].max():
                zones.append(df.iloc[i]['high'])
            if df.iloc[i]['low'] == window['low'].min():
                zones.append(df.iloc[i]['low'])
        return zones[-10:] if zones else []
