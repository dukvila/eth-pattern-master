import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Griežta Konfigūracija
st.set_page_config(page_title="TITAN REVENGE V181", layout="wide")
st_autorefresh(interval=30000, key="v181_refresh")

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
    # AMD LOGIKA: Randame paskutinį stiprų dugną (Liquidity Low)
    # Tai ta vieta, kur kaina "nuėmė" visus stop-loss (kaip tavo 1661.75)
    liquid_low = df['low'].tail(50).min()
    
    # Nustatome pirkimo zoną TIK prie to dugno
    buy_zone = round(liquid_low + 2.0, 2)
    # Pardavimas - ties artimiausiu pasipriešinimu (Distribution)
    sell_target = round(df['high'].tail(20).max() - 3.0, 2)

    st.markdown(f"<h1 style='text-align: center; color: #ff0055;'>🩸 TITAN REVENGE V181</h1>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("RINKA DABAR", f"{cur_p}€")
    c2.metric("REVENGE BUY (AMD DUGNAS)", f"{buy_zone}€")
    c3.metric("SELL TARGET (DISTRIBUTION)", f"{sell_target}€")

    # --- GRAFIKAS SU AMD ZONOMIS ---
        fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'], df['close'], color='white', label='Kaina')
    
    # Vizualizuojame zonas pagal tavo pavyzdžius (image_67455d.png)
    ax.axhspan(liquid_low - 5, buy_zone, color='cyan', alpha=0.3, label='Manipulation (PIRKTI)')
    ax.axhspan(sell_target, sell_target + 5, color='magenta', alpha=0.2, label='Distribution (PARDUOTI)')
    
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    plt.legend()
    st.pyplot(fig)

    # --- VALDYMAS ---
    st.divider()
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🎯 Snaiperio užduotis")
        final_buy = st.number_input("Pirkimas ties uodega", value=buy_zone)
        final_sell = st.number_input("Pardavimas viršuje", value=sell_target)
    with col_r:
        in_sum = st.number_input("Suma (€)", value=1000.0)
        if st.button("🔱 PALEISTI REVENGE REIDĄ", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.active_trades.append({"buy": final_buy, "sell": final_sell, "amt": in_sum, "status": "MEDŽIOJA"})
                st.session_state.wallet -= in_sum
                st.rerun()

    # LOGIKA: Jokių prisitaikymų, tik vykdymas
    for t in st.session_state.active_trades:
        if t['status'] == "MEDŽIOJA" and cur_p <= t['buy']:
            t['status'] = "🚀 POZICIJOJE"
        if t['status'] == "🚀 POZICIJOJE" and cur_p >= t['sell']:
            profit = (t['amt'] / t['buy']) * (t['sell'] - t['buy'])
            st.session_state.wallet += (t['amt'] + profit)
            t['status'] = "✅ PROFIT"; st.balloons()
