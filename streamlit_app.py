import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
import math
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V170 TITAN PREDATOR", layout="wide")
st_autorefresh(interval=60000, key="v170_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []
if 'equity_curve' not in st.session_state: st.session_state.equity_curve = [{"time": datetime.now(), "balance": 1711.45}]
if 'auto_raid' not in st.session_state: st.session_state.auto_raid = False

def get_probability(current, target, std):
    if std < 0.01: std = 0.5
    dist = abs(current - target)
    prob = math.exp(-dist / (std * 2)) * 100 
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
    st.sidebar.title("🎮 Predator Control")
    st.session_state.auto_raid = st.sidebar.toggle("🤖 ĮJUNGTI AUTO-RAID", value=st.session_state.auto_raid)
    mode = st.sidebar.select_slider("Rizika", options=["SAUGUS", "SUBALANSUOTAS", "AGRESYVUS"], value="SUBALANSUOTAS")
    
    if mode == "SAUGUS": buy_off, prof_t = 0.9, 1.2
    elif mode == "AGRESYVUS": buy_off, prof_t = 0.1, 5.0
    else: buy_off, prof_t = 0.4, 2.5
    
    smart_buy = round(cur_p - (std_val * buy_off), 2)
    smart_sell = round(max(smart_buy + prof_t, target_20h), 2)

    # --- AUTOMATINIS VYKDYMAS ---
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA":
            if cur_p < trade['buy_p'] * 0.98:
                st.session_state.wallet += trade['amount']
                trade['status'] = "🛡️ STOP"
            elif cur_p <= trade['buy_p']:
                trade['status'] = "🚀 VYKDOMAS"
        if trade['status'] == "🚀 VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "✅ PELNAS"
            trade['finish_time'] = datetime.now()
            trade['profit_eur'] = profit
            st.session_state.history.append(trade)
            st.session_state.equity_curve.append({"time": datetime.now(), "balance": st.session_state.wallet})
            st.balloons()

    # --- AUTO-RAID LOGIKA ---
    # Jei nėra aktyvių sandorių ir Auto-Raid įjungtas - užstatome naują automatiškai
    active_count = len([t for t in st.session_state.active_trades if t['status'] in ["LAUKIA", "🚀 VYKDOMAS"]])
    if st.session_state.auto_raid and active_count == 0 and st.session_state.wallet >= 500:
        st.session_state.active_trades.append({
            "buy_p": smart_buy, "sell_p": smart_sell, "amount": 500.0, 
            "status": "LAUKIA", "time": datetime.now().strftime("%H:%M")
        })
        st.session_state.wallet -= 500.0
        st.toast("🤖 Auto-Raid: Naujas sandoris užstatytas!")
        st.rerun()

    # --- PAGRINDINIS EKRANAS ---
    st.title(f"⚡ Titan Predator V170: {round(st.session_state.wallet, 2)}€")
    
    if st.session_state.auto_raid:
        st.warning("⚠️ AUTO-RAID AKTYVUS: Robotas pats medžioja geriausias kainas.")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    c2.metric("TRENDAS", "KYLA 📈" if cur_p > ma100 else "KRINTA 📉")
    c3.metric("20H TIKSLAS", f"{round(target_20h, 2)}€")

    # --- TRANSPARENT MONITOR ---
    st.divider()
    st.subheader("📑 Aktyvi Medžioklė")
    if active_count > 0:
        for t in st.session_state.active_trades:
            if t['status'] in ["LAUKIA", "🚀 VYKDOMAS"]:
                cols = st.columns(4)
                cols[0].write(f"Pirkimas: **{t['buy_p']}€**")
                cols[1].write(f"Pardavimas: **{t['sell_p']}€**")
                cols[2].info(f"Būsena: {t['status']}")
                if cols[3].button("STOP", key=f"stop_{t['time']}"):
                    st.session_state.wallet += t['amount']
                    t['status'] = "RANKINIS ATŠAUKIMAS"
                    st.rerun()
    else:
        st.write("Laukiama progos...")

    # --- ISTORIJA ---
    if st.session_state.history:
        with st.expander("📜 Paskutinių reidų istorija"):
            st.table(pd.DataFrame(st.session_state.history).tail(5))
