import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Branduolys
st.set_page_config(page_title="TITAN SENTINEL V199", layout="wide")
st_autorefresh(interval=30000, key="v199_refresh")

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
    # --- BULIŲ / MEŠKŲ JĖGOS SKAIČIAVIMAS ---
    cur_p = df.iloc[-1]['close']
    ema_13 = df['close'].ewm(span=13, adjust=False).mean().iloc[-1]
    
    bull_power = df['high'].iloc[-1] - ema_13
    bear_power = df['low'].iloc[-1] - ema_13
    
    # Normalizuojame jėgą (0-100%)
    total_force = abs(bull_power) + abs(bear_power)
    bull_pct = round((abs(bull_power) / total_force) * 100) if total_force != 0 else 50
    bear_pct = 100 - bull_pct

    st.markdown(f"<h1 style='text-align: center; color: #00ffcc;'>🛡️ TITAN SENTINEL V199</h1>", unsafe_allow_html=True)

    # --- JĖGOS MATUOKLIS (VIZUALUS) ---
    st.subheader("⚔️ Rinkos Jėgų Pusiausvyra (Kas 15 min.)")
    col_bull, col_bear = st.columns([bull_pct, bear_pct])
    col_bull.markdown(f"<div style='background-color: #00ff00; text-align: center; padding: 10px; border-radius: 5px 0 0 5px; color: black;'><b>BULIAI: {bull_pct}%</b></div>", unsafe_allow_html=True)
    col_bear.markdown(f"<div style='background-color: #ff4b4b; text-align: center; padding: 10px; border-radius: 0 5px 5px 0; color: white;'><b>MEŠKOS: {bear_pct}%</b></div>", unsafe_allow_html=True)

    # --- DINAMINĖ PROGNOZĖ PAGAL JĖGĄ ---
    trend_dir = "KILIMAS" if bull_pct > bear_pct else "KRITIMAS"
    trend_col = "#00ff00" if trend_dir == "KILIMAS" else "#ff4b4b"
    
    st.markdown(f"<h3 style='text-align: center;'>Dabartinė kryptis: <span style='color: {trend_col};'>{trend_dir}</span></h3>", unsafe_allow_html=True)

    # --- ATEITIES LENTELĖ SU KRYPTIES KEITIMU ---
    st.subheader("🕒 Tikslus laikas ir prognozuojama kaina")
    future_data = []
    volatility = (df['high'] - df['low']).tail(5).mean()
    
    for i in range(1, 6):
        f_time = (datetime.now() + timedelta(minutes=15*i)).strftime("%H:%M")
        # Jei meškos stipresnės, kaina prognozuojama žemyn
        price_change = (volatility * 0.4 * i) if bull_pct > bear_pct else -(volatility * 0.4 * i)
        f_price = round(cur_p + price_change, 2)
        
        future_data.append({
            "Laikas": f_time,
            "Prognozuojama Kaina (€)": f"{f_price} €",
            "Kryptis": "📈 Kyla" if bull_pct > bear_pct else "📉 Krenta",
            "Tikimybė": f"{max(bull_pct, bear_pct)} %",
            "Pelnas (€) iš 1000€": f"{round((1000/cur_p * f_price) - 1000, 2)} €"
        })
    st.table(future_data)

    # --- GRAFIKAS ---
    fig, ax = plt.subplots(figsize=(12, 4))
    hist_view = df.tail(10)
    ax.plot(hist_view['time'], hist_view['close'], color='white', label='Istorija')
    
    # Ateities prognozės linija (keičia kryptį!)
    f_times = [hist_view['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 6)]
    f_vals = [cur_p + ((volatility * 0.4 * i) if bull_pct > bear_pct else -(volatility * 0.4 * i)) for i in range(1, 6)]
    ax.plot(f_times, f_vals, color=trend_col, linestyle='--', marker='o', label=f'Prognozuojamas {trend_dir}')

    ax.set_facecolor('#0E1117'); fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white'); plt.legend()
    st.pyplot(fig)
