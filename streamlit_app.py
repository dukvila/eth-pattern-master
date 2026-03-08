import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
import base64
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V140 GUARDIAN", layout="wide")
st_autorefresh(interval=60000, key="v140_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []

# --- GARSINIO SIGNALO FUNKCIJA ---
def play_alert():
    # Sukuriamas trumpas pyptelėjimas (Beep)
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

    st.title(f"🛡️ V140 Guardian: {round(st.session_state.wallet, 2)}€")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Kaina", f"{round(cur_p, 2)}€")
    col2.metric("MA 7 (Geltona)", f"{round(ma7, 2)}€")
    col3.metric("MA 25 (Purpurinė)", f"{round(ma25, 2)}€")

    # --- SIGNALO LOGIKA ---
    if cur_p <= ma25 * 1.0005:
        st.error("⚠️ KAINA PASIEKĖ MA 25 (PURPURINĘ) LINIJĄ! RUOŠK REVOLUT X!")
        play_alert() # Paleidžiamas garsas
    elif cur_p <= ma7 * 1.0005:
        st.warning("🔔 Kaina liečia MA 7 (Geltoną) liniją.")

    # Grafikas
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['time'].tail(40), df['close'].tail(40), label="Kaina", color='blue')
    ax.plot(df['time'].tail(40), df['MA7'].tail(40), label="MA 7", color='gold', linestyle='--')
    ax.plot(df['time'].tail(40), df['MA25'].tail(40), label="MA 25", color='purple', linestyle='--')
    ax.legend()
    st.pyplot(fig)

    # PREKYBA
    potential_profit = (st.session_state.wallet / cur_p) * (max_f - cur_p)

    if st.session_state.active_trade is None:
        if potential_profit >= 10.0 and (cur_p <= ma7 or cur_p <= ma25):
            st.success(f"💎 PROGA: {round(potential_profit, 2)}€")
            if st.button("SUDARYTI SANDORĮ"):
                st.session_state.active_trade = {"buy_p": round(cur_p, 2), "target": round(max_f, 2), "invested": st.session_state.wallet}
                st.session_state.trades_log.insert(0, {"Laikas": datetime.now().strftime("%H:%M"), "Veiksmas": "🛒 PIRKTI", "Kaina": round(cur_p, 2), "Tikslas": round(max_f, 2)})
                st.rerun()

    # Reinvestavimas
    if st.session_state.active_trade:
        t = st.session_state.active_trade
        st.info(f"⏳ Laukiama pardavimo ties {t['target']}€")
        if cur_p >= t['target']:
            profit = (t['invested'] / t['buy_p']) * (cur_p - t['buy_p'])
            st.session_state.wallet += profit
            st.session_state.active_trade = None
            st.balloons()

    st.subheader("📜 Žurnalas")
    st.table(pd.DataFrame(st.session_state.trades_log).head(5))
