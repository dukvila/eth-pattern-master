import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V147 ORACLE", layout="wide")
st_autorefresh(interval=60000, key="v147_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []
if 'prediction_history' not in st.session_state: st.session_state.prediction_history = []

# --- GARSINIS SIGNALAS ---
def play_alert():
    st.components.v1.html('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg"></audio>', height=0)

# 2. Duomenų gavimas
def get_data():
    try:
        # Imame daugiau duomenų 4h istorijai (15min * 16 = 4h, tad imame 120 taškų atsargai)
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-120:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['MA7'] = df['close'].rolling(window=7).mean()
            df['MA25'] = df['close'].rolling(window=25).mean()
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # --- 20 VALANDŲ PROGNOZĖS MODELIS ---
    y = df['close'].tail(16).values # Analizuojame paskutines 4 valandas
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    
    # Prognozuojame 20 valandų (15min * 80 taškų)
    future_x = np.arange(len(y), len(y) + 80)
    prediction = slope * future_x + intercept
    
    # --- KLAIDOS MATAVIMAS (ATSILIKIMO KREIVĖ) ---
    current_time = df.iloc[-1]['time']
    st.session_state.prediction_history.append({"time": current_time, "pred": prediction[0], "fact": cur_p})
    
    # Saugome tik paskutinius 50 matavimų
    if len(st.session_state.prediction_history) > 50:
        st.session_state.prediction_history.pop(0)
    
    pred_df = pd.DataFrame(st.session_state.prediction_history)
    pred_df['error'] = (pred_df['fact'] - pred_df['pred']).abs()
    avg_error = pred_df['error'].mean()
    # Sėkmės koeficientas (0-100%)
    accuracy = max(0, 100 - (avg_error / cur_p * 1000)) 

    st.title(f"🔮 Oracle V147: {round(st.session_state.wallet, 2)}€")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("ETH Kaina", f"{round(cur_p, 2)}€")
    col2.metric("Sėkmės Tikimybė", f"{round(accuracy, 1)}%", f"{round(slope, 4)} trendas")
    col3.metric("Vidutinė Paklaida", f"{round(avg_error, 2)}€")

    # --- GRAFIKAS: 4H ISTORIJA IR 20H ATEITIS ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # Pagrindinis grafikas
    ax1.plot(df['time'].tail(16), df['close'].tail(16), label="4h Istorija", color='blue', linewidth=3)
    future_times = [current_time + timedelta(minutes=15*i) for i in range(1, 81)]
    ax1.plot(future_times, prediction, label="20h Prognozė", color='orange', linestyle='--')
    ax1.axhline(y=cur_p, color='gray', linestyle=':', alpha=0.5)
    ax1.set_title("Kainos Prognozavimo Radaras")
    ax1.legend()

    # Klaidos/Neteisingumo kreivė (rodo kiek prognozė atsiliko nuo fakto)
    ax2.plot(pred_df['time'], pred_df['error'], color='red', label="Prognozės Paklaida (Klaida)")
    ax2.fill_between(pred_df['time'], pred_df['error'], color='red', alpha=0.1)
    ax2.set_title("Sistemos Mokymosi Kreivė (Mažiau = Geriau)")
    ax2.legend()
    
    st.pyplot(fig)

    # PREKYBOS LOGIKA (Sustiprinta sėkmės koeficientu)
    target_sell = prediction[-1]
    potential_gain = (st.session_state.wallet / cur_p) * (target_sell - cur_p)

    if st.session_state.active_trade is None:
        # Perkam tik jei prognozė rodo >10€ pelno IR sėkmės tikimybė > 75%
        if potential_gain >= 10.0 and accuracy > 75:
            st.success(f"💎 SAUGI PROGA: Pelnas ~{round(potential_gain, 2)}€ (Tikimybė: {round(accuracy, 1)}%)")
            play_alert()
            if st.button("SUDARYTI SANDORĮ"):
                st.session_state.active_trade = {"buy_p": cur_p, "target": target_sell, "invested": st.session_state.wallet}
                st.session_state.trades_log.insert(0, {"Laikas": datetime.now().strftime("%H:%M"), "Sėkmė": f"{round(accuracy, 1)}%", "Tikslas": round(target_sell, 2)})
                st.rerun()

    # Reinvestavimas
    if st.session_state.active_trade:
        t = st.session_state.active_trade
        curr_pelnas = (t['invested'] / t['buy_p']) * (cur_p - t['buy_p'])
        st.warning(f"💼 Įdarbinta {t['invested']}€. Dabartinis rezultatas: {round(curr_pelnas, 2)}€")
        if cur_p >= t['target'] or (curr_pelnas >= 10.0 and accuracy < 50):
            st.session_state.wallet += curr_pelnas
            st.session_state.active_trade = None
            st.balloons()

    st.table(pd.DataFrame(st.session_state.trades_log).head(5))
