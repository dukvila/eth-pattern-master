import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# I. BRANDUOLIO KONFIGŪRACIJA (STABILUMO GARANTAS)
# ==============================================================================
st.set_page_config(page_title="TITAN V900 GOLDEN", layout="wide")
st_autorefresh(interval=30000, key="v900_stable_refresh")

# Tavo baziniai lygiai iš nuotraukų
H24_HIGH = 1758.64  #
H24_LOW = 1660.00   #
SMA20_PIVOT = 1737.44  #

# ==============================================================================
# II. NEURAL SKENERIS (SUTAPIMAI SU CHEAT SHEETS)
# ==============================================================================
def apply_neural_engine(df):
    # RSI(6) skaičiavimas
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
    df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
    
    # SMA20 - Tavo ašis
    df['sma20'] = df['close'].rolling(20).mean()
    
    # Pattern Match: Bullish Engulfing
    df['buy_signal'] = (df['close'] > df['open']) & \
                       (df['close'].shift(1) < df['open'].shift(1)) & \
                       (df['close'] >= df['open'].shift(1))
    return df

# ==============================================================================
# III. DUOMENŲ SRAUTAS
# ==============================================================================
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return apply_neural_engine(df)
    except:
        return pd.DataFrame()

# ==============================================================================
# IV. MODERNI VALDYMO PULTAS
# ==============================================================================
df = get_data()

if not df.empty:
    now = df.iloc[-1]
    
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🚀 TITAN NEURAL V900</h1>", unsafe_allow_html=True)
    
    # KPI Blokas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("KAINA", f"{now['close']} €")
    with col2:
        st.metric("RSI(6)", round(now['rsi6'], 2))
    with col3:
        st.metric("TRENDAS", "BULL" if now['close'] > SMA20_PIVOT else "BEAR")
    with col4:
        st.metric("BALANSAS", "1711.45 €")

    st.divider()

    # Grafinis atvaizdavimas (Šiuolaikiškas Dark-Mode)
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#0E1117')
    ax.set_facecolor('#0E1117')
    
    h = df.tail(40)
    # Neoninis efektas
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=3, label='ETH Price')
    ax.plot(h['time'], h['sma20'], color='#ff00ff', linestyle='--', alpha=0.6, label='SMA20 Support')
    
    # Signalų atvaizdavimas
    buys = h[h['buy_signal']]
    ax.scatter(buys['time'], buys['close'] * 0.998, marker='^', color='#00ff00', s=150, label='BUY')
    
    # Lygių fiksavimas (IŠTAISYTA: Uždaryti skliaustai)
    ax.axhline(H24_HIGH, color='gold', alpha=0.5, label='Target High')
    ax.axhline(H24_LOW, color='red', alpha=0.3, label='Support Low')
    
    ax.tick_params(axis='x', colors='white', rotation=45)
    ax.tick_params(axis='y', colors='white')
    ax.grid(alpha=0.1)
    ax.legend(facecolor='#1E2127', labelcolor='white')
    st.pyplot(fig)

    # Analitinis Skyrius (Sutvarkyta Indentacija)
    st.subheader("🧬 Modelių Skenavimas")
    c_a, c_
