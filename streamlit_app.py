import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V141 VISUAL GUARDIAN", layout="wide")
st_autorefresh(interval=60000, key="v141_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []

# --- GARSINIS SIGNALAS ---
def play_alert():
    audio_html = """
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# 2. Duomenų gavimas
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['MA7'] = df['close'].rolling(window=7).mean()
            df['MA25'] = df['close'].rolling(window=25).mean()
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    ma7 = df.iloc[-1]['MA7']
    ma25 = df.iloc[-1]['MA25']
    
    # 20h Prognozė
    y = df['close'].tail(20).values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    future_prices = slope * np.arange(len(y), len(y) + 80) + intercept
    max_f = np.max(future_prices)

    st.title(f"🛡️ V141 Visual Guardian: {round(st.session_state.wallet, 2)}€")
    
    # Indikatoriai
    c1, c2, c3 = st.columns(3)
    c1.metric("ETH Kaina", f"{round(cur_p, 2)}€")
    c2.metric("Palaikymas (MA25)", f"{round(ma25, 2)}€")
    
    # --- VIZUALUS IR GARSINIS PERSPĖJIMAS ---
    trigger_zone = ma25 * 1.001 # 0.1% virš MA25
    if cur_p <= trigger_zone:
        st.error(f"🚨 ALERT: KAINA LIEČIA MA25 ({round(ma25, 2)}€)! PIRK REVOLUTE!")
        play_alert()
        c3.error("PIRKIMO SIGNALAS!")
    else:
        c3.success("SAUGI ZONA")

    # GRAFIKAS SU VIZUALIA „PAVOJAUS ZONA“
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'].tail(40), df['close'].tail(40), label="Kaina", color='#1f77b4', linewidth=2)
    ax.plot(df['time'].tail(40), df['MA7'].tail(40), label="MA 7 (Greita)", color='gold', linestyle='--')
    ax.plot(df['time'].tail(40), df['MA25'].tail(40), label="MA 25 (Siena)", color='purple', linewidth=2)
    
    # Raudona zona (Pirkimo sritis)
    ax.fill_between(df['time'].tail(40), ma25*0.995, ma25*1.001, color='red', alpha=0.2, label="PIRKIMO ZONA")
    
    ax.legend()
    st.pyplot(fig)

    # 3. Prekybos logika
    potential_profit = (st.session_state.wallet / cur_p) * (max_f - cur_p)

    if st.session_state.active_trade is None:
        if potential_profit >= 10.0 and cur_p <= trigger_zone:
            if st.button(f"SUDARYTI SANDORĮ UŽ {round(st.session_state.wallet, 2)}€"):
                st.session_state.active_trade = {"buy_p": round(cur_p, 2), "target": round(max_f, 2), "invested": st.session_state.wallet}
                st.session_state.trades_log.insert(0, {"Laikas": datetime.now().strftime("%H:%M"), "Veiksmas": "🛒 PIRKTI", "Kaina": round(cur_p, 2), "Tikslas": round(max_f, 2)})
                st.rerun()
    
    # Aktyvaus sandorio valdymas
    if st.session_state.active_trade:
        t = st.session_state.active_trade
        st.warning(f"⏳ ĮDARBINTA: {t['invested']}€. Laukiama kainos: {t['target']}€")
        if cur_p >= t['target']:
            profit = (t['invested'] / t['buy_p']) * (cur_p - t['buy_p'])
            st.session_state.wallet += profit
            st.session_state.active_trade = None
            st.balloons()

    st.subheader("📜 Pinigų augimo istorija")
    st.table(pd.DataFrame(st.session_state.trades_log).head(5))
