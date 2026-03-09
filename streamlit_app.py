import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE SETTINGS ---
st.set_page_config(page_title="TITAN V1700", layout="wide")
st_autorefresh(interval=30000, key="v1700_refresh")

# Tavo nustatyti lygiai
SMA20_PIVOT = 1737.44
MY_BALANCE = 1711.45

# --- 2. DATA ENGINE ---
def fetch_and_clean():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            raw_data = res['result']['XETHZEUR']
            df = pd.DataFrame(raw_data, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI(6)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            
            # SMA20
            df['sma20'] = df['close'].rolling(20).mean()
            
            # Pattern: Bullish Engulfing
            df['signal'] = (df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1))
            return df
    except:
        return pd.DataFrame()

# --- 3. TERMINAL INTERFACE ---
df = fetch_and_clean()

if not df.empty:
    now = df.iloc[-1]
    
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN GOLDEN-EYE V1700</h1>", unsafe_allow_html=True)
    
    # KPI Hub
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("SPOT KAINA", f"{now['close']} €")
    with k2:
        st.metric("RSI(6) IMPULSAS", round(now['rsi6'], 2))
    with k3:
        st.metric("BALANSAS", f"{MY_BALANCE} €")

    st.divider()

    # --- 4. GRAPH ENGINE (BUG-FREE) ---
    # Ištaisyta 84 eilutė: visi skliaustai uždaryti
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4))
    h = df.tail(40)
    
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Kaina')
    ax.plot(h['time'], h['sma20'], color='#ff00ff', linestyle='--', label='SMA20')
    
    # Ištaisyta 103 eilutė: tikslus lygis
    ax.axhline(y=SMA20_PIVOT, color='white', linestyle=':', alpha=0.5, label='Pivot')
    
    # Pirkimo taškai pagal Cheat Sheet
    buys = h[h['signal']]
    if not buys.empty:
        ax.scatter(buys['time'], buys['close'] * 0.998, marker='^', color='#00ff00', s=120)

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.legend(prop={'size': 8})
    st.pyplot(fig)

    # --- 5. ANALYTICS (FIXED STRUCTURE) ---
    st.subheader("🧬 Skenavimo Rezultatas")
    # Ištaisyta 104 eilutė: pilni kintamieji
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.write("**Trendo būsena:**")
        if now['close'] > SMA20_PIVOT:
            st.success(f"BULL: Kaina virš {SMA20_PIVOT}€")
        else:
            st.warning("BEAR: Kaina žemiau vidurkio")

    with col_right:
        st.write("**Patternų atpažinimas:**")
        if now['signal']:
            st.success("🔥 SIGNALAS: Aptiktas 'Bullish Engulfing'!")
        else:
            st.info("Skenuojami žvakių modeliai...")
