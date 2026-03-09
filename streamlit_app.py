import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Branduolys
st.set_page_config(page_title="TITAN VOLATILITY V186", layout="wide")
st_autorefresh(interval=30000, key="v186_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            # Traukiame tik tiek, kiek reikia 4 val. istorijai (16 žvakių) + rezervas
            d = res['result']['XETHZEUR'][-100:] 
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except:
        return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # --- 4 VALANDŲ ISTORIJOS FILTRAS ---
    hist_4h = df.tail(16).copy()
    
    # Skaičiuojame kintamumą (šuolius) prognozei
    volatility = (hist_4h['high'] - hist_4h['low']).mean()

    # --- DINAMINĖ 20 VALANDŲ PROGNOZĖ (Su šuoliais) ---
    future_steps = 80 # 20 valandų po 4 žvakes
    last_p = hist_4h.iloc[-1]['close']
    
    # Generuojame kreivę su atsitiktiniais rinkos "šokiais"
    np.random.seed(int(datetime.now().timestamp() / 100))
    shocks = np.random.normal(0, volatility * 0.8, future_steps)
    trend = np.linspace(0, volatility * 2, future_steps)
    future_vals = last_p + trend + np.cumsum(shocks)

    # Tikslūs AMD taškai
    buy_p = round(hist_4h['low'].min() - 0.5, 2)
    sell_p = round(future_vals.max(), 2)

    st.markdown("<h1 style='text-align: center; color: #ff00ff;'>📈 TITAN VOLATILITY V186</h1>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH DABAR", f"{cur_p}€")
    c2.metric("AMD BUY", f"{buy_p}€", "DUGNAS")
    c3.metric("SELL TARGET", f"{sell_p}€", "PIKAS")
    c4.metric("BALANSAS", f"{round(st.session_state.wallet, 2)}€")

    # --- GRAFIKAS SU DINAMINE KREIVE ---
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # 4 valandų istorija (Mėlyna)
    ax.plot(hist_4h['time'], hist_4h['close'], color='#00f2ff', label='4 val. Istorija', linewidth=2)
    
    # 20 valandų prognozė (Violetinė su šuoliais)
    f_times = [hist_4h['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, future_steps + 1)]
    ax.plot(f_times, future_vals, color='#ff00ff', linestyle='--', alpha=0.
