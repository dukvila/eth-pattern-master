import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. KONFIGŪRACIJA IR BALANSAS
st.set_page_config(page_title="TITAN V8000", layout="wide")
st_autorefresh(interval=60000, key="titan_final")

# Tavo duomenys
SMA20_LEVEL = 1737.44
MY_BALANCE = 1711.45

# 2. DUOMENŲ GAVIMAS (KRAKEN API)
def fetch_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI skaičiavimas
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            
            # 4H PROGNOZĖ (Regression)
            y = df['close'].tail(32).values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            f_idx = np.arange(len(y), len(y) + 16)
            preds = slope * f_idx + intercept
            
            return df, preds
    except:
        return pd.DataFrame(), None

# 3. INTERFASAS
df, prediction = fetch_data()

if not df.empty:
    now = df.iloc[-1]
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🚀 TITAN V8000: CORE SYSTEM</h1>", unsafe_allow_html=True)
    
    # Šoninis valdymas
    st.sidebar.header("🕹️ Rizikos Valdymas")
    user_price = st.sidebar.number_input("Tavo Pirkimo Kaina (€):", value=now['close'])
    risk_pct = st.sidebar.slider("Stop Loss (%)", 0.5, 3.0, 1.0)
    sl_price = user_price * (1 - risk_pct / 100)
    
    # KPI RODIKLIAI
    c1, c2, c3 = st.columns(3)
    c1.metric("ESAMA KAINA", f"{now['close']} €")
    c2.metric("SMA20 AŠIS", f"{SMA20_LEVEL} €")
    c3.metric("BALANSAS", f"{MY_BALANCE} €")

    st.divider()

    # 4. GRAFIKAS (IŠTAISYTA 84 EILUTĖ - SKLIAUSTAI UŽDARYTI)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    h = df.tail(60)

    # Pagrindinė kaina
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Kaina')
    
    # SMA20 Ašis
    ax.axhline(SMA20_LEVEL, color='white', linestyle=':', alpha=0.4, label='SMA20 Pivot')
    
    # Stop Loss linija
    ax.axhline(sl_price, color='red', linestyle='-.', alpha=0.6, label='Stop Loss')

    # Prognozės linija (4 valandos)
    f_t = [h['time'].iloc[-1] + timedelta(minutes=15 * i) for i in range(1, 17)]
    ax.plot(f_t, prediction, color='#ff00ff', linestyle='--', label='4H Prognozė')

    # Perpirkimas (RSI > 70)
    ob = h[h['rsi6'] > 70]
    ax.scatter(ob['time'], ob['close'], color='orange', s=50, label='Perpirkimas')

    # Apipavidalinimas
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.legend(loc='upper left', fontsize='small')
    st.pyplot(fig)

    # 5. VERDIKTAS
    st.subheader("🧬 Analitinė Išvada")
    diff = round(prediction[-1] - user_price, 2)
    if diff > 0:
        st.success(f"Prognozuojamas kilimas: +{diff} € virš tavo kainos po 4 valandų.")
    else:
        st.error(f"Prognozuojamas kritimas: {diff} € žemiau tavo kainos.")
