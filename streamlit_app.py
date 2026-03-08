import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="TITAN ABSOLUTE V178", layout="wide")
st_autorefresh(interval=60000, key="v178_refresh") # Atnaujinimas kas 1 min (rimtesnei analizei)

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-120:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # --- ABSOLIUTI ANALITIKA (Pagal tavo image_67455d.png) ---
    # Nustatome pasipriešinimo zoną, kur kaina TIKRAI atšoks
    resistance_zone = df['high'].tail(24).max() 
    # Nustatome manipuliacijos dugną (kur pirkimas turi prasmę)
    support_zone = df['low'].tail(24).min()
    
    # Tikrasis AMD tikslas (ne "prisitaikantis", o siekiantis viršūnės)
    absolute_target = round(resistance_zone * 0.998, 2) 

    st.markdown(f"<h1 style='text-align: center; color: #ff4b4b;'>🩸 TITAN ABSOLUTE V178</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("RINKOS KAINA", f"{cur_p}€")
    col2.metric("DUGNO ZONA (SUPPORT)", f"{support_zone}€")
    col3.metric("TIKRAS TIKSLAS (TARGET)", f"{absolute_target}€")

    # --- GRAFIKAS SU ZONOMIS ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'], df['close'], color='white', label='Kaina')
    
    # Brėžiame AMD zonas kaip tavo pavyzdžiuose
    ax.axhspan(support_zone, support_zone + 5, color='green', alpha=0.2, label='Manipulation Zone')
    ax.axhspan(absolute_target - 5, absolute_target, color='red', alpha=0.2, label='Distribution Zone')
    
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    plt.legend()
    st.pyplot(fig)

    # --- VEIKSMŲ CENTRAS ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🤖 Algoritmo Sprendimas")
        if cur_p > support_zone + 10:
            st.warning("⚠️ Kaina per aukštai. Laukiame manipuliacijos (kritimo į žalią zoną).")
        else:
            st.success("✅ Pirkimo zona pasiekta. Galima vykdyti reidą.")
            
        in_buy = st.number_input("Pirkimo riba", value=round(support_zone + 2, 2))
        in_sell = st.number_input("Pardavimo riba", value=absolute_target)
    
    with c2:
        in_sum = st.number_input("Investicija (€)", value=1000.0)
        if st.button("🚀 VYKDYTI ATSAKOMYBĖS REIDĄ", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.active_trades.append({"buy_p": in_buy, "sell_p": in_sell, "amount": in_sum, "status": "LAUKIA"})
                st.session_state.wallet -= in_sum
                st.info("Sandoris užfiksuotas. Robotas nebekeis tikslų.")
                st.rerun()

    # LOGIKA BE "PRISITAIKYMO"
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA" and cur_p <= trade['buy_p']:
            trade['status'] = "🚀 VYKDOMAS"
        if trade['status'] == "🚀 VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "✅ PELNAS"
            st.balloons()
