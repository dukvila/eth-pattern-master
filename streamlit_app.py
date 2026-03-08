import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Stabilumas ir Konfigūracija
st.set_page_config(page_title="V156 TITAN SENTINEL", layout="wide")
st_autorefresh(interval=60000, key="v156_refresh")

# Duomenų bazė sesijoje (išlieka kol veikia debesys)
if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []

# 2. Saugus Duomenų Gavimas (Be klaidų)
def get_crypto_data():
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
    except Exception as e:
        st.error(f"Ryšio klaida: {e}")
        return pd.DataFrame()

df = get_crypto_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    ma100 = df.iloc[-1]['MA100']
    std_val = df.iloc[-1]['STD']
    
    # Tikslioji 20H Prognozė
    y_vals = df['close'].tail(16).values 
    slope, intercept = np.polyfit(np.arange(len(y_vals)), y_vals, 1)
    target_20h = slope * 96 + intercept
    trend_power = slope # Trendo stiprumo indikatorius

    st.title(f"🛡️ Titan Sentinel V156: {round(st.session_state.wallet, 2)}€")
    
    # --- AUTOMATINIS VYKDYMO VARIKLIS ---
    for trade in st.session_state.active_trades:
        # A. Automatinis Pirkimas
        if trade['status'] == "LAUKIA" and cur_p <= trade['buy_p']:
            trade['status'] = "VYKDOMAS"
            st.toast(f"✅ Nupirkta už {trade['buy_p']}€")
            
        # B. Dinaminis Pelno Kėlimas (Tik jei trendas stiprus)
        if trade['status'] == "VYKDOMAS":
            if target_20h > trade['sell_p'] and trend_power > 0.6:
                old_target = trade['sell_p']
                trade['sell_p'] = round(target_20h, 2)
                st.toast(f"📈 Pelno tikslas pakeltas: {old_target} -> {trade['sell_p']}€")

        # C. Automatinis Pardavimas (Tik į PLIUSĄ)
        if trade['status'] == "VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "PELNAS"
            st.session_state.history.append(trade)
            st.balloons()
            st.success(f"💰 Sandoris baigtas! Pelnas: +{round(profit, 2)}€")

    # --- KOMANDINIS SKYDELIS ---
    st.sidebar.header("📊 Biudžeto Valdymas")
    trade_sum = st.sidebar.number_input("Suma vienam sandoriui (€)", value=100.0)
    
    st.subheader("🎯 Strateginis Planavimas")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        req_buy = st.number_input("Pirkimo kaina (€)", value=cur_p - 0.5)
        dist = abs(cur_p - req_buy)
        prob = max(0, min(100, 100 - (dist / std_val * 25)))
        st.write(f"📊 Tikimybė nupirkti: **{round(prob, 1)}%**")

    with c2:
        buy_pct = round(((req_buy - cur_p) / cur_p) * 100, 2)
        st.write(f"Rekomendacija: **{buy_pct}%** nuo dabartinės")
        # Rekomenduojamas pardavimas (min +1% arba prognozė)
        rec_sell = max(req_buy * 1.01, target_20h)
        req_sell = st.number_input("Pardavimo kaina (€)", value=round(rec_sell, 2))

    with c3:
        st.write(f"Trendo jėga: **{'STIPRI 🚀' if trend_power > 0.5 else 'STABILI ⏳'}**")
        if st.button("UŽSTATYTI AUTO-SANDORĮ"):
            if st.session_state.wallet >= trade_sum:
                st.session_state.active_trades.append({
                    "buy_p": req_buy, "sell_p": req_sell, 
                    "amount": trade_sum, "status": "LAUKIA",
                    "time": datetime.now().strftime("%H:%M")
                })
                st.session_state.wallet -= trade_sum
                st.rerun()
            else:
                st.error("Nepakanka pinigų!")

    # --- MONITORINGAS ---
    st.divider()
    active_list = [t for t in st.session_state.active_trades if t['status'] != "PELNAS"]
    if active_list:
        st.subheader("📑 Aktyvios Operacijos")
        st.table(pd.DataFrame(active_list))

    # Grafinis Radaras
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.plot(df['time'].tail(50), df['close'].tail(50), color='#1f77b4', label="ETH Kaina")
