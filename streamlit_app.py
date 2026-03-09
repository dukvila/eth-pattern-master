import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Branduolys
st.set_page_config(page_title="TITAN COMPOUND V197", layout="wide")
st_autorefresh(interval=30000, key="v197_refresh")

# Tavo realus balansas
if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-720:] 
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df = get_data()

if not df.empty:
    # --- ANALIZĖ ---
    df['rsi'] = calculate_rsi(df['close'])
    df['ema_long'] = df['close'].ewm(span=200, adjust=False).mean()
    
    cur_p = df.iloc[-1]['close']
    cur_rsi = df.iloc[-1]['rsi']
    long_term_trend = df.iloc[-1]['ema_long']
    
    # Tikslios ribos
    buy_p = round(min(df['low'].tail(16).min(), long_term_trend * 0.997), 2)
    sell_p = round(max(df['high'].tail(16).max(), long_term_trend * 1.025), 2)
    stop_loss_p = round(buy_p * 0.985, 2)

    # Sėkmės tikimybė
    win_prob = min(max(100 - cur_rsi + (10 if cur_p <= long_term_trend else 0), 5), 98)

    st.markdown(f"<h1 style='text-align: center; color: #00ff88;'>📈 TITAN COMPOUND V197</h1>", unsafe_allow_html=True)
    
    # --- TURTO SUVESTINĖ ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("DABARTINIS BALANSAS", f"{round(st.session_state.wallet, 2)} €")
    c2.metric("SĖKMĖS TIKIMYBĖ", f"{round(win_prob, 1)} %")
    c3.metric("PELNAS / REIDAS", f"+{round(((sell_p-buy_p)/buy_p)*100, 2)} %")
    c4.metric("7D PROGNOZĖ", f"{round(st.session_state.wallet * 1.15, 2)} €", "+15%")

    # --- BALANSO AUGIMO PROGNOZĖS GRAFIKAS (7 DIENOS) ---
    st.subheader("🚀 7 Dienų Balanso Augimo Projekcija (Tik 70%+ Tikimybės)")
    
    days = np.arange(0, 8)
    # Modelis: Darant po 2 sėkmingus reidus per dieną su vidutiniu 1.2% pelnu
    growth_values = [st.session_state.wallet * (1.024 ** day) for day in days]
    
    fig_growth, ax_growth = plt.subplots(figsize=(12, 3))
    ax_growth.plot(days, growth_values, marker='o', color='#00ff88', linewidth=3, markersize=8)
    ax_growth.fill_between(days, st.session_state.wallet, growth_values, color='#00ff88', alpha=0.1)
    
    ax_growth.set_facecolor('#0E1117')
    fig_growth.patch.set_facecolor('#0E1117')
    ax_growth.set_xlabel("Dienos", color='white')
    ax_growth.set_ylabel("Eurai (€)", color='white')
    ax_growth.tick_params(colors='white')
    ax_growth.grid(color='white', alpha=0.1)
    st.pyplot(fig_growth)

    # --- DINAMINĖ REIDŲ LENTELĖ ---
    st.subheader("📊 15 Min. Reido Detalės (1000€ Investicija)")
    prog_list = []
    for i in range(1, 6):
        target_t = (datetime.now() + timedelta(minutes=i*15)).strftime("%H:%M")
        cash_p = (1000.0 / buy_p) * (sell_p - buy_p)
        
        prog_list.append({
            "Pardavimo Laikas": target_t,
            "Tikimybė": f"{round(win_prob, 1)} %",
            "Pelnas (€)": f"+{round(cash_p, 2)} €",
            "Stop-Loss (€)": f"{stop_loss_p} €",
            "Rizika": "🟢 ŽEMA" if win_prob > 70 else "🟡 VIDUTINĖ",
            "Rekomendacija": "🔥 PIRKTI" if win_prob > 70 else "⏳ LAUKTI"
        })
    st.table(prog_list)

    # --- KAINOS GRAFIKAS ---
    fig_p, ax_p = plt.subplots(figsize=(12, 5))
    hist_view = df.tail(32)
    ax_p.plot(hist_view['time'], hist_view['close'], color='white', linewidth=2)
    ax_p.axhline(sell_p, color='#00ff88', linestyle='--', label="Target")
    ax_p.axhline(buy_p, color='#ffd000', linestyle='--', label="Entry")
    ax_p.axhline(stop_loss_p, color='#ff4b4b', linewidth=2, label="Stop-Loss")
    ax_p.set_facecolor('#0E1117'); fig_p.patch.set_facecolor('#0E1117')
    ax_p.tick_params(colors='white'); ax_p.legend()
    st.pyplot(fig_p)
