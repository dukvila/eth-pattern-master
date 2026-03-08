import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
import math
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V172 TITAN ULTIMATUM", layout="wide")
st_autorefresh(interval=60000, key="v172_refresh")

# Sesijos atmintis (Naudojame tavo realų balansą 1711.45€)
if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []
if 'auto_raid' not in st.session_state: st.session_state.auto_raid = False

# PATAISYTA: Tikimybės be 'scipy' bibliotekos (veiks visur)
def get_probability(current, target, std):
    if std < 0.1: std = 0.5
    # Naudojame Sigmoid funkciją atstumui įvertinti
    diff = abs(current - target)
    prob = 1 / (1 + math.exp(diff / (std * 2))) * 200
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
            df['MA100'] = df['close'].rolling(window=100).mean()
            df['STD'] = df['close'].rolling(window=20).std()
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    std_val = df.iloc[-1]['STD']
    ma100 = df.iloc[-1]['MA100']
    
    # Prognozė
    y_vals = df['close'].tail(16).values 
    slope, intercept = np.polyfit(np.arange(len(y_vals)), y_vals, 1)
    target_20h = slope * 80 + intercept

    # --- ŠONINIS VALDYMAS ---
    st.sidebar.title("🎮 Nustatymai")
    st.session_state.auto_raid = st.sidebar.toggle("🤖 AUTO-RAID", value=st.session_state.auto_raid)
    mode = st.sidebar.select_slider("Rizika", options=["SAUGUS", "SUBALANSUOTAS", "AGRESYVUS"], value="SUBALANSUOTAS")
    
    # Protingos rekomendacijos
    if mode == "SAUGUS": buy_off, prof_t = 0.8, 1.5
    elif mode == "AGRESYVUS": buy_off, prof_t = 0.2, 5.0
    else: buy_off, prof_t = 0.5, 2.5
    
    smart_buy = round(cur_p - (std_val * buy_off), 2)
    smart_sell = round(max(smart_buy + prof_t, target_20h), 2)

    # --- VYKDYMAS ---
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA":
            if cur_p <= trade['buy_p']: trade['status'] = "🚀 VYKDOMAS"
            elif cur_p < trade['buy_p'] * 0.98: # Stop loss
                st.session_state.wallet += trade['amount']
                trade['status'] = "🛡️ ATŠAUKTA"
        
        if trade['status'] == "🚀 VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "✅ PELNAS"
            trade['finish_time'] = datetime.now()
            trade['profit_eur'] = profit
            st.session_state.history.append(trade)
            st.balloons()

    # AUTO-RAID logika
    if st.session_state.auto_raid and not any(t['status'] in ["LAUKIA", "🚀 VYKDOMAS"] for t in st.session_state.active_trades):
        if st.session_state.wallet >= 500:
            st.session_state.active_trades.append({"buy_p": smart_buy, "sell_p": smart_sell, "amount": 500.0, "status": "LAUKIA", "time": datetime.now().strftime("%H:%M")})
            st.session_state.wallet -= 500.0
            st.rerun()

    # --- PAGRINDINIS EKRANAS ---
    st.title(f"🚀 Titan Ultimatum V172: {round(st.session_state.wallet, 2)}€")
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    col_b.metric("TRENDAS", "KRINTA 📉" if cur_p < ma100 else "KYLA 📈")
    col_c.metric("20H TIKSLAS", f"{round(target_20h, 2)}€")

    # --- KONTROLĖS SKYDELIS ---
    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🎯 Strateginis Planavimas")
        # Naudojame key, kad kaina NEATŠOKTŲ
        in_buy = st.number_input("Pirkimo kaina (€)", value=smart_buy, key="buy_input")
        in_sell = st.number_input("Pardavimo kaina (€)", value=smart_sell, key="sell_input")
        in_sum = st.number_input("Suma (€)", value=500.0)
    
    with c2:
        st.write("📊 **Tikimybė nupirkti**")
        p_buy = get_probability(cur_p, in_buy, std_val)
        st.title(f"{round(p_buy, 1)}%")
        
        if st.button("🚀 UŽSTATYTI SANDORĮ", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.active_trades.append({"buy_p": in_buy, "sell_p": in_sell, "amount": in_sum, "status": "LAUKIA", "time": datetime.now().strftime("%H:%M")})
                st.session_state.wallet -= in_sum
                st.rerun()

    # --- GRAFIKAI IR ATASKAITOS ---
    st.divider()
    t1, t2, t3 = st.tabs(["📉 Grafikas", "📜 Aktyvūs", "📋 Istorija"])
    
    with t1:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(df['time'].tail(50), df['close'].tail(50), color="#1f77b4", label="Kaina")
        ax.axhline(y=in_buy, color='green', linestyle='--', label="Tavo Pirkimas")
        ax.axhline(y=in_sell, color='red', linestyle='--', label="Tavo Pardavimas")
        ax.set_facecolor('#0E1117')
        fig.patch.set_facecolor('#0E1117')
        plt.legend()
        st.pyplot(fig)
        
    with t2:
        active = [t for t in st.session_state.active_trades if t['status'] in ["LAUKIA", "🚀 VYKDOMAS"]]
        if active: st.table(pd.DataFrame(active))
        else: st.write("Aktyvių operacijų nėra.")

    with t3:
        if st.session_state.history: st.dataframe(pd.DataFrame(st.session_state.history))
