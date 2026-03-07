import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="ETH PRO-TRADER V95", layout="wide")
st_autorefresh(interval=60000, key="v95_refresh")

if 'history' not in st.session_state:
    st.session_state.history = []

def get_live_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            if 'result' in res:
                d = res['result']['XETHZEUR'][-160:]
                df = pd.DataFrame(d, columns=['time','open','high','low','close','vwap','vol','count']).astype(float)
                df['time'] = pd.to_datetime(df['time'], unit='s') + timedelta(hours=2)
                return df
    except: return pd.DataFrame()

df = get_live_data()

def analyze_pro_logic(data):
    if data.empty: return None
    l, p = data.iloc[-1], data.iloc[-2]
    
    # Indikatoriai tikslumui
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean().iloc[-1]
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean().iloc[-1]
    rsi = 100 - (100 / (1 + (gain / loss))) if loss > 0 else 50
    volatility = data['close'].tail(10).std()

    cur_p = l['close']
    score, cmd = 0, "LAUKTI"
    
    # 1. PIRKIMO LOGIKA
    if l['close'] > l['open'] and l['close'] > p['open'] and rsi < 60:
        score, cmd = 3.0, "🟢 PIRKTI"
    # 2. PARDAVIMO LOGIKA
    elif l['close'] < l['open'] and l['close'] < p['open'] and rsi > 40:
        score, cmd = -3.0, "🔴 PARDUOTI"

    # STRATEGIJOS APSKAIČIAVIMAS (Tavo prašyti skaičiai)
    tp1 = cur_p + (volatility * 1.5)  # Pirmas pelnas (Saugus)
    tp2 = cur_p + (volatility * 3.0)  # Antras pelnas (Agresyvus)
    sl = cur_p - (volatility * 2.0)   # Stop Loss (Rizikos riba)
    
    risk_level = "Aukšta" if volatility > 5 else "Vidutinė" if volatility > 2 else "Žema"
    win_rate = min(95.0, abs(score)*25 + (rsi if score > 0 else 100-rsi)/2)

    return {
        "cmd": cmd, "price": cur_p, "rsi": rsi, "tp1": tp1, "tp2": tp2, 
        "sl": sl, "risk": risk_level, "win": win_rate, "score": score
    }

res = analyze_pro_logic(df)

if res:
    color = "#28a745" if "PIRKTI" in res['cmd'] else "#dc3545" if "PARDUOTI" in res['cmd'] else "#343a40"
    
    st.markdown(f"""
    <div style="background-color:{color}; padding:25px; border-radius:15px; color:white; border: 5px solid white;">
        <h1 style="text-align:center; margin:0;">{res['cmd']} | {res['price']:.2f}€</h1>
        <div style="display:flex; justify-content:space-around; margin-top:20px; font-weight:bold; background:rgba(0,0,0,0.2); padding:15px; border-radius:10px;">
            <div style="text-align:center;">🎯 TARGET 1 (Pelnas 1)<br><span style="font-size:24px;">{res['tp1']:.2f}€</span></div>
            <div style="text-align:center;">🚀 TARGET 2 (Pelnas 2)<br><span style="font-size:24px;">{res['tp2']:.2f}€</span></div>
            <div style="text-align:center;">🛡️ STOP LOSS (Rizika)<br><span style="font-size:24px;">{res['sl']:.2f}€</span></div>
        </div>
        <p style="text-align:center; margin-top:15px; font-size:18px;">
            Tikimybė: {res['win']:.1f}% | Rizika: {res['risk']} | RSI: {res['rsi']:.1f}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Grafikas su vizualiomis pelno linijomis
    fig, ax = plt.subplots(figsize=(12, 5), facecolor='black')
    ax.set_facecolor('#0a0a0a')
    ax.plot(df['time'].tail(30), df['close'].tail(30), color='white', alpha=0.5)
    
    # Vizualios prekybos zonos
    ax.axhline(res['tp1'], color='#00ffcc', linestyle='--', label="TP1")
    ax.axhline(res['tp2'], color='#28a745', linestyle='--', label="TP2")
    ax.axhline(res['sl'], color='#ff4b4b', linestyle=':', label="SL")
    
    ax.tick_params(colors='white')
    st.pyplot(fig)
