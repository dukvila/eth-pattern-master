import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Pagrindinė konfigūracija
st.set_page_config(page_title="V145 MAX SCALPER", layout="wide")
st_autorefresh(interval=60000, key="v145_refresh")

# Piniginės sekimas - pradedam nuo 1700€ arba tiek, kiek jau uždirbai
if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []

# --- GARSINIS SIGNALAS ---
def play_alert():
    st.components.v1.html('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg"></audio>', height=0)

# 2. Realaus laiko duomenys
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
    except Exception as e:
        return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    ma7 = df.iloc[-1]['MA7']
    ma25 = df.iloc[-1]['MA25']
    
    # --- AGRESYVI MAX PELNO LOGIKA ---
    # Skaičiuojame, kokio kainos šuolio reikia, kad gautume bent 10€ pelno
    min_jump_needed = (10.0 * cur_p) / st.session_state.wallet
    
    # Prognozuojame maksimalų pardavimo tašką pagal paskutinį judesį
    y = df['close'].tail(15).values
    slope, intercept = np.polyfit(np.arange(len(y)), y, 1)
    
    # Pirkimo ir pardavimo prognozė
    target_buy = cur_p if cur_p <= ma7 else ma7
    # Pardavimo tikslas: min 10€, bet jei kyla - gaudom viršūnę
    target_sell = target_buy + max(min_jump_needed + 2.0, slope * 40)

    st.title(f"💰 MAX PROFIT SCALPER: {round(st.session_state.wallet, 2)}€")
    
    # Pagrindiniai skaitliukai
    c1, c2, c3 = st.columns(3)
    c1.metric("PIRKTI TIES (Agresyviai)", f"{round(target_buy, 2)}€")
    c2.metric("PROGNOZUOJAMAS PARDAVIMAS", f"{round(target_sell, 2)}€")
    c3.metric("TIKĖTINAS PELNAS", f"{round((st.session_state.wallet/target_buy)*(target_sell-target_buy), 2)}€")

    # Garsinis signalas pirkimui
    if cur_p <= target_buy * 1.001:
        st.error(f"🚨 AGRESYVI PROGA! Kaina tinkama pirkimui. Tikslas: {round(target_sell, 2)}€")
        play_alert()

    # Grafikas su pirkimo/pardavimo ribom
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'].tail(40), df['close'].tail(40), label="ETH kaina", color='#1f77b4', linewidth=2)
    ax.plot(df['time'].tail(40), df['MA7'].tail(40), label="MA 7 (Greita)", color='gold', linestyle='--')
    ax.plot(df['time'].tail(40), df['MA25'].tail(40), label="MA 25 (Siena)", color='purple', linewidth=2)
    
    # Vizualios pelno ribos
    ax.axhline(y=target_buy, color='green', linestyle='-', alpha=0.3, label="Pirkimo zona")
    ax.axhline(y=target_sell, color='orange', linestyle='-', alpha=0.3, label="Pardavimo tikslas")
    ax.fill_between(df['time'].tail(40), target_buy-2, target_buy+1, color='green', alpha=0.1)
    
    ax.legend(loc='upper left')
    st.pyplot(fig)

    # 3. Prekybos vykdymas
    if st.session_state.active_trade is None:
        if st.button(f"SUDARYTI SANDORĮ (Investuoti {round(st.session_state.wallet, 2)}€)"):
            st.session_state.active_trade = {
                "buy_p": round(cur_p, 2),
                "target": round(target_sell, 2),
                "invested": st.session_state.wallet
            }
            st.session_state.trades_log.insert(0, {
                "Laikas": datetime.now().strftime("%H:%M"),
                "Veiksmas": "PIRKTI",
                "Kaina": round(cur_p, 2),
                "Tikslas": round(target_sell, 2)
            })
            st.rerun()

    # Pelnas ir Reinvestavimas
    if st.session_state.active_trade:
        t = st.session_state.active_trade
        current_gain = (t['invested'] / t['buy_p']) * (cur_p - t['buy_p'])
        st.warning(f"💼 Sandoris aktyvus. Pelnas dabar: {round(current_gain, 2)}€")
        
        # Parduodam pasiekus tikslą ARBA jei pelnas > 10€ ir trendas lūžta
        if cur_p >= t['target'] or (current_gain >= 10.0 and slope < -0.1):
            st.session_state.wallet += current_gain
            st.session_state.active_trade = None
            st.balloons()
            st.success(f"✅ PELNAS UŽFIKSUOTAS: {round(current_gain, 2)}€")

    st.subheader("📜 Piniginės augimo istorija")
    st.table(pd.DataFrame(st.session_state.trades_log).head(5))
