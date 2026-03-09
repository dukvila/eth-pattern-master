import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. BRANDUOLYS ---
st.set_page_config(page_title="TITAN V1400", layout="wide")
st_autorefresh(interval=30000, key="v1400_fixed")

# Tavo nustatymai iš nuotraukų
SMA20_LEVEL = 1737.44  #
BALANCE_NOW = 1711.45   #

# --- 2. DUOMENŲ VARIKLIS ---
def get_titan_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            data = res['result']['XETHZEUR']
            df = pd.DataFrame(data, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI(6)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            df['sma20'] = df['close'].rolling(20).mean()
            
            # Patternai
            df['is_bull'] = (df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1))
            return df
    except:
        return pd.DataFrame()

# --- 3. TERMINALAS ---
df = get_titan_data()

if not df.empty:
    now = df.iloc[-1]
    
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🚀 TITAN GOLIATH V1400</h1>", unsafe_allow_html=True)
    
    # KPI BLOKAS
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ETH KAINA", f"{now['close']} €")
    with col2:
        st.metric("RSI(6)", round(now['rsi6'], 2))
    with col3:
        st.metric("BALANSAS", f"{BALANCE_NOW} €")

    st.divider()

    # --- 4. GRAFIKAS (TIKSLIAI PAGAL NUOTRAUKAS) ---
    # Ištaisytos visos skliaustų klaidos
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4))
    h = df.tail(40)
    
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Price')
    ax.plot(h['time'], h['sma20'], color='#ff00ff', linestyle='--', label='SMA20')
    ax.axhline(y=SMA20_LEVEL, color='white', linestyle=':', alpha=0.4)
    
    # Signalai
    buys = h[h['is_bull']]
    if not buys.empty:
        ax.scatter(buys['time'], buys['close'] * 0.998, marker='^', color='#00ff00', s=100)

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.legend(fontsize='x-small')
    st.pyplot(fig)

    # --- 5. ANALITIKA (IŠTAISYTA INDENTACIJA) ---
    # Ištaisytos klaidos iš image_f8cc0f.png ir image_f856f8.png
    st.subheader("🧬 Skenavimo Rezultatas")
    c_left, c_right = st.columns(2)
    
    with c_left:
        st.write("**Trendas:**")
        if now['close'] > SMA20_LEVEL:
            st.success(f"VIRŠ SMA20 ({SMA20_LEVEL}€) - STIPRU")
        else:
            st.warning("ŽEMIAU SMA20 - RIZIKA")

    with c_right:
        st.write("**Signalas:**")
        if now['is_bull']:
            st.success("🔥 BULLISH ENGULFING!")
        else:
            st.info("Ieškoma progų...")
