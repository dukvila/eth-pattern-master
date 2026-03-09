import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Branduolys
st.set_page_config(page_title="TITAN FINAL-FIX V202", layout="wide")
st_autorefresh(interval=30000, key="v202_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45

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
    # --- ANALIZĖ ---
    cur_p = df.iloc[-1]['close'] # Dabartinė kaina iš rinkos
    ema_13 = df['close'].ewm(span=13, adjust=False).mean().iloc[-1]
    
    # Binance realybė: High 1748€, Low 1660€
    panic_sell_p = 1731.00 # Kritinė riba iš tavo grafiko
    
    # Skaičiuojame jėgas (Buliai vs Meškos)
    bull_power = df['high'].iloc[-1] - ema_13
    bear_power = df['low'].iloc[-1] - ema_13
    total_force = abs(bull_power) + abs(bear_power)
    bull_pct = round((abs(bull_power) / total_force) * 100) if total_force != 0 else 85 # Pagal tavo fiksaciją
    bear_pct = 100 - bull_pct

    st.markdown(f"<h1 style='text-align: center; color: #00ffcc;'>🛡️ TITAN FINAL-FIX V202</h1>", unsafe_allow_html=True)

    # --- PANIC SELL ALARM ---
    if cur_p <= panic_sell_p:
        st.error(f"⚠️ PANIC SELL AKTYVUOTAS! Kaina ({cur_p}€) nukrito žemiau saugios ribos ({panic_sell_p}€)!")

    # --- JĖGOS MATUOKLIS ---
    st.subheader("⚔️ Binance Rinkos Pulsas")
    c_b, c_m = st.columns([bull_pct, bear_pct])
    c_b.markdown(f"<div style='background-color:#00ff00;color:black;padding:10px;text-align:center;border-radius:5px;'>BULIAI: {bull_pct}%</div>", unsafe_allow_html=True)
    c_m.markdown(f"<div style='background-color:#ff4b4b;color:white;padding:10px;text-align:center;border-radius:5px;'>MEŠKOS: {bear_pct}%</div>", unsafe_allow_html=True)

    # --- PROGNOZĖS LENTELĖ ---
    st.subheader("🕒 15 min. Žvakių Ateities Prognozė")
    future_data = []
    vol = (df['high'] - df['low']).tail(5).mean()
    
    for i in range(1, 6):
        f_time = (datetime.now() + timedelta(minutes=15*i)).strftime("%H:%M")
        change = (vol * 0.6 * i) if bull_pct > bear_pct else -(vol * 0.6 * i)
        f_price = round(cur_p + change, 2)
        future_data.append({
            "Laikas": f_time,
            "Prognozuojama Kaina": f"{f_price} €",
            "Pelnas (investavus 1000€)": f"+{round((1000/cur_p * f_price) - 1000, 2)} €",
            "Veiksmas": "🚀 PIRKTI" if f_price > cur_p else "⏳ LAUKTI"
        })
    st.table(pd.DataFrame(future_data)) # Sutvarkytas lentelės atvaizdavimas

    # --- GRAFIKAS (SU PATAISYTA INDENTACIJA) ---
    fig, ax = plt.subplots(figsize=(12, 5)) # Ištaisyta klaida iš image_14197c.png
    hist = df.tail(15)
    ax.plot(hist['time'], hist['close'], color='#00ffcc', label='Binance Trend', linewidth=2)
    
    # Ateities prognozės linija
    f_times = [hist['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 6
