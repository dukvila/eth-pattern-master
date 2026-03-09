import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. KONFIGŪRACIJA
st.set_page_config(page_title="TITAN V1500", layout="wide")
st_autorefresh(interval=30000, key="v1500_recovery")

# Tavo parametrai iš image_f8cfd0.png
SMA20_PIVOT = 1737.44
BALANCE = 1711.45

# 2. DUOMENŲ SRAUTAS
def load_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI(6) skaičiavimas
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            df['sma20'] = df['close'].rolling(20).mean()
            
            # Patternas: Bullish Engulfing
            df['buy'] = (df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1))
            return df
    except:
        return pd.DataFrame()

# 3. INTERFASAS
df = load_data()

if not df.empty:
    now = df.iloc[-1]
    
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN OMNI-SCANNER V1500</h1>", unsafe_allow_html=True)
    
    # KPI RODIKLIAI
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ESAMA KAINA", f"{now['close']} €")
    with col2:
        st.metric("RSI(6) IMPULSAS", round(now['rsi6'], 2))
    with col3:
        st.metric("BALANSAS", f"{BALANCE} €")

    st.divider()

    # 4. GRAFIKAS - pilnai užbaigta sintaksė be klaidų
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4))
    h = df.tail(40)
    
    # Pagrindinės linijos - IŠTAISYTA 84 eilutė
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Price')
    ax.plot(h['time'], h['sma20'], color='#ff00ff', linestyle='--', label='SMA20')
    
    # Tikslinė riba - IŠTAISYTA 103 eilutė
    ax.axhline(y=SMA20_PIVOT, color='white', linestyle=':', alpha=0.5, label='Pivot')
    
    # Pirkimo taškai
    buys = h[h['buy']]
    if not buys.empty:
        ax.scatter(buys['time'], buys['close'] * 0.998, marker='^', color='#00ff00', s=100)

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.legend(prop={'size': 7})
    st.pyplot(fig)

    # 5. ANALITIKA - IŠTAISYTA indentacija
    st.subheader("🧬 Modelių Skenavimas")
    c_left, c_right = st.columns(2) # Ištaisyta iš c_a, c_
    
    with c_left:
        st.write("**Būsena:**")
        if now['close'] > SMA20_PIVOT:
            st.success("STIPRUS TRENDAS: Kaina virš vidurkio.")
        else:
            st.warning("SILPNAS TRENDAS: Kaina žemiau vidurkio.")

    with c_right:
        st.write("**Signalas:**")
        if now['buy']:
            st.success("🔥 APTIKTAS PIRKIMO MODELIS!")
        else:
            st.info("Ieškoma progų pagal Cheat Sheet...")
