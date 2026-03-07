import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH MASTER V85 + LOG", layout="wide")
st_autorefresh(interval=60000, key="v85_refresh")

# Sesijos saugykla istorijai
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

# --- IŠPLĖSTINIS MODELIŲ ATPAŽINIMAS ---
def analyze_with_log(data):
    if data.empty: return 0, "Laukiam...", 0
    l = data.iloc[-1]
    p = data.iloc[-2]
    body = abs(l['close'] - l['open'])
    u_wick = l['high'] - max(l['close'], l['open'])
    l_wick = min(l['close'], l['open']) - l['low']
    
    score, pattern = 0, "Neutralu"

    if l['close'] > l['open'] and p['close'] < p['open'] and l['close'] > p['open']:
        score, pattern = 2.5, "🔥 BULLISH ENGULFING"
    elif l_wick > body * 2.5 and u_wick < body:
        score, pattern = 1.8, "🔨 HAMMER"
    elif u_wick > body * 2.5 and l_wick < body:
        score, pattern = -2.5, "🌠 SHOOTING STAR"
    elif l['close'] < l['open'] and p['close'] > p['open'] and l['close'] < p['open']:
        score, pattern = -2.2, "📉 BEARISH ENGULFING"
    elif body < (l['high'] - l['low']) * 0.1:
        score, pattern = 0.1, "⚖️ DOJI (Neapibrėžtumas)"
    else:
        mom = l['close'] - p['close']
        score, pattern = (0.5, "Mažas kilimas") if mom > 0 else (-0.5, "Mažas kritimas")

    # Pridedame į istoriją, jei tai naujas signalas
    now_str = datetime.now().strftime("%H:%M")
    if not st.session_state.history or st.session_state.history[0]['Laikas'] != now_str:
        st.session_state.history.insert(0, {
            "Laikas": now_str,
            "Modelis": pattern,
            "Kaina": f"{l['close']:.2f}€",
            "Jėga": f"{abs(score)*40:.0f}%"
        })
    
    return score, pattern, l['close']

if not df.empty:
    score, p_msg, cur_p = analyze_with_log(df)
    
    # UI skydelis
    status_color = "#28a745" if score >= 1.5 else "#dc3545" if score <= -1.5 else "#343a40"
    
    st.markdown(f"""
    <div style="background-color:{status_color}; padding:20px; border-radius:15px; text-align:center; color:white; border: 4px solid white;">
        <h1 style="margin:0;">{p_msg}</h1>
        <h2 style="margin:10px;">ETH: {cur_p:.2f}€</h2>
        <p>Modelio patikimumas: {abs(score)*40:.0f}%</p>
    </div>
    """, unsafe_allow_html=True)

    # Pagrindinis grafikas
    l_fut = [df['time'].iloc[-1] + timedelta(minutes=30*i) for i in range(1, 11)]
    p_fut = [cur_p + (score * i * 0.8) for i in range(1, 11)]

    fig, ax = plt.subplots(figsize=(12, 5), facecolor='black')
    ax.set_facecolor('#0a0a0a')
    ax.plot(df['time'].tail(25), df['close'].tail(
