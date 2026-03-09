import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Branduolys (Ištaisytos visos skliaustų ir indentacijos klaidos)
st.set_page_config(page_title="TITAN RIOT V187", layout="wide")
st_autorefresh(interval=30000, key="v187_refresh")

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
    # --- 4 VALANDŲ ISTORIJA ---
    # Analizuojame tik paskutines 16 žvakių (15min * 16 = 4 valandos)
    hist_4h = df.tail(16).copy()
    cur_p = hist_4h.iloc[-1]['close']
    volatility = (hist_4h['high'] - hist_4h['low']).mean()

    # --- AGRESYVI 20 VALANDŲ PROGNOZĖ ---
    # Sugeneruojame zigzagą, kuris imituoja šuolius ir nuosmukius
    future_steps = 80 
    np.random.seed(int(datetime.now().timestamp() % 1000))
    # Sukuriame "triukšmingą" kelią
    shocks = np.random.normal(0, volatility * 1.5, future_steps)
    trend = np.linspace(0, volatility * 2, future_steps)
    future_vals = cur_p + trend + np.cumsum(shocks)

    # Tikslūs AMD taškai iš tavo nustatymų
    buy_p = round(hist_4h['low'].min() - 0.5, 2)
    sell_p = round(future_vals.max(), 2)

    st.markdown("<h1 style='text-align: center; color: #ff00ff;'>⚡ TITAN RIOT V187</h1>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH DABAR", f"{cur_p}€")
    c2.metric("AMD BUY", f"{buy_p}€", "DUGNAS")
    c3.metric("RIOT TARGET", f"{sell_p}€", "ŠUOLIS")
    c4.metric("BALANSAS", f"{round(st.session_state.wallet, 2)}€")

    # --- GRAFIKAS SU SHOCK KREIVE ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(hist_4h['time'], hist_4h['close'], color='#00f2ff', label='4 val. Istorija', linewidth=2)
    
    # 20 valandų prognozė (Violetinis zigzagas)
    f_times = [hist_4h['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, future_steps + 1)]
    ax.plot(f_times, future_vals, color='#ff00ff', linestyle='--', alpha=0.8, label='Shock Prognozė')
    
    # Horizontalios zonos
    ax.axhspan(buy_p - 1, buy_p + 1, color='green', alpha=0.1, label='Pirkimas')
    ax.axhspan(sell_p - 1, sell_p + 1, color='red', alpha=0.1, label='Pardavimas')

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    plt.legend(facecolor='#0E1117', labelcolor='white')
    st.pyplot(fig)

    # --- VALDYMAS ---
    if st.button("🔱 PALEISTI SHOCK REIDĄ", use_container_width=True):
        st.session_state.active_trades.append({"buy": buy_p, "sell": sell_p, "status": "ACTIVE"})
        st.toast(f"Taikinys: {sell_p}€", icon="🎯")
