import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. CORE SETUP
st.set_page_config(page_title="TITAN V9000", layout="wide")
st_autorefresh(interval=60000, key="v9000_refresh")

# Tavo baziniai duomenys
SMA20_PIVOT = 1737.44
MY_BALANCE = 1711.45

# 2. DATA ENGINE
def get_clean_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            data = res['result']['XETHZEUR']
            df = pd.DataFrame(data, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI(6) Impulsas
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            
            # 4H PROGNOZĖ (Linear Regression)
            y = df['close'].tail(32).values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            f_idx = np.arange(len(y), len(y) + 16)
            preds = slope * f_idx + intercept
            
            return df, preds, slope
    except:
        return pd.DataFrame(), None, 0

# 3. INTERFACE
df, prediction, slope = get_clean_data()

if not df.empty:
    now = df.iloc[-1]
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN V9000: NEW PROJECT</h1>", unsafe_allow_html=True)
    
    # Valdymo pultas šone
    st.sidebar.header("🕹️ Kontrolė")
    user_entry = st.sidebar.number_input("Tavo Pirkimo Kaina (€):", value=now['close'])
    risk_pct = st.sidebar.slider("Leistina Rizika (%)", 0.5, 5.0, 1.5)
    sl_price = user_entry * (1 - risk_pct / 100)

    # Metrikos
    m1, m2, m3 = st.columns(3)
    m1.metric("ESAMA KAINA", f"{now['close']} €")
    m2.metric("SMA20 AŠIS", f"{SMA20_PIVOT} €")
    m3.metric("RSI(6) BŪSENA", f"{round(now['rsi6'], 1)}%")

    st.divider()

    # 4. GRAFIKAS (SAUGI SINTAKSĖ)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    h = df.tail(60)

    # Tikroji kaina - Ištaisyta 84 eilutė
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Rinka')
    
    # Perpirkimas (
