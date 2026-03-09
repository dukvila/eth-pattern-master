import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. SISTEMOS PAMATAI
st.set_page_config(page_title="TITAN V1600", layout="wide")
st_autorefresh(interval=30000, key="v1600_fixed_final")

# Rodikliai iš tavo nuotraukų
SMA20_TARGET = 1737.44  #
MY_BALANCE = 1711.45    #

# 2. DUOMENŲ VARIKLIS
def get_clean_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            raw = res['result']['XETHZEUR']
            df = pd.DataFrame(raw, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI(6) skaičiavimas
            delta = df['close'].diff()
            up = delta.clip(lower=0)
            down = -1 * delta.clip(upper=0)
            ema_up = up.rolling(6).mean()
            ema_down = down.rolling(6).mean()
            df['rsi6'] = 100 - (100 / (1 + (ema_up / ema_down)))
            
            df['sma20'] = df['close'].rolling(20).mean()
            
            # Pattern: Bullish Engulfing
            df['signal'] = (df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1))
            return df
    except:
        return pd.DataFrame()

# 3. VALDYMO PULTAS
df = get_clean_data()

if not df.empty
