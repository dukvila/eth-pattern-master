import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V148 ZERO LOSS", layout="wide")
st_autorefresh(interval=60000, key="v148_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []
if 'prediction_history' not in st.session_state: st.session_state.prediction_history = []

def play_alert():
    st.components.v1.html('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg"></audio>', height=0)

# 2. Duomenų gavimas (4h istorija)
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-120:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['MA25'] = df['close'].rolling(window=25).mean()
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # --- 20H OPTIMALIOS RIZIKOS PROGNOZĖ ---
    y = df['close'].tail(16).values 
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    
    # Skaičiuojame 80 taškų (20 valandų į priekį)
    future_x = np.arange(len(y), len(y) + 80)
    prediction = slope * future_x + intercept
    
    # --- PROGNOZĖS PATIKIMUMO ANALIZĖ ---
    current_time = df.iloc[-1]['time']
    st.session_state.prediction_history.append({"time": current_time, "pred": prediction[0], "fact": cur_p})
    if len(st.session_state.prediction_history) > 60: st.session_state.prediction_history.pop(0)
    
    pred_df = pd.DataFrame(st.session_state.prediction_history)
    pred_df['error'] = (pred_df['fact'] - pred_df['pred']).abs()
    avg_error = pred_df['error'].mean()
    # Patikimumas: 100% yra idealu, <70% reiškia didelę riziką
    reliability = max(0, 100 - (avg_error / cur_p * 1500))

    st.title(f"🛡️ Zero Loss Evolution: {round(st.session_state.wallet, 2)}€")
    
    # PAGRINDINĖS METRIKOS
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    m2.metric("PROGNOZĖ (20H)", f"{round(prediction[-1], 2)}€")
    m3.metric("PATIKIMUMAS", f"{round(reliability, 1)}%")
    
    # --- OPTIMALI PARDAVIMO KAINA (BE MINUSO) ---
    if st.session_state.active_trade:
        entry = st.session_state.active_trade['buy_p']
        # Tikslas: Pirkimo kaina + 10€ pelno minimumas
        min_sell_to_profit = entry + (10.0 * entry / st.session_state.wallet)
        # Optimalus pardavimas: geriausias iš Prognozės arba Min Pelno
        optimal_sell = max(prediction[-1], min_sell_to_profit)
        m4.metric("OPTIMALUS PARDAVIMAS", f"{round(optimal_sell, 2)}€")
    else:
        m4.metric("LAUKIAMAS ĮĖJIMAS", f"{round(df['MA25'].iloc[-1], 2)}€")

    # GRAFIKAS
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(df['time'].tail(16), df['close'].tail(16), label="4h Istorija", color='blue', linewidth=3)
    future_times = [current_time + timedelta(minutes=15*i) for i in range(1, 81)]
    ax1.plot(future_times, prediction, label="20h Prognozė", color='orange', linestyle='--')
    
    if st.session_state.active_trade:
        ax1.axhline(y=st.session_state.active_trade['buy_p'], color='green', label="Pirkimo Kaina (STOP MINUS)")
        ax1.axhline(y=optimal_sell, color='red', linestyle='--', label="Optimalus Tikslas")

    ax1.legend()
    ax2.plot(pred_df['time'], pred_df['error'], color='red', label="Rinkos Netikėtumai (Klaida)")
    ax2.fill_between(pred_df['time'], pred_df['error'], color='red', alpha=0.1)
    st.pyplot(fig)

    # PREKYBOS LOGIKA
    if st.session_state.active_trade is None:
        if reliability > 75 and prediction[-1] > cur_p + 5:
            st.success(f"✅ SAUGUS ĮĖJIMAS: Patikimumas {round(reliability, 1)}%")
            play_alert()
            if st.button("PIRKTI DABAR"):
                st.session_state.active_trade = {"buy_p": cur_p, "invested": st.session_state.wallet}
                st.session_state.trades_log.insert(0, {"Laikas": datetime.now().strftime("%H:%M"), "Kaina": cur_p, "Tipas": "SAUGUS"})
                st.rerun()

    if st.session_state.active_trade:
        t = st.session_state.active_trade
        current_profit = (t['invested'] / t['buy_p']) * (cur_p - t['buy_p'])
        
        # JOKIO PARDAVIMO Į MINUSĄ
        if cur_p >= optimal_sell:
            if st.button(f"FIKSUOTI PELNĄ: {round(current_profit, 2)}€"):
                st.session_state.wallet += current_profit
                st.session_state.active_trade = None
                st.balloons()
                st.rerun()
        else:
            st.info(f"⏳ LAUKIAMAS TIKSLAS. Dabartinis rezultatas: {round(current_profit, 2)}€ (Reikia: {round(optimal_sell - cur_p, 2)}€ iki pelno)")

    st.table(pd.DataFrame(st.session_state.trades_log).head(5))
