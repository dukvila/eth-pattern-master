import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. SISTEMOS PAMATAI
st.set_page_config(page_title="TITAN V1200", layout="wide")
st_autorefresh(interval=30000, key="v1200_final")

# Nustatymai iš tavo nuotraukų
SMA20_LEVEL = 1737.44  #
BALANCE = 1711.45      #

# 2. ANALITIKOS VARIKLIS (TAVO CHEAT SHEET)
def get_crypto_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI(6)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            df['sma20'] = df['close'].rolling(20).mean()
            
            # Bullish Engulfing
            df['buy'] = (df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1))
            return df
    except:
        return pd.DataFrame()
