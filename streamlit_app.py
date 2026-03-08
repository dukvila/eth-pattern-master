import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Griežta Konfigūracija - Jokių klaidų
st.set_page_config(page_title="TITAN EXECUTIONER V182", layout="wide")
st_autorefresh(interval=30000, key="v182_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'trades' not in st.session_state: st.session_state.trades = []

def get_market_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

df = get_market_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    # AMD LOGIKA: Randame tikrąjį likvidumo dugną (kaip tavo 1661.75 pavyzdyje)
    # Tai yra žemiausias taškas per pastarąsias 12 valandų
    liquidity_bottom = df['low'].tail(48).min()
    
    # PIRKIMO ZONA: Tik tada, kai kaina "pramuša" dugną ir bando atšokti
    execution_buy = round(liquidity_bottom + 1.25, 2)
    # PARDAVIMO ZONA: Paskutinis lokalus pikas (Distribution)
    execution_sell = round(df['high'].tail(24).max() - 4.0, 2)

    st.markdown(f"<h1 style='text-align: center; color: #00ff44;'>🎯 TITAN EXECUTIONER V182</h1>", unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("ETH KAINA", f"{cur_p}€")
    m2.metric("AMD BUY (TARGET)", f"{execution_buy}€", "DUGNAS")
    m3.metric("AMD SELL (TARGET)", f"{execution_sell}€", "PELNAS")

    # --- GRAFIKAS: AMD MANIPULIACIJOS STEBĖJIMAS ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'], df['close'], color='#00ff44', label='Market Price', linewidth=1.5)
    
    # Vizualizuojame "Manipulation Zone" kur kaina surinko likvidumą (kaip 1661.75€)
    ax.axhspan(liquidity_bottom - 5, execution_buy, color='green', alpha=0.2, label='Manipulation (BUY)')
    ax.axhspan(execution_sell, execution_sell + 5, color='red', alpha=0.2, label='Distribution (SELL)')
    
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    ax.grid(color='#2D323E', linestyle='--', alpha=0.5)
    plt.legend()
    st.pyplot(fig)

    # --- OPERACIJŲ VALDYMAS ---
    st.divider()
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🛠️ Snaiperio Nustatymai")
        final_buy = st.number_input("Pirkimo riba (Liquidity Sweep)", value=execution_buy)
        final_sell = st.number_input("Pardavimo riba (Distribution)", value=execution_sell)
    
    with col_r:
        in_sum = st.number_input("Investicija (€)", value=1000.0)
        potential = round((in_sum / final_buy) * (final_sell - final_buy), 2)
        if st.button("🔱 PALEISTI AMD REIDĄ", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.trades.append({
                    "buy_p": final_buy, "sell_p": final_sell, "amt": in_sum, "status": "LAUKIA"
                })
                st.session_state.wallet -= in_sum
                st.success("Reidas paleistas. Laukiama pirkimo zonos.")
                st.rerun()
        st.write(f"Planuojamas pelnas: **+{potential}€**")

    # --- VYKDYMAS: JOKIŲ NUOLAIDŲ ---
    for trade in st.session_state.trades:
        if trade['status'] == "LAUKIA" and cur_p <= trade['buy_p']:
            trade['status'] = "🚀 POZICIJOJE"
        if trade['status'] == "🚀 POZICIJOJE" and cur_p >= trade['sell_p']:
            profit = (trade['amt'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amt'] + profit)
            trade['status'] = "✅ PELNAS SUGAUTAS"
            st.balloons()
