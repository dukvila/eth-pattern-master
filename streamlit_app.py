import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# I. BRANDUOLIO KONFIGŪRACIJA (TOTAL STABILITY)
# ==============================================================================
st.set_page_config(page_title="TITAN V1000", layout="wide")
st_autorefresh(interval=30000, key="v1000_final_refresh")

# Tavo istoriniai lygiai iš Binance
TARGET_HIGH = 1758.64
TARGET_LOW = 1660.00
SMA20_PIVOT = 1737.44 # Tavo ašis iš image_f8cfd0.png

# ==============================================================================
# II. NEURAL ENGINE (TAVO CHEAT SHEETS)
# ==============================================================================
def apply_titan_logic(df):
    # RSI(6) tikslumas
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
    df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
    
    # SMA20 - Trendo indikatorius
    df['sma20'] = df['close'].rolling(20).mean()
    
    # Pattern Match: Bullish Engulfing iš image_f8c0aa.png
    df['buy_signal'] = (df['close'] > df['open']) & \
                       (df['close'].shift(1) < df['open'].shift(1)) & \
                       (df['close'] >= df['open'].shift(1))
    return df

# ==============================================================================
# III. DUOMENŲ SRAUTAS (SAFE FETCH)
# ==============================================================================
def fetch_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return apply_titan_logic(df)
    except:
        return pd.DataFrame()

# ==============================================================================
# IV. MODERNI INTERFASO ARCHITEKTŪRA
# ==============================================================================
df = fetch_data()

if not df.empty:
    now = df.iloc[-1]
    
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN ULTIMATE V1000</h1>", unsafe_allow_html=True)
    
    # --- KPI HUB ---
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("SPOT KAINA", f"{now['close']} €", f"{round(now['close']-df.iloc[-2]['close'], 2)}")
    with k2:
        st.metric("RSI(6) IMPULSAS", round(now['rsi6'], 2))
    with k3:
        st.metric("SMA20 STATUS", "VIRŠ (BULL)" if now['close'] > SMA20_PIVOT else "PO (BEAR)")
    with k4:
        st.metric("BALANSAS", "1711.45 €")

    st.divider()

    # --- MODERNUS GRAFIKAS (IŠTAISYTA) ---
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    h = df.tail(45)
