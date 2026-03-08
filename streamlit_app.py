import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija - Greitas atnaujinimas ir stilius
st.set_page_config(page_title="TITAN PURE-AMD V177", layout="wide")
st_autorefresh(interval=30000, key="v177_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            # AMD Rodikliai
            df['EMA_Fast'] = df['close'].ewm(span=12).mean()
            df['EMA_Slow'] = df['close'].ewm(span=26).mean()
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # --- AMD ANALITIKA (Tavo nuotraukų pagrindu) ---
    # Accumulation: Vidutinė kaina per paskutinę valandą
    acc_level = df['close'].tail(4).mean()
    # Manipulation: Ieškome 0.3% "netikro" kritimo galimybės
    manip_dip = round(cur_p * 0.997, 2)
    # Distribution: Tikslas pagal tavo matytą Trend x AMD modelį
    dist_target = round(cur_p * 1.006, 2) 

    st.markdown(f"<h1 style='text-align: center; color: #00ff00;'>🔱 TITAN PURE-AMD V177</h1>", unsafe_allow_html=True)
    
    # METRIKOS
    m1, m2, m3 = st.columns(3)
    m1.metric("ETH DABAR", f"{cur_p}€", f"{round(cur_p - acc_level, 2)}€")
    m2.metric("MANIPULIACIJA (PIRKTI)", f"{manip_dip}€")
    m3.metric("DISTRIBUCIJA (TIKSLAS)", f"{dist_target}€")

    # --- GRAFIKAS (Pakeistas į Matplotlib, kad veiktų!) ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'], df['close'], color='#1f77b4', label='Kaina', linewidth=2)
    ax.plot(df['time'], df['EMA_Fast'], color='#00ff00', alpha=0.5, label='Fast Trend')
    
    # Prognozės vizualizacija (AMD Path)
    future_time = df['time'].iloc[-1] + timedelta(minutes=45)
    ax.annotate('', xy=(future_time, dist_target), xytext=(df['time'].iloc[-1], cur_p),
                arrowprops=dict(facecolor='yellow', shrink=0.05, width=2, headwidth=10))
    ax.text(future_time, dist_target, f' PROGNOZĖ: {dist_target}€', color='yellow', fontweight='bold')

    # Stilius
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    ax.grid(color='gray', linestyle='--', alpha=0.3)
    plt.legend()
    st.pyplot(fig)

    # --- VALDYMAS ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        in_buy = st.number_input("Pirkimas (Manipulation Zone)", value=manip_dip, key="b177")
        in_sell = st.number_input("Pardavimas (Distribution)", value=dist_target, key="s177")
    with c2:
        in_sum = st.number_input("Suma (€)", value=1000.0)
        potential = round((in_sum/in_buy) * (in_sell - in_buy), 2)
        if st.button("🔥 PALEISTI AMD REIDĄ", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.active_trades.append({"buy_p": in_buy, "sell_p": in_sell, "amount": in_sum, "status": "LAUKIA"})
                st.session_state.wallet -= in_sum
                st.rerun()
        st.write(f"Sėkmės atveju: **+{potential}€**")

    # LOGIKA
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA" and cur_p <= trade['buy_p']: trade['status'] = "🚀 VYKDOMAS"
        if trade['status'] == "🚀 VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "✅ PELNAS"; trade['final'] = profit
