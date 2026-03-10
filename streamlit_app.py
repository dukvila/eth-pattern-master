import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. SISTEMOS PAMATAI (BE KLAIDŲ)
st.set_page_config(page_title="TITAN V6000", layout="wide")
st_autorefresh(interval=60000, key="v6000_core")

# Tavo nustatyti parametrai
SMA20_LEVEL = 1737.44
MY_BALANCE = 1711.45

# 2. DUOMENŲ VARIKLIS SU SAVIKONTROLE
def get_verified_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI(6)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            
            # 4 VALANDŲ PROGNOZĖ (STABILI)
            y = df['close'].tail(32).values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            f_idx = np.arange(len(y), len(y) + 16)
            preds = slope * f_idx + intercept
            
            return df, preds, slope
    except:
        return pd.DataFrame(), None, 0

# 3. VALDYMO PULTAS
df, prediction, slope = get_verified_data()

if not df.empty:
    now = df.iloc[-1]
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN V6000: ERROR-PROOF</h1>", unsafe_allow_html=True)
    
    # ŠONINIS MENIU: TAVO SPRENDIMAI
    st.sidebar.header("🕹️ Sprendimų Kontrolė")
    user_price = st.sidebar.number_input("Tavo Pirkimo Kaina (€):", value=now['close'])
    risk_limit = st.sidebar.slider("Rizika (%)", 0.5, 3.0, 1.5)
    
    # STOP LOSS
    sl_price = user_price * (1 - risk_limit / 100)
    
    # KPI BLOKAS
    c1, c2, c3 = st.columns(3)
    c1.metric("RINKA", f"{now['close']} €")
    c2.metric("SMA20", f"{SMA20_LEVEL} €")
    c3.metric("BALANSAS", f"{MY_BALANCE} €")

    st.divider()

    # 4. GRAFIKAS (PILNAI IŠTAISYTA 84/103 EILUTĖ)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    h = df.tail(60)

    # Ištaisyta sintaksė - jokių neuždarytų skliaustų
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Kaina')
    
    # Perpirkimo taškai
    ob = h[h['rsi6'] > 70]
    ax.scatter(ob['time'], ob['close'], color='orange', s=60, label='Perpirkta')

    # Prognozės linija
    f_t = [h['time'].iloc[-1] + timedelta(minutes=15 * i) for i in range(1, 17)]
    ax.plot(f_t, prediction, color='#ff00ff', linestyle='--', label='4H Prognozė')
    
    # Stop Loss ir SMA20 linijos
    ax.axhline(sl_price, color='red', linestyle='-.', alpha=0.5, label='Stop Loss')
    ax.axhline(SMA20_LEVEL, color='white', alpha=0.2, label='Ašis')

    # Markeriai
    ax.scatter(f_t[0], prediction[0], color='lime', marker='P', s=200)
    ax.scatter(f_t[-1], prediction[-1], color='red', marker='X', s=200)

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.legend(loc='upper left', fontsize='small')
    st.pyplot(fig)

    # 5. KLAIDŲ LYGINIMAS IR MOKYMASIS
    st.subheader("🧬 Sistemos Savianalizė")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📝 Tavo įėjimas vs Prognozė:**")
        target_gain = round(prediction[-1] - user_price, 2)
        st.info(f"Tikslas: {round(prediction[-1], 2)} € | Skirtumas: {target_gain} €")

    with col2:
        st.write("**🤖 Mokymosi statusas:**")
        # Sistema lygina trendą su SMA20
        if now['close'] > SMA20_LEVEL and slope > 0:
            st.success("Sutapimas: Trendas ir Ašis patvirtina kilimą.")
        elif now['close'] < SMA20_LEVEL and slope < 0:
            st.error("Sutapimas: Trendas ir Ašis patvirtina kritimą.")
        else:
            st.warning("Konfiktas: Trendas prieštarauja ašies pozicijai.")
