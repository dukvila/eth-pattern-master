import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V146 IMPULSE HUNTER", layout="wide")
st_autorefresh(interval=60000, key="v146_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []

# --- GARSINIS SIGNALAS ---
def play_alert():
    st.components.v1.html('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg"></audio>', height=0)

# --- INDIKATORIŲ SKAIČIAVIMAS ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1  + rs))

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
            df['RSI'] = calculate_rsi(df['close'])
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    ma7 = df.iloc[-1]['MA7']
    ma25 = df.iloc[-1]['MA25']
    rsi_now = df.iloc[-1]['RSI']
    vol_now = df.iloc[-1]['vol']
    vol_avg = df['vol'].tail(20).mean()

    # --- BREAKOUT STRENGTH ANALIZĖ ---
    # Jėga matuojama pagal RSI ir Apimtis (Volume)
    strength_score = 0
    if rsi_now > 50: strength_score += 40
    if vol_now > vol_avg: strength_score += 40
    if cur_p > ma7: strength_score += 20
    
    # Tikslų skaičiavimas
    min_gain_needed = (10.0 * cur_p) / st.session_state.wallet
    target_buy = cur_p if cur_p <= ma7 else ma7
    
    # Jei jėga didelė (>70), keliam pardavimo tikslą agresyviau
    bonus_multiplier = 1.5 if strength_score >= 80 else 1.1
    target_sell = target_buy + (min_gain_needed * bonus_multiplier) + 5

    st.title(f"⚡ Impulse Hunter: {round(st.session_state.wallet, 2)}€")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH Kaina", f"{round(cur_p, 2)}€")
    c2.metric("Proveržio Jėga", f"{int(strength_score)}%", "STIPRUS" if strength_score >= 70 else "SILPNAS")
    c3.metric("RSI (Momentas)", f"{round(rsi_now, 1)}")
    c4.metric("Pardavimo Tikslas", f"{round(target_sell, 2)}€")

    # Grafikas
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(df['time'].tail(40), df['close'].tail(40), label="Kaina", color='#1f77b4', linewidth=2)
    ax1.plot(df['time'].tail(40), df['MA7'].tail(40), label="MA 7", color='gold', linestyle='--')
    ax1.plot(df['time'].tail(40), df['MA25'].tail(40), label="MA 25", color='purple', linewidth=2)
    ax1.axhline(y=target_sell, color='orange', linestyle=':', label="Dinaminis tikslas")
    ax1.legend(loc='upper left')
    
    # RSI Grafikas
    ax2.plot(df['time'].tail(40), df['RSI'].tail(40), color='gray')
    ax2.axhline(y=70, color='red', linestyle='--', alpha=0.3)
    ax2.axhline(y=30, color='green', linestyle='--', alpha=0.3)
    ax2.fill_between(df['time'].tail(40), 30, 70, color='gray', alpha=0.1)
    ax2.set_ylabel("RSI")
    st.pyplot(fig)

    # PREKYBA
    if st.session_state.active_trade is None:
        # Pirkimo sąlyga: Jėga auga IR kaina prie MA7 arba MA25
        if strength_score >= 60 and cur_p <= ma7 * 1.002:
            st.error(f"🚀 IMPULSO PRADŽIA! Jėga: {strength_score}%. Tikslas: {round(target_sell, 2)}€")
            play_alert()
            if st.button(f"VYKDYTI MAX SANDORĮ"):
                st.session_state.active_trade = {"buy_p": round(cur_p, 2), "target": round(target_sell, 2), "invested": st.session_state.wallet}
                st.session_state.trades_log.insert(0, {"Laikas": datetime.now().strftime("%H:%M"), "Jėga": f"{int(strength_score)}%", "Kaina": round(cur_p, 2), "Tikslas": round(target_sell, 2)})
                st.rerun()

    # PARDAVIMAS
    if st.session_state.active_trade:
        t = st.session_state.active_trade
        current_gain = (t['invested'] / t['buy_p']) * (cur_p - t['buy_p'])
        st.warning(f"💼 Sandoris aktyvus. Pelnas: {round(current_gain, 2)}€")
        
        # Dinaminis išėjimas: parduodame jei pasiektas tikslas ARBA jei jėga krenta virš 10€ pelno
        if cur_p >= t['target'] or (current_gain >= 10.0 and strength_score < 40):
            st.session_state.wallet += current_gain
            st.session_state.active_trade = None
            st.balloons()
            st.success(f"✅ PELNAS FIKSUOTAS: {round(current_gain, 2)}€")

    st.table(pd.DataFrame(st.session_state.trades_log).head(5))
