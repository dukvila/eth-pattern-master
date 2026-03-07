import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH DAY-TRADER V90", layout="wide")
st_autorefresh(interval=60000, key="v90_refresh")

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

def analyze_logic(data):
    if data.empty: return 0, "Laukiam...", 0, 50
    l, p = data.iloc[-1], data.iloc[-2]
    body = abs(l['close'] - l['open'])
    u_wick, l_wick = l['high'] - max(l['close'], l['open']), min(l['close'], l['open']) - l['low']
    
    # RSI skaičiavimas patvirtinimui
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean().iloc[-1]
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean().iloc[-1]
    rsi = 100 - (100 / (1 + (gain / loss))) if loss > 0 else 50
    
    score, cmd = 0, "LAUKTI"
    
    # AGRESYVI DAY-TRADING LOGIKA
    if l['close'] > l['open'] and l['close'] > p['open'] and rsi < 65:
        score, cmd = 2.8, "🟢 PIRKTI (Engulfing + RSI)"
    elif l_wick > body * 2 and rsi < 40:
        score, cmd = 2.0, "🟢 PIRKTI (Hammer apmokestintas)"
    elif l['close'] < l['open'] and l['close'] < p['open'] and rsi > 35:
        score, cmd = -2.8, "🔴 PARDUOTI (Bearish Force)"
    elif u_wick > body * 2 and rsi > 60:
        score, cmd = -2.2, "🔴 PARDUOTI (Shooting Star)"

    now_str = datetime.now().strftime("%H:%M")
    if not st.session_state.history or st.session_state.history[0]['Laikas'] != now_str:
        st.session_state.history.insert(0, {"Laikas": now_str, "Veiksmas": cmd, "Kaina": f"{l['close']:.2f}€"})
    
    return score, cmd, l['close'], rsi

if not df.empty:
    score, cmd, cur_p, rsi_v = analyze_logic(df)
    color = "#28a745" if "PIRKTI" in cmd else "#dc3545" if "PARDUOTI" in cmd else "#343a40"
    
    st.markdown(f"""
    <div style="background-color:{color}; padding:30px; border-radius:20px; text-align:center; color:white; border: 5px solid white;">
        <h1 style="margin:0; font-size:50px;">{cmd}</h1>
        <h2 style="margin:10px;">ETH: {cur_p:.2f}€ | RSI: {rsi_v:.1f}</h2>
        <p style="font-size:20px;">Tikimybė: {min(95, abs(score)*30 + (rsi_v if score>0 else 100-rsi_v)/2):.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

    # Grafikas
    l_fut = [df['time'].iloc[-1] + timedelta(minutes=30*i) for i in range(1, 11)]
    p_fut = [cur_p + (score * i * 0.9) for i in range(1, 11)]
    fig, ax = plt.subplots(figsize=(12, 5), facecolor='black')
    ax.set_facecolor('#0a0a0a')
    ax.plot(df['time'].tail(30), df['close'].tail(30), color='white', alpha=0.4)
    ax.plot(l_fut, p_fut, color='#00ffcc', linewidth=6, marker='o')
    ax.axhline(1717.85, color='orange', linestyle='--', alpha=0.4)
    ax.tick_params(colors='white')
    st.pyplot(fig)

    st.markdown("### 📊 Prekybos Žurnalas")
    st.table(pd.DataFrame(st.session_state.history).head(5))
