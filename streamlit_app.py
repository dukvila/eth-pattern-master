import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. ARCHITEKTŪRA
st.set_page_config(page_title="TITAN ORACLE V211", layout="wide")
st_autorefresh(interval=30000, key="v211_refresh")

if 'wallet' not in st.session_state: 
    st.session_state.wallet = 1711.45

def get_pro_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:] 
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # PRO MATEMATIKA: 
            # 1. Eksponentinis judantis vidurkis (EMA) jautresnis pokyčiams
            df['ema8'] = df['close'].ewm(span=8, adjust=False).mean()
            df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
            # 2. ATR (Average True Range) - rinkos nervingumo matas
            df['tr'] = np.maximum((df['high'] - df['low']), 
                                  np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                             abs(df['low'] - df['close'].shift(1))))
            df['atr'] = df['tr'].rolling(window=14).mean()
            return df
    except: return pd.DataFrame()

df = get_pro_data()

if not df.empty:
    # --- ANALITINIS BRANDUOLYS ---
    cur_p = df.iloc[-1]['close'] # ~1,749€
    rsi_v = 59.53 # Remiantis tavo naujausiu Omni-Scanner
    sma20 = 1737.44 #
    
    # Kritiniai lygiai iš nuotraukų
    p_high = 1758.64 #
    p_low = 1728.77 #
    
    st.markdown("<h1 style='text-align: center; color: #00d4ff;'>🏛️ TITAN ORACLE: DOCTORATE V211</h1>", unsafe_allow_html=True)

    # --- 1 DALIS: MATEMATINĖ RIZIKOS MATRICA ---
    st.subheader("🛡️ Rizikos ir Kapitalo Valdymas")
    col1, col2, col3 = st.columns(3)
    
    with col
