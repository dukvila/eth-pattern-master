import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V151 INTERNAL INTELLIGENCE", layout="wide")
st_autorefresh(interval=60000, key="v151_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []
if 'prediction_history' not in st.session_state: st.session_state.prediction_history = []

# 2. Duomenų gavimas
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-200:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['MA25'] = df['close'].rolling(window=25).mean()
            df['MA100'] = df['close'].rolling(window=100).mean()
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    ma100 = df.iloc[-1]['MA100']
    
    # --- 20H PROGNOZĖ IR TRENDO ANALIZĖ ---
    y_4h = df['close'].tail(16).values 
    x_4h = np.arange(len(y_4h))
    slope, intercept = np.polyfit(x_4h, y_4h, 1)
    prediction = slope * np.arange(len(y_4h), len(y_4h) + 80) + intercept
    
    # Tikrasis patikimumas vertinant 24h trendo kryptį
    current_time = df.iloc[-1]['time']
    st.session_state.prediction_history.append({"time": current_time, "pred": prediction[0], "fact": cur_p})
    if len(st.session_state.prediction_history) > 60: st.session_state.prediction_history.pop(0)
    
    error_val = (pd.DataFrame(st.session_state.prediction_history)['fact'] - pd.DataFrame(st.session_state.prediction_history)['pred']).abs().mean()
    
    # Jei 24h trendas priešingas 4h prognozei - mažiname patikimumą
    trend_multiplier = 1.0 if (slope > 0 and cur_p > ma100) or (slope < 0 and cur_p < ma100) else 0.4
    reliability = max(0, (100 - (error_val / cur_p * 2500)) * trend_multiplier)

    st.title(f"🧠 Internal Intelligence V151: {round(st.session_state.wallet, 2)}€")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    c2.metric("24H TRENDAS", "KYLANTIS 📈" if cur_p > ma100 else "KRINTANTIS 📉")
    c3.metric("TIKRAS PATIKIMUMAS", f"{round(reliability, 1)}%")
    c4.metric("20H TIKSLAS", f"{round(prediction[-1], 2)}€")

    # GRAFIKAS SU TRENDO ANALIZE
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'].tail(100), df['close'].tail(100), label="24h Istorija", color='lightgray', alpha=0.6)
    ax.plot(df['time'].tail(16), df['close'].tail(16), label="4h Aktyvi zona", color='blue', linewidth=3)
    
    future_times = [current_time + timedelta(minutes=15*i) for i in range(1, 81)]
    ax.plot(future_times, prediction, label="20h Prognozė", color='orange', linestyle='--')
    ax.axhline(y=ma100, color='red', alpha=0.3, label="24h Trendo ašis")
    
    if st.session_state.active_trade:
        ax.axhline(y=st.session_state.active_trade['buy_p'], color='green', linestyle=':', label="Tavo įėjimas")
        
    ax.legend()
    st.pyplot(fig)

    # VALDYMAS
    if st.session_state.active_trade is None:
        if reliability > 85:
            st.success("💎 MATEMATINIS SIGNALAS PATVIRTINTAS. Rinka nuspėjama.")
            if st.button("VYKDYTI MAX SANDORĮ"):
                st.session_state.active_trade = {"buy_p": cur_p, "invested": st.session_state.wallet}
                st.rerun()
        else:
            st.warning(f"⏳ LAUKIAMAS PATVIRTINIMAS. Tikras patikimumas ({round(reliability, 1)}%) per žemas pirkimui.")

    if st.session_state.active_trade:
        t = st.session_state.active_trade
        current_profit = (t['invested'] / t['buy_p']) * (cur_p - t['buy_p'])
        target_price = t['buy_p'] + (10.0 * t['buy_p'] / st.session_state.wallet)
        
        st.info(f"💼 Sandoris aktyvus. Pelnas dabar: {round(current_profit, 2)}€")
        
        # Tikriname, ar galima parduoti pagal tavo "No Loss" principą
        if cur_p >= target_price:
            if st.button(f"FIKSUOTI PELNĄ ({round(current_profit, 2)}€)"):
                st.session_state.wallet += current_profit
                st.session_state.active_trade = None
                st.balloons()
                st.rerun()
        else:
            st.error(f"⚠️ LAUKIAMAS ATŠOKIMAS. Minimalus pelno tikslas: {round(target_price, 2)}€")
