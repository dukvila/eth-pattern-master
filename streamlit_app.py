import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# I. QUANTUM SISTEMOS BRANDUOLYS
# ==============================================================================
st.set_page_config(page_title="TITAN COMMAND V800", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=30000, key="v800_mega_refresh")

# Tavo nustatytos vertės iš archyvo
TARGET_HIGH = 1758.64 #
TARGET_LOW = 1660.00 #
SMA20_PIVOT = 1737.44 #

# ==============================================================================
# II. NEURAL PATTERN ENGINE (IŠ TAVO CHEAT SHEETS)
# ==============================================================================
def apply_neural_logic(df):
    """Skenuoja sutapimus pagal tavo image_f8c0aa.png ir image_f8bff8.jpg."""
    # 1. Bullish Engulfing detektorius
    df['bull_engulfing'] = (df['close'] > df['open']) & \
                           (df['close'].shift(1) < df['open'].shift(1)) & \
                           (df['close'] >= df['open'].shift(1))
    
    # 2. RSI(6) High-Precision skaičiavimas
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
    df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
    
    # 3. SMA20 - Tavo pagrindinė ašis
    df['sma20'] = df['close'].rolling(20).mean()
    return df

# ==============================================================================
# III. GIGANTINĖ DUOMENŲ ANALITIKA
# ==============================================================================
@st.cache_data(ttl=30)
def fetch_institutional_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return apply_neural_logic(df)
    except Exception:
        return pd.DataFrame()

# ==============================================================================
# IV. MODERNI INTERFASO REVOLIUCIJA (NEON DARK)
# ==============================================================================
df = fetch_institutional_data()

if not df.empty:
    now = df.iloc[-1]
    
    st.markdown("<h1 style='text-align: center; color: #00ffcc;
