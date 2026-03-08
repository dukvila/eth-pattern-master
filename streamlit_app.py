import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Griežta Konfigūracija
st.set_page_config(page_title="TITAN LIQUIDITY V179", layout="wide")
st_autorefresh(interval=30000, key="v179_refresh")

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
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    # Nustatome TIKRĄ likvidumo dugną (žemiausia žvakės uodega per 24 val.)
    liquidity_bottom = df['low'].tail(96).min() 
    # Nustatome TIKRĄ pasipriešinimą (kur rinka "apsisuko" paskutinį kartą)
    real_resistance = df['high'].tail(24).max()
    
    # AMD Strategija: Perkam tik ten, kur kiti praranda viltį (prie liquidity_bottom)
    hunt_buy = round(liquidity_bottom + (cur_p * 0.001), 2)
    hunt_sell = round(cur_p + (real_resistance - cur_p) * 0.6, 2) # Realus, pasiekiamas tikslas

    st.markdown(f"<h1 style='text-align: center; color: #00f2ff;'>🎯 TITAN LIQUIDITY HUNTER V179</h1>", unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("ETH DABAR", f"{cur_p}€")
    m2.metric("MEDŽIOKLĖS ZONA (BUY)", f"{hunt_buy}€", "LIKVIDUMAS", delta_color="inverse")
    m3.metric("IŠĖJIMO TIKSLAS (SELL)", f"{hunt_sell}€")

    # --- GRAFIKAS: LIKVIDUMO ŽEMĖLAPIS ---
        fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'], df['close'], color='white', linewidth=1, label='Market')
    
    # Vizualizuojame pirkimo ir pardavimo zonas pagal tavo pavyzdžius
    ax.axhspan(liquidity_bottom, hunt_buy, color='cyan', alpha=0.3, label='Liquidity Sweep Zone')
    ax.axhspan(hunt_sell, real_resistance, color='magenta', alpha=0.2, label='Take Profit Zone')
    
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    plt.legend(loc='upper left')
    st.pyplot(fig)

    # --- REIDO VALDYMAS ---
    st.divider()
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🛠️ Operacijos nustatymai")
        final_buy = st.number_input("Pirkimo kaina (Medžioklė)", value=hunt_buy)
        final_sell = st.number_input("Pardavimo kaina (Profit)", value=hunt_sell)
    
    with col_r:
        in_sum = st.number_input("Investicija (€)", value=1000.0)
        potential = round((in_sum/final_buy) * (final_sell - final_buy), 2)
        if st.button("🔱 PALEISTI LIQUIDITY REIDĄ", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.active_trades.append({
                    "buy_p": final_buy, "sell_p": final_sell, "amount": in_sum, "status": "MEDŽIOJA"
                })
                st.session_state.wallet -= in_sum
                st.success("Reidas aktyvuotas. Laukiama kainos įkritimo į zoną.")
                st.rerun()
        st.write(f"Planuojamas uždarbis: **+{potential}€**")

    # --- LOGIKA: JOKIŲ NUOLAIDŲ ---
    for trade in st.session_state.active_trades:
        if trade['status'] == "MEDŽIOJA" and cur_p <= trade['buy_p']:
            trade['status'] = "🔥 POZICIJOJE"
        if trade['status'] == "🔥 POZICIJOJE" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "✅ PELNAS SUGAUTAS"
            st.session_state.history.append(trade)
            st.balloons()
