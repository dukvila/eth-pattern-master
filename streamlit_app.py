import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Švarus Branduolys (Ištaisytos visos tavo nuotraukose matytos klaidos)
st.set_page_config(page_title="TITAN RIOT V186", layout="wide")
st_autorefresh(interval=30000, key="v186_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:] 
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # --- 4 VALANDŲ ISTORIJOS ANALIZĖ ---
    hist_4h = df.tail(16).copy()
    volatility = (hist_4h['high'] - hist_4h['low']).mean()

    # --- AGRESYVI 20 VALANDŲ PROGNOZĖ (Su šuoliais ir nuosmukiais) ---
    future_steps = 80 
    last_p = hist_4h.iloc[-1]['close']
    
    # Generuojame "Riot" kreivę: trendas + atsitiktiniai rinkos smūgiai
    np.random.seed(int(datetime.now().timestamp() % 1000))
    noise = np.random.normal(0, volatility * 1.2, future_steps) # Padidintas triukšmas šuoliams
    trend = np.linspace(0, volatility * 2, future_steps)
    # Sukuriame zigzagą (kintančią kreivę)
    future_vals = last_p + trend + np.cumsum(noise) * 0.5 

    # Tikslūs taškai pagal tavo nustatytas ribas
    buy_p = round(hist_4h['low'].min() - 0.5, 2)
    sell_p = round(future_vals.max(), 2)

    st.markdown("<h1 style='text-align: center; color: #ff00ff;'>🔥 TITAN RIOT V186</h1>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH DABAR", f"{cur_p}€")
    c2.metric("AMD BUY", f"{buy_p}€", "DUGNAS")
    c3.metric("RIOT TARGET", f"{sell_p}€", "ŠUOLIS")
    c4.metric("BALANSAS", f"{round(st.session_state.wallet, 2)}€")

    # --- DINAMINIS GRAFIKAS ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(hist_4h['time'], hist_4h['close'], color='#00f2ff', label='4 val. Istorija', linewidth=2)
    
    # 20 valandų prognozė (Zigzagai, ne tiesė)
    f_times = [hist_4h['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, future_steps + 1)]
    ax.plot(f_times, future_vals, color='#ff00ff', linestyle='--', alpha=0.8, label='Agresyvūs 20 val. Šuoliai')
    
    ax.axhspan(buy_p - 2, buy_p + 1, color='green', alpha=0.1, label='Pirkimo zona')
    ax.axhspan
