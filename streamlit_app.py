import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija - Griežtas stabilumas
st.set_page_config(page_title="TITAN SNIPER V180", layout="wide")
st_autorefresh(interval=30000, key="v180_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-120:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    # SNIPER LOGIKA: Randame tikrąjį likvidumo dugną (kaip tavo 1661.75€ pavyzdyje)
    liquidity_low = df['low'].tail(48).min() 
    # Nustatome pasipriešinimą viršuje
    resistance_high = df['high'].tail(48).max()
    
    # AMD REAKCIJOS ZONA: Perkam tik tada, kai rinka bando "apgauti" (manipuliacija)
    sniper_buy = round(liquidity_low + 1.50, 2)
    sniper_sell = round(resistance_high - 5.00, 2)

    st.markdown(f"<h1 style='text-align: center; color: #00f2ff;'>🎯 TITAN SNIPER V180</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("ETH DABAR", f"{cur_p}€")
    col2.metric("SNIPER BUY (DUGNAS)", f"{sniper_buy}€", "MEDŽIOKLĖ")
    col3.metric("SNIPER SELL (TIKSLAS)", f"{sniper_sell}€", "PROFITAS")

    # --- GRAFIKAS: AMD ZONŲ VIZUALIZACIJA ---
        fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'], df['close'], color='white', linewidth=1.5, label='Market')
    
    # Braižome zonas pagal image_67455d.png principą
    ax.axhspan(liquidity_low - 2, sniper_buy, color='green', alpha=0.3, label='MANIPULATION ZONE (PIRKTI)')
    ax.axhspan(sniper_sell, resistance_high + 2, color='red', alpha=0.3, label='DISTRIBUTION ZONE (PARDUOTI)')
    
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    plt.legend(loc='upper left')
    st.pyplot(fig)

    # --- ATSAKOMYBĖS VALDYMAS ---
    st.divider()
    c_left, c_right = st.columns(2)
    with c_left:
        st.subheader("🛠️ Snaiperio Nustatymai")
        in_buy = st.number_input("Pirkimo riba (nekeičiama)", value=sniper_buy)
        in_sell = st.number_input("Pardavimo riba (tikslas)", value=sniper_sell)
    
    with c_right:
        in_sum = st.number_input("Investicijos suma (€)", value=1000.0)
        p_profit = round((in_sum/in_buy) * (in_sell - in_buy), 2)
        if
