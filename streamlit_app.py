import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V105 TRUST-METRIC", layout="wide")
st_autorefresh(interval=60000, key="v105_refresh")

if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"Laimėta": 0, "Viso": 0}

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

def analyze_v105(data):
    if data.empty: return None
    l, p = data.iloc[-1], data.iloc[-2]
    
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
    rsi = 100 - (100 / (1 + (gain / loss))) if loss > 0 else 50
    vol = data['close'].tail(12).std()

    cur_p = l['close']
    score, cmd = 0, "STEBĖTI"
    
    if l['close'] > l['open'] and l['close'] > p['open'] and rsi < 60:
        score, cmd = 3.5, "🟢 PIRKTI"
    elif l['close'] < l['open'] and l['close'] < p['open'] and rsi > 40:
        score, cmd = -3.5, "🔴 PARDUOTI"

    tp = cur_p + (vol * 2.2) if score > 0 else cur_p - (vol * 2.2)
    sl = cur_p - (vol * 1.5) if score > 0 else cur_p + (vol * 1.5)
    
    now_str = datetime.now().strftime("%H:%M")
    
    # Tikriname senus signalus ir atnaujiname statistiką
    for trade in st.session_state.trades_log:
        if trade['Rezultatas'] == "Tikrinama...":
            if (trade['Signal'] == "🟢 PIRKTI" and cur_p >= trade['TP']):
                trade['Rezultatas'] = "✅ LAIMĖTA"
                st.session_state.stats["Laimėta"] += 1
            elif (trade['Signal'] == "🟢 PIRKTI" and cur_p <= trade['SL']):
                trade['Rezultatas'] = "❌ STOP LOSS"
            elif (trade['Signal'] == "🔴 PARDUOTI" and cur_p <= trade['TP']):
                trade['Rezultatas'] = "✅ LAIMĖTA"
                st.session_state.stats["Laimėta"] += 1
            elif (trade['Signal'] == "🔴 PARDUOTI" and cur_p >= trade['SL']):
                trade['Rezultatas'] = "❌ STOP LOSS"

    # Įrašome naują signalą
    if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_str:
        if cmd != "STEBĖTI":
            st.session_state.stats["Viso"] += 1
            st.session_state.trades_log.insert(0, {
                "Laikas": now_str, "Signal": cmd, "Kaina": cur_p, 
                "TP": tp, "SL": sl, "Rezultatas": "Tikrinama..."
            })

    return {"cmd": cmd, "p": cur_p, "rsi": rsi, "tp": tp, "sl": sl, "score": score}

res = analyze_v105(df)

if res:
    # 🏆 SĖKMĖS STATISTIKA
    win_rate = (st.session_state.stats["Laimėta"] / st.session_state.stats["Viso"] * 100) if st.session_state.stats["Viso"] > 0 else 0
    st.markdown(f"""
        <div style="background-color:#1e1e1e; padding:10px; border-radius:10px; text-align:center; border: 1px solid #444; margin-bottom:10px;">
            <span style="color:white; font-size:20px;">📊 Sistemos Patikimumas: </span>
            <span style="color:#00ffcc; font-size:25px; font-weight:bold;">{win_rate:.1f}%</span>
            <span style="color:#888; margin-left:15px;">(Laimėta: {st.session_state.stats['Laimėta']} iš {st.session_state.stats['Viso']})</span>
        </div>
    """, unsafe_allow_html=True)

    color = "#28a745" if "PIRKTI" in res['cmd'] else "#dc3545" if "PARDUOTI" in res['cmd'] else "#343a40"
    st.markdown(f"""
    <div style="background-
