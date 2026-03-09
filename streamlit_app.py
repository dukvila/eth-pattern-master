import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="TITAN PREDICTOR-ULTRA V183", layout="wide")
st_autorefresh(interval=45000, key="v183_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []

def get_market_data():
    try:
        # Traukiame duomenis 15 min intervalais (kad padengtume 4 val istoriją)
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-120:] # Paskutinės 30 valandų
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

df = get_market_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # --- 4 VALANDŲ ISTORIJOS ANALIZĖ ---
    history_4h = df.tail(16) # 16 žvakių po 15 min = 4 valandos
    h_min = history_4h['low'].min()
    h_max = history_4h['high'].max()
    volatility = h_max - h_min

    # --- 20 VALANDŲ ATEITIES PROGNOZĖ (Regression + AMD Shadow) ---
    x_hist = np.arange(len(df))
    y_hist = df['close'].values
    z = np.polyfit(x_hist, y_hist, 2) # Antro laipsnio regresija trendui pagauti
    p = np.poly1d(z)
    
    # Generuojame ateities 20 valandų (80 žvakių)
    future_steps = 80
    future_x = np.arange(len(df), len(df) + future_steps)
    future_y = p(future_x)
    
    # Pritaikome AMD "manipuliacijos" koeficientą (ieškome dugno prieš atšokimą)
    prediction_min = round(min(future_y) - (volatility * 0.2), 2)
    prediction_max = round(max(future_y) + (volatility * 0.4), 2)
    
    # Tikslūs prekybos taškai pagal tavo nuotraukų logiką
    buy_strike = round(cur_p - (volatility * 0.35), 2)
    sell_strike = round(prediction_max, 2)

    st.markdown(f"<h1 style='text-align: center; color: #00f2ff;'>👁️ TITAN PREDICTOR V183</h1>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ESAMA KAINA", f"{cur_p}€")
    c2.metric("PIRKTI TIES (AMD)", f"{buy_strike}€", "MEDŽIOKLĖ")
    c3.metric("PARDUOTI TIES", f"{sell_strike}€", "TIKSLAS")
    c4.metric("BALANSAS", f"{round(st.session_state.wallet, 2)}€")

    # --- PAGRINDINIS PROGNOZĖS GRAFIKAS ---
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Istorija
    ax.plot(df['time'], df['close'], color='white', label='4 val. Istorija', linewidth=1.5)
    
    # Ateities prognozė (20 val.)
    future_times = [df['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, future_steps + 1)]
    ax.plot(future_times, future_y, color='yellow', linestyle='--', alpha=0.7, label='20 val. Prognozė')
    
    # Zonos
    ax.axhspan(buy_strike - 3, buy_strike + 1, color='green', alpha=0.2, label='Pirkimo zona')
    ax.axhspan(sell_strike - 1, sell_strike + 3, color='red', alpha=0.2, label='Pelnas')

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    plt.legend()
    st.pyplot(fig)

    # --- OPERACIJŲ KONSTRUKTORIUS ---
    st.divider()
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🛠️ Automatinė Strategija")
        final_buy = st.number_input("Pirkimo kaina", value=buy_strike)
        final_sell = st.number_input("Pardavimo kaina", value=sell_strike)
    
    with col_r:
        in_sum = st.number_input("Investicija (€)", value=1000.0)
        p_profit = round((in_sum/final_buy) * (final_sell - final_buy), 2)
        if st.button("🚀 PALEISTI PREDICTOR REIDĄ", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.active_trades.append({
                    "buy": final_buy, "sell": final_sell, "amt": in_sum, "status": "LAUKIA"
                })
                st.session_state.wallet -= in_sum
                st.success(f"Užduotis priimta. Tikslas: **+{p_profit}€**")
                st.rerun()

    # Logika (be klaidų)
    for t in st.session_state.active_trades:
        if t['status'] == "LAUKIA" and cur_p <= t['buy']: t['status'] = "🚀 VYKDOMAS"
        if t['status'] == "🚀 VYKDOMAS" and cur_p >= t['sell']:
            profit = (t['amt'] / t['buy']) * (t['sell'] - t['buy'])
            st.session_state.wallet += (t['amt'] + profit)
            t['status'] = "✅ PELNAS"; st.balloons()
