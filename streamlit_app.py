import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# I. GLOBALŪS PARAMETRAI IR KLAIDŲ SKANERIS
# ==============================================================================
st.set_page_config(page_title="TITAN V700", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=30000, key="v700_core_refresh")

# Tavo balanso bazė
if 'wallet' not in st.session_state:
    st.session_state.wallet = 1711.45

# ==============================================================================
# II. ŽVAKIŲ MODELIŲ VARIKLIS (IŠ TAVO CHEAT SHEET)
# ==============================================================================
def detect_patterns(df):
    """Skenuoja sutapimus pagal tavo image_f8c0aa.png ir image_f8bff8.jpg."""
    # Bullish Engulfing detektorius
    df['pattern_bull'] = (df['close'] > df['open']) & \
                         (df['close'].shift(1) < df['open'].shift(1)) & \
                         (df['close'] >= df['open'].shift(1))
    
    # RSI(6) tikslumas pagal tavo Binance ekranus
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
    df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
    
    # Tavo SMA20 ašis
    df['sma20'] = df['close'].rolling(20).mean()
    return df

# ==============================================================================
# III. DUOMENŲ GAVIMAS IR ANALIZĖ
# ==============================================================================
@st.cache_data(ttl=30)
def get_titan_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return detect_patterns(df)
    except:
        return pd.DataFrame()

# ==============================================================================
# IV. ŠIUOLAIKIŠKA VIZUALIZACIJA (3D EFEKTAS 2D ERDVĖJE)
# ==============================================================================
df = get_titan_data()

if not df.empty:
    now = df.iloc[-1]
    
    # Kritiniai taškai iš tavo archyvo
    H24_HIGH = 1758.64
    H24_LOW = 1660.00
    SMA20_PIVOT = 1737.44

    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN NEURAL V700</h1>", unsafe_allow_html=True)
    
    # --- KPI HUBAS ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("SPOT KAINA", f"{now['close']} €", f"{round(now['close']-df.iloc[-2]['close'], 2)}")
    with c2:
        st.metric("RSI(6) IMPULSAS", round(now['rsi6'], 2))
    with c3:
        st.metric("SMA20 STATUSAS", "BULLISH" if now['close'] > SMA20_PIVOT else "BEARISH")
    with c4:
        st.metric("PORTFELIS", f"{st.session_state.wallet} €")

    st.markdown("---")

    # --- MODERNI GRAFIKA ---
    tab1, tab2 = st.tabs(["🚀 NEURAL TERMINAL", "🧬 PATTERN SCANNER"])

    with tab1:
        # Ištaisyta klaida iš image_14197c.png - dabar indentacija ideali
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(15, 7))
        hist = df.tail(45)
        
        # 3D gylio imitacija (Švytėjimas)
        ax.fill_between(hist['time'], hist['close'], hist['sma20'], color='#00ffcc', alpha=0.1)
        ax.plot(hist['time'], hist['close'], color='#00ffcc', linewidth=4, label='ETH/EUR Core')
        ax.plot(hist['time'], hist['sma20'], color='#ff00ff', linestyle='--', alpha=0.6, label='SMA20 Pivot')
        
        # Signalai pagal tavo "Buy/Sell" logiką
        buys = hist[hist['pattern_bull']]
        ax.scatter(buys['time'], buys['close'] * 0.998, marker='^', color='#00ff00', s=200, label='BUY PATTERN')
        
        # Tikslinės ribos
        ax.axhline(H24_HIGH
