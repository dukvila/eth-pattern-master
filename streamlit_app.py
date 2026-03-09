import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. BRANDUOLYS
st.set_page_config(page_title="TITAN V1300", layout="wide")
st_autorefresh(interval=30000, key="v1300_core")

# Tavo nustatymai
SMA20_LEVEL = 1737.44
USER_BALANCE = 1711.45

# 2. DUOMENŲ VARIKLIS
def fetch_titan_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # Rodikliai
            df['sma20'] = df['close'].rolling(20).mean()
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            
            # Patternai
            df['is_bull'] = (df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1))
            return df
    except:
        return pd.DataFrame()

# 3. TERMINALAS
df = fetch_titan_data()

if not df.empty:
    now = df.iloc[-1]
    
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN COMMAND V1300</h1>", unsafe_allow_html=True)
    
    # KPI Blokas
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("ETH KAINA", f"{now['close']} €")
    with m2:
        st.metric("RSI(6) STATUSAS", round(now['rsi6'], 2))
    with m3:
        st.metric("BALANSAS", f"{USER_BALANCE} €")

    st.divider()

    # SAUGUS GRAFIKAS (Visi skliaustai uždaryti rankiniu būdu)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4))
    h = df.tail(40)
    
    # Pagrindinės linijos
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Kaina')
    ax.plot(h['time'], h['sma20'], color='#ff00ff', linestyle='--', label='SMA20')
    
    # Tavo tikslinė linija
    ax.axhline(y=SMA20_LEVEL, color='white', linestyle=':', alpha=0.5)
    
    # Pirkimo signalai
    buys = h[h['is_bull']]
    if not buys.empty:
        ax.scatter(buys['time'], buys['close'] * 0.998, marker='^', color='#00ff00', s=100)

    # Estetika
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.legend(loc='upper left', fontsize='small')
    st.pyplot(fig)

    # ANALITIKOS SKILTIS (Ištaisyta indentacija ir dvitaškiai)
    st.subheader("🧬 Rinkos Skenavimas")
    c_a, c_b = st.columns(2)
    
    with c_a:
        st.write("**Techninė būsena:**")
        if now['close'] > SMA20_LEVEL:
            st.success(f"Kaina VIRŠ vidurkio ({SMA20_LEVEL}€) - Trendas stiprus.")
        else:
            st.warning(f"Kaina ŽEMIAU vidurkio - būk atsargus.")

    with c_b:
        st.write("**Žvakių analizė:**")
        if now['is_bull']:
            st.success("🔥 Aptiktas pirkimo modelis (Bullish Engulfing)!")
        else:
            st.info("Laukiama patvirtinto signalo...")
