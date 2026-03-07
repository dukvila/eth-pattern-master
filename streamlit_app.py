import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V100 VALIDATOR", layout="wide")
st_autorefresh(interval=60000, key="v100_refresh")

if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []

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

def analyze_v100(data):
    if data.empty: return None
    l, p = data.iloc[-1], data.iloc[-2]
    
    # Indikatoriai
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean().iloc[-1]
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean().iloc[-1]
    rsi = 100 - (100 / (1 + (gain / loss))) if loss > 0 else 50
    vol = data['close'].tail(8).std()

    cur_p = l['close']
    score, cmd = 0, "STEBĖTI"
    
    # Griežta logika
    if l['close'] > l['open'] and l['close'] > p['open'] and rsi < 65:
        score, cmd = 3.2, "🟢 PIRKTI"
    elif l['close'] < l['open'] and l['close'] < p['open'] and rsi > 35:
        score, cmd = -3.2, "🔴 PARDUOTI"

    # Tikslai ir rizika
    tp = cur_p + (vol * 2.5) if score > 0 else cur_p - (vol * 2.5)
    sl = cur_p - (vol * 1.8) if score > 0 else cur_p + (vol * 1.8)
    
    # Validacijos įrašas
    now = datetime.now()
    if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now.strftime("%H:%M"):
        st.session_state.trades_log.insert(0, {
            "Laikas": now.strftime("%H:%M"),
            "Signal": cmd,
            "Kaina": cur_p,
            "Rezultatas": "Tikrinama..."
        })

    return {"cmd": cmd, "p": cur_p, "rsi": rsi, "tp": tp, "sl": sl, "score": score, "vol": vol}

res = analyze_v100(df)

if res:
    # Vizualinis skydas
    color = "#28a745" if "PIRKTI" in res['cmd'] else "#dc3545" if "PARDUOTI" in res['cmd'] else "#f39c12"
    st.markdown(f"""
    <div style="background-color:{color}; padding:20px; border-radius:15px; color:white; text-align:center; border: 4px solid white;">
        <h1 style="margin:0;">{res['cmd']} | {res['p']:.2f}€</h1>
        <p style="font-size:20px;">Target: {res['tp']:.2f}€ | Stop Loss: {res['sl']:.2f}€ | RSI: {res['rsi']:.1f}</p>
    </div>
    """, unsafe_allow_html=True)

    # GRAFIKAS: 2 valandų istorija + paros prognozė
    fig, ax = plt.subplots(figsize=(12, 5), facecolor='black')
    ax
