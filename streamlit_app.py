import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Branduolys
st.set_page_config(page_title="TITAN OMNI-SCANNER V210", layout="wide")
st_autorefresh(interval=30000, key="v210_refresh")

if 'wallet' not in st.session_state: 
    st.session_state.wallet = 1711.45

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:] 
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    # --- RODIKLIŲ SKAIČIAVIMAS ---
    cur_p = df.iloc[-1]['close'] # ~1,749.83€
    
    # RSI Skaičiavimas (pagal tavo nuotraukų logiką)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
    rs = gain / loss
    rsi = round(100 - (100 / (1 + rs)).iloc[-1], 2) # ~60.17

    # Bollingerio juostos (Svyravimo ribos)
    sma = df['close'].rolling(window=20).mean().iloc[-1]
    std = df['close'].rolling(window=20).std().iloc[-1]
    upper_band = round(sma + (std * 2), 2)
    lower_band = round(sma - (std * 2), 2)

    # 24h High/Low iš tavo fiksacijų
    day_high = 1758.64 
    day_low = 1660.00

    st.markdown(f"<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN OMNI-SCANNER V210</h1>", unsafe_allow_html=True)

    # --- 1 DALIS: RODIKLIŲ SKYDAS ---
    st.subheader("🛠️ Techninių Rodiklių Suvestinė")
    r1, r2, r3, r4 = st.columns(4)
    
    # RSI Logika
    rsi_color = "green" if rsi < 70 else "red"
    r1.markdown(f"**RSI(6):** <span style='color:{rsi_color}'>{rsi}</span>", unsafe_allow_html=True)
    r1.caption("Žemiau 70 - Buliams gerai, virš 70 - perkaitę.")

    # Tendencijos Logika
    trend_color = "green" if cur_p > sma else "red"
    r2.markdown(f"**TRENDAS (SMA20):** <span style='color:{trend_color}'>{round(sma, 2)}€</span>", unsafe_allow_html=True)
    r2.caption("Kaina virš vidurkio - stiprus trendas.")

    # Bollingerio Logika
