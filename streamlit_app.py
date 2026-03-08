import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
import math
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V171 COMMAND CENTER", layout="wide")
st_autorefresh(interval=60000, key="v171_refresh")

# Sesijos atmintis
if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []
if 'equity_curve' not in st.session_state: st.session_state.equity_curve = [{"time": datetime.now(), "balance": 1711.45}]
if 'auto_raid' not in st.session_state: st.session_state.auto_raid = False

# Patikslinta tikimybių matematika (V169 Precision)
def get_probability(current, target, std):
    if std < 0.01: std = 0.5
    dist = abs(current - target)
    prob = math.exp(-dist / (std * 2.5)) * 100 
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
    
    # 20h Prognozė ir Trendo jėga
    y_vals = df['close'].tail(16).values 
    slope, intercept = np.polyfit(np.arange(len(y_vals)), y_vals, 1)
    target_20h = slope * 80 + intercept
    trend_power = "STIPRUS 🚀" if abs(slope) > 0.5 else "STABILUS ⚖️"

    # --- ŠONINIS VALDYMAS ---
    st.sidebar.title("🎮 Nustatymai")
    st.session_state.auto_raid = st.sidebar.toggle("🤖 AUTO-RAID", value=st.session_state.auto_raid)
    mode = st.sidebar.select_slider("Rizika", options=["SAUGUS", "SUBALANSUOTAS", "AGRESYVUS"], value="SUBALANSUOTAS")
    
    if mode == "SAUGUS": buy_off, prof_t = 0.8, 1.2
    elif mode == "AGRESYVUS": buy_off, prof_t = 0.2, 5.0
    else: buy_off, prof_t = 0.5, 2.5
    
    smart_buy = round(cur_p - (std_val * buy_off), 2)
    smart_sell = round(max(smart_buy + prof_t, target_20h), 2)

    # --- VYKDYMO LOGIKA ---
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA":
            if cur_p < trade['buy_p'] * 0.98: # Stop-Loss
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
