import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V149 STRATEGIC ALIGNMENT", layout="wide")
st_autorefresh(interval=60000, key="v149_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []
if 'prediction_history' not in st.session_state: st.session_state.prediction_history = []

# 2. Duomenų gavimas (imame 200 taškų, kad užtektų 24h analizei)
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-200:] # Daugiau duomenų gilesnei analizei
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['MA25'] = df['close'].rolling(window=25).mean()
            df['MA100'] = df['close'].rolling(window=100).mean() # 25 valandų vidurkis
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    ma100 = df.iloc[-1]['MA100'] # 24-25 valandų trendo linija
    
    # --- 24H TRENDO ANALIZĖ ---
    # Jei kaina virš MA100 - dienos trendas kyla. Jei žemiau - krenta.
    day_trend = "KYLANTIS 📈" if cur_p > ma100 else "KRINTANTIS 📉"
    trend_color = "green" if cur_p > ma100 else "red"
    
    # --- 20H PROGNOZĖ (iš 4h istorijos) ---
    y_4h = df['close'].tail(16).values 
    x_4h = np.arange(len(y_4h))
    slope, intercept = np.polyfit(x_4h, y_4h, 1)
    prediction = slope * np.arange(len(y_4h), len(y_4h) + 80) + intercept
    
    # --- PATIKIMUMO SKAIČIAVIMAS ---
    current_time = df.iloc[-1]['time']
    st.session_state.prediction_history.append({"time": current_time, "pred": prediction[0], "fact": cur_p})
    if len(st.session_state.prediction_history) > 60: st.session_state.prediction_history.pop(0)
    pred_df = pd.DataFrame(st.session_state.prediction_history)
    pred_df['error'] = (pred_df['fact'] - pred_df['pred']).abs()
    reliability = max(0, 100 - (pred_df['error'].mean() / cur_p * 1500))

    st.title(f"🛡️ Oracle V149: {round(st.session_state.wallet, 2)}€")
    
    # METRIKŲ SKYDELIS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    c2.markdown(f"**DIENOS TRENDAS (24H):** <span style='color:{trend_color}'>{day_trend}</span>", unsafe_allow_html=True)
    c3.metric("PATIKIMUMAS", f"{round(reliability, 1)}%")
    c4.metric("20H TIKSLAS", f"{round(prediction[-1], 2)}€")

    # GRAFIKAS
    fig, ax = plt.subplots(figsize=(12, 5))
    # 24h Istorija (pilka)
    ax.plot(df['time'].tail(96), df['close'].tail(96), label="24h Istorija", color='lightgray', alpha=0.5)
    # 4h Istorija (mėlyna)
    ax.plot(df['time'].tail(16), df['close'].tail(16), label="4h Aktyvi zona", color='blue', linewidth=3)
    # 20h Prognozė (oranžinė)
    future_times = [current_time + timedelta(minutes=15*i) for i in range(1, 81)]
    ax.plot(future_times, prediction, label="20h Prognozė", color='orange', linestyle='--')
    # 24h Trendo linija
    ax.plot(df['time'].tail(96), df['MA100'].tail(96), label="24h Trendo ašis (MA100)", color='red', alpha=0.3)
    
    ax.legend()
    st.pyplot(fig)

    # PREKYBOS LOGIKA
    if st.session_state.active_trade is None:
        # Perkam tik jei 20h prognozė sutampa su dienos trendu arba yra stiprus atšokimas
        if reliability > 75 and (cur_p > ma100 or slope > 0):
            st.success("✅ STRATEGINIS SUTAPIMAS: Pirkimo momentas palankus.")
            if st.button("VYKDYTI PIRKIMĄ"):
                st.session_state.active_trade = {"buy_p": cur_p, "invested": st.session_state.wallet}
                st.rerun()

    if st.session_state.active_trade:
        t = st.session_state.active_trade
        profit = (t['invested'] / t['buy_p']) * (cur_p - t['buy_p'])
        target = t['buy_p'] + (10.0 * t['buy_p'] / st.session_state.wallet)
        
        st.info(f"💼 Įdarbinta: {t['invested']}€. Tikslas: >{round(target, 2)}€ (Pelnas dabar: {round(profit, 2)}€)")
        if cur_p >= target and cur_p >= prediction[-1]:
            if st.button("FIKSUOTI MAX PELNĄ"):
                st.session_state.wallet += profit
                st.session_state.active_trade = None
                st.balloons()
                st.rerun()
