import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
import math
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V173 TITAN SCALPER", layout="wide")
st_autorefresh(interval=45000, key="v173_refresh") # Greitesnis atnaujinimas

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []
if 'auto_raid' not in st.session_state: st.session_state.auto_raid = False

# Patikslinta tikimybė skalpavimui
def get_probability(current, target, std):
    if std < 0.1: std = 0.5
    diff = abs(current - target)
    prob = 1 / (1 + math.exp(diff / (std * 1.5))) * 180
    return max(min(prob, 99.9), 0.1)

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-200:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['MA25'] = df['close'].rolling(window=25).mean()
            df['STD'] = df['close'].rolling(window=20).std()
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    std_val = df.iloc[-1]['STD']
    ma25 = df.iloc[-1]['MA25']
    
    # Trumpalaikis tikslas (Scalping)
    smart_buy = round(cur_p - (std_val * 0.3), 2) # Perka arčiau esamos kainos
    smart_sell = round(cur_p + (std_val * 0.5), 2) # Parduoda greičiau

    # --- VALDYMAS ---
    st.sidebar.title("🎮 Scalper Mode")
    st.session_state.auto_raid = st.sidebar.toggle("🤖 AUTO-SCALP", value=st.session_state.auto_raid)
    
    # --- LOGIKA ---
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA" and cur_p <= trade['buy_p']:
            trade['status'] = "🚀 VYKDOMAS"
        if trade['status'] == "🚀 VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "✅ PELNAS"
            trade['profit_eur'] = profit
            st.session_state.history.append(trade)
            st.balloons()

    if st.session_state.auto_raid and not any(t['status'] in ["LAUKIA", "🚀 VYKDOMAS"] for t in st.session_state.active_trades):
        if st.session_state.wallet >= 500:
            st.session_state.active_trades.append({"buy_p": smart_buy, "sell_p": smart_sell, "amount": 500.0, "status": "LAUKIA"})
            st.session_state.wallet -= 500.0
            st.rerun()

    # --- EKRANAS ---
    st.title(f"💰 Scalper V173: {round(st.session_state.wallet, 2)}€")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("ESAMA KAINA", f"{cur_p}€")
    c2.metric("SIŪLOMAS PIRKIMAS", f"{smart_buy}€")
    c3.metric("SIŪLOMAS PARDAVIMAS", f"{smart_sell}€")

    st.divider()
    # Rankinis koregavimas (neatšoka!)
    col_in, col_prob = st.columns([2, 1])
    with col_in:
        in_buy = st.number_input("Tavo Pirkimas", value=smart_buy, key="b_v173")
        in_sell = st.number_input("Tavo Pardavimas", value=smart_sell, key="s_v173")
        if st.button("🚀 PALEISTI MEDŽIOKLĘ", use_container_width=True):
            st.session_state.active_trades.append({"buy_p": in_buy, "sell_p": in_sell, "amount": 500.0, "status": "LAUKIA"})
            st.session_state.wallet -= 500.0
            st.rerun()

    with col_prob:
        st.write("📈 **Tikimybė:**")
        st.title(f"{round(get_probability(cur_p, in_buy, std_val), 1)}%")

    # GRAFIKAS
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df['time'].tail(40), df['close'].tail(40), color="#1f77b4")
    ax.axhline(y=in_buy, color='green', linestyle='--', label="Pirkimas")
    ax.axhline(y=in_sell, color='red', linestyle='--', label="Pardavimas")
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    st.pyplot(fig)
