import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="TITAN V2000", layout="wide")
st_autorefresh(interval=30000, key="v2000_ironclad")

# Duomenys iš tavo Cheat Sheet
TARGET_SMA20 = 1737.44
CURRENT_BAL = 1711.45

# --- 2. DATA ENGINE ---
def fetch_market_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            raw = res['result']['XETHZEUR']
            df = pd.DataFrame(raw, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # Rodikliai pagal tavo nuotraukas
            df['sma20'] = df['close'].rolling(20).mean()
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            
            # Pirkimo signalas: Bullish Engulfing
            df['buy_sig'] = (df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1))
            return df
    except:
        return pd.DataFrame()

# --- 3. TERMINAL ---
df = fetch_market_data()

if not df.empty:
    now = df.iloc[-1]
    
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🚀 TITAN V2000 IRONCLAD</h1>", unsafe_allow_html=True)
    
    # KPI Blokas
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("ETH KAINA", f"{now['close']} €")
    with m2:
        st.metric("RSI(6) IMPULSAS", round(now['rsi6'], 2))
    with m3:
        st.metric("BALANSAS", f"{CURRENT_BAL} €")

    st.divider()

    # --- 4. GRAFIKAS (IŠTAISYTA 84 IR 103 EILUTĖS) ---
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4))
    h = df.tail(40)
    
    # Ištaisyta 84 eilutė
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Price')
    ax.plot(h['time'], h['sma20'], color='#ff00ff', linestyle='--', label='SMA20')
    
    # Ištaisyta 103 eilutė
    ax.axhline(y=TARGET_SMA20, color='red', linestyle=':', alpha=0.6, label='Pivot')
    
    # Signalų atvaizdavimas
    buys = h[h['buy_sig']]
    if not buys.empty:
        ax.scatter(buys['time'], buys['close'] * 0.998, marker='^', color='#00ff00', s=100)

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.legend(prop={'size': 8})
    st.pyplot(fig)

    # --- 5. ANALITIKA (IŠTAISYTA 104 EILUTĖ) ---
    st.subheader("🧬 Rinkos Skenavimas")
    c1, c2 = st.columns(2) # Ištaisyta iš c_a, c_
    
    with c1:
        if now['close'] > TARGET_SMA20:
            st.success(f"STIPRU: Kaina virš SMA20 ({TARGET_SMA20}€)")
        else:
            st.warning("SILPNA: Kaina žemiau SMA20")

    with c2:
        if now['buy_sig']:
            st.success("🔥 PIRKIMO SIGNALAS: Bullish Engulfing!")
        else:
            st.info("Laukiama patvirtinto signalo...")
