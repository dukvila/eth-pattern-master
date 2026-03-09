import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# I. NUSTATYMAI (PAGAL TAVO NUOTRAUKAS)
# ==============================================================================
st.set_page_config(page_title="TITAN V1100", layout="wide")
st_autorefresh(interval=30000, key="v1100_refresh")

# Tavo nustatyti kritiniai lygiai
H24_HIGH = 1758.64  #
H24_LOW = 1660.00   #
SMA20_PIVOT = 1737.44  #

# ==============================================================================
# II. ANALITINIS VARIKLIS (TAVO CHEAT SHEET)
# ==============================================================================
def apply_logic(df):
    # RSI(6) tikslumas pagal tavo ekranus
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
    df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
    
    # SMA20 - Tavo pagrindinis filtras
    df['sma20'] = df['close'].rolling(20).mean()
    
    # Pattern Match: Bullish Engulfing
    df['buy_signal'] = (df['close'] > df['open']) & \
                       (df['close'].shift(1) < df['open'].shift(1)) & \
                       (df['close'] >= df['open'].shift(1))
    return df

# ==============================================================================
# III. SAUGUS DUOMENŲ GAVIMAS
# ==============================================================================
def get_clean_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return apply_logic(df)
    except Exception as e:
        st.error(f"Ryšio klaida: {e}")
        return pd.DataFrame()

# ==============================================================================
# IV. VAIZDINIS VALDYMO PULTAS
# ==============================================================================
df = get_clean_data()

if not df.empty:
    now = df.iloc[-1]
    
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN COMMAND V1100</h1>", unsafe_allow_html=True)
    
    # Svarbiausi rodikliai
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("ESAMA KAINA", f"{now['close']} €")
    with c2:
        st.metric("RSI(6) IMPULSAS", round(now['rsi6'], 2))
    with c3:
        status = "🟢 BULL" if now['close'] > SMA20_PIVOT else "🔴 BEAR"
        st.metric("TRENDAS (SMA20)", status)

    st.divider()

    # Modernus grafikas be jokių "Plotly" klaidų
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5))
    h = df.tail(40)
    
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Kaina')
    ax.plot(h['time'], h['sma20'], color
