import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija ir Stabilumas
st.set_page_config(page_title="V152 SUPREME SENTINEL", layout="wide")
st_autorefresh(interval=60000, key="v152_final")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []
if 'prediction_history' not in st.session_state: st.session_state.prediction_history = []

def play_alert():
    st.components.v1.html('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg"></audio>', height=0)

# 2. Duomenų gavimas be klaidų
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-200:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['MA7'] = df['close'].rolling(window=7).mean()
            df['MA25'] = df['close'].rolling(window=25).mean()
            df['MA100'] = df['close'].rolling(window=100).mean() # Dienos trendo ašis
            return df
    except Exception as e:
        st.error(f"Duomenų klaida: {e}")
        return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    ma100 = df.iloc[-1]['MA100']
    
    # --- PROGNOZĖS SKAIČIAVIMAS ---
    y_4h = df['close'].tail(16).values 
    x_4h = np.arange(len(y_4h))
    slope, intercept = np.polyfit(x_4h, y_4h, 1)
    prediction = slope * np.arange(len(y_4h), len(y_4h) + 80) + intercept
    
    # --- PATIKIMUMO FILTRAS ---
    current_time = df.iloc[-1]['time']
    st.session_state.prediction_history.append({"time": current_time, "pred": prediction[0], "fact": cur_p})
    if len(st.session_state.prediction_history) > 60: st.session_state.prediction_history.pop(0)
    
    error_df = pd.DataFrame(st.session_state.prediction_history)
    avg_err = (error_df['fact'] - error_df['pred']).abs().mean()
    
    # Tikrasis patikimumas: Baudžiame, jei 4h kryptis priešinga 24h trendui
    trend_aligned = (slope > 0 and cur_p > ma100)
    reliability = max(0, (100 - (avg_err / cur_p * 2500)))
    if not trend_aligned: reliability *= 0.5 # Mažiname pasitikėjimą perpus, jei trendas krenta

    # --- VAIZDUOJAMASIS SKYDELIS ---
    st.title(f"🛡️ Supreme Sentinel V152: {round(st.session_state.wallet, 2)}€")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    trend_txt = "KYLANTIS 📈" if cur_p > ma100 else "KRINTANTIS 📉"
    c2.metric("DIENOS TRENDAS (24H)", trend_txt, delta=round(cur_p - ma100, 2))
    c3.metric("TIKRAS PATIKIMUMAS", f"{round(reliability, 1)}%")
    c4.metric("20H TIKSLAS", f"{round(prediction[-1], 2)}€")

    # 3. Grafikas be "SyntaxError"
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # Pagrindinis grafikas
    ax1.plot(df['time'].tail(100), df['close'].tail(100), label="24h Istorija", color='lightgray', alpha=0.5)
    ax1.plot(df['time'].tail(16), df['close'].tail(16), label="4h Aktyvi zona", color='blue', linewidth=2)
    
    future_times = [current_time + timedelta(minutes=15*i) for i in range(1, 81)]
    ax1.plot(future_times, prediction, label="20h Prognozė", color='orange', linestyle='--')
    ax1.axhline(y=ma100, color='red', alpha=0.3, label="Dienos ašis (MA100)")
    ax1.legend()
    
    # Klaidos grafikas (Mokymosi kreivė)
    ax2.plot(error_df['time'], (error_df['fact'] - error_df['pred']).abs(), color='red')
    ax2.set_title("Sistemos Paklaida (Kuo žemiau, tuo tiksliau)")
    
    st.pyplot(fig)

    # 4. Griežta Prekybos Logika
    if st.session_state.active_trade is None:
        if cur_p > ma100 and reliability > 80:
            st.success("💎 SAUGUS SIGNALAS: Trendas ir Prognozė sutampa.")
            if st.button("INVESTUOTI MAX"):
                st.session_state.active_trade = {"buy_p": cur_p, "invested": st.session_state.wallet}
                st.rerun()
        else:
            st.warning("⚠️ BLOKUOJAMA: Dienos trendas krenta arba patikimumas per mažas.")

    if st.session_state.active_trade:
        t = st.session_state.active_trade
        profit = (t['invested'] / t['buy_p']) * (cur_p - t['buy_p'])
        target = t['buy_p'] + (10.0 * t['buy_p'] / st.session_state.wallet)
        
        st.info(f"💼 Sandoris: {t['invested']}€. Dabartinis rezultatas: {round(profit, 2)}€")
        
        # Tikriname "No Loss" taisyklę
        if cur_p >= target:
            if st.button(f"FIKSUOTI PELNĄ ({round(profit, 2)}€)"):
                st.session_state.wallet += profit
                st.session_state.active_trade = None
                st.balloons()
                st.rerun()
        else:
            st.error(f"Laukiamas atšokimas iki {round(target, 2)}€ (Neprekiaujame į minusą!)")

    st.table(pd.DataFrame(st.session_state.trades_log).head(5))
