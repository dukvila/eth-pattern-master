import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. CORE CONFIG
st.set_page_config(page_title="TITAN V3000", layout="wide")
st_autorefresh(interval=30000, key="v3000_final")

# Tavo nustatyti lygiai
DAZN_APATINIS = 1660.00
STAT_MINIMAS = 1680.00
SMA20_ASIS = 1737.44
STAT_MAKSIMAS = 1758.64
BALANSAS = 1711.45

# 2. DATA ENGINE
def get_market_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['sma20'] = df['close'].rolling(20).mean()
            return df
    except:
        return pd.DataFrame()

# 3. INTERFACE
df = get_market_data()

if not df.empty:
    now = df.iloc[-1]
    st.markdown(f"<h1 style='text-align:center; color:#00ffcc;'>🛰️ TITAN V3000 IRONCLAD</h1>", unsafe_allow_html=True)
    
    # KPI Hub
    c1, c2, c3 = st.columns(3)
    c1.metric("ESAMA KAINA", f"{now['close']} €")
    c2.metric("SMA20 AŠIS", f"{SMA20_ASIS} €")
    c3.metric("BALANSAS", f"{BALANSAS} €")

    st.divider()

    # 4. GRAPH ENGINE (FIXED SYNTAX)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 5))
    h = df.tail(48) # 48 salizio langas

    # Ištaisyta 84 eilutė
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Kaina')
    ax.plot(h['time'], h['sma20'], color='#ff00ff', linestyle='--', alpha=0.5, label='SMA20')

    # Ištaisyta 103 eilutė - Dažnio linijos
    ax.axhline(DAZN_APATINIS, color='red', linestyle='-', alpha=0.8, label='Apatinis (1660)')
    ax.axhline(STAT_MINIMAS, color='red', linestyle=':', alpha=0.4)
    ax.axhline(SMA20_ASIS, color='white', linestyle='-', alpha=0.5, label='SMA20 Ašis')
    ax.axhline(STAT_MAKSIMAS, color='yellow', linestyle=':', alpha=0.4)
    ax.axhline(1780.78, color='yellow', linestyle='-', alpha=0.8, label='Viršutinis (1780)')

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.legend(loc='upper left', fontsize='small')
    st.pyplot(fig)

    # 5. ANALYTICS HUB (FIXED COLUMN NAMES)
    st.subheader("🧬 Strateginis Skenavimas")
    col_l, col_r = st.columns(2)
    
    with col_l:
        if now['close'] > SMA20_ASIS:
            st.success(f"BULLISH: Kaina virš vidurkio ({SMA20_ASIS}€)")
        else:
            st.warning("BEARISH: Kaina po vidurkiu")

    with col_r:
        if now['close'] >= STAT_MAKSIMAS:
            st.error("PARDAVIMO ZONA: Pasiektas statistinis maksimumas")
        elif now['close'] <= STAT_MINIMAS:
            st.success("PIRKIMO ZONA: Pasiektas statistinis minimas")
        else:
            st.info("NEUTRALU: Kaina svyruoja tarp dažnio ribų")
