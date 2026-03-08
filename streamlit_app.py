import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V144 AGRESSIVE GUARDIAN", layout="wide")
st_autorefresh(interval=60000, key="v144_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []

# --- GARSINIS SIGNALAS ---
def play_alert():
    st.components.v1.html('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg"></audio>', height=0)

# 2. Duomenų gavimas
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['MA7'] = df['close'].rolling(window=7).mean()
            df['MA25'] = df['close'].rolling(window=25).mean()
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    ma7 = df.iloc[-1]['MA7']
    ma25 = df.iloc[-1]['MA25']
    
    # --- AGRESYVI PROGNOZĖ IR PELNAS ---
    # Skaičiuojame kiekvienos progos pelno potencialą
    y = df['close'].tail(20).values
    slope, intercept = np.polyfit(np.arange(len(y)), y, 1)
    
    # Agresyvus tikslas: jei kyla - gaudom aukščiau, jei krenta - laukiam dugno
    target_sell = cur_p + (abs(slope) * 50) if slope > 0 else cur_p + 15
    current_potential = (st.session_state.wallet / cur_p) * (target_sell - cur_p)

    st.title(f"⚡ Agresyvus Režimas: {round(st.session_state.wallet, 2)}€")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Dabartinė Kaina", f"{round(cur_p, 2)}€")
    c2.metric("Pelno Potencialas", f"{round(current_potential, 2)}€")
    c3.metric("Režimas", "AGRESYVUS (Min 10€)")

    # GRAFIKAS SU AGRESYVIA ZONA
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'].tail(40), df['close'].tail(40), label="ETH Kaina", color='#1f77b4', linewidth=2)
    ax.plot(df['time'].tail(40), df['MA7'].tail(40), label="MA
