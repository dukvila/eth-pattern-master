import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Branduolys
st.set_page_config(page_title="TITAN LOGIC V209", layout="wide")
st_autorefresh(interval=30000, key="v209_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:] 
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close'] # ~1,749.83€
    support_level = 1746.80 # Paskutinis dugnas
    resistance_level = 1758.64 # Naujas pikas
    
    st.markdown(f"<h1 style='text-align: center; color: #ffcc00;'>🧠 TITAN LOGIC V209</h1>", unsafe_allow_html=True)

    # --- LOGIKOS ANALIZATORIUS ---
    c1, c2 = st.columns(2)
    with c1:
        if cur_p > support_level:
            st.success(f"✅ LOGIKA: TRENDAS KILANTIS. Kaina laikosi virš {support_level} €")
        else:
            st.error(f"❌ LOGIKA: TRENDAS LŪŽO. Kaina nukrito žemiau {support_level} €")
    
    with c2:
        rsi_val = 60.17 # Iš tavo foto
        st.metric("RSI BŪSENA", f"{rsi_val}", "ERDVĖS KILIMUI YRA" if rsi_val < 70 else "PERKAITA")

    # --- 4 VALANDŲ SCENARIJAI ---
    st.subheader("📊 Loginiai Scenarijai (Pelnas su 1711.45€)")
    vol = (df['high'] - df['low']).tail(5).mean()
    
    logic_table = []
    for i in range(1, 17):
        f_time = (datetime.now() + timedelta(minutes=15*i)).strftime("%H:%M")
        # Loginis modelis: Lėtas kilimas link 1,770€ arba stabilizacija
        f_price = round(cur_p + (vol * 0.25 * i), 2)
        pelnas = (st.session_state.wallet / cur_p * f_price) - st.session_state.wallet
        
        logic_table.append({
            "Laikas": f_time,
            "Prognozė": f"{f_price} €",
            "Pelnas (€)": f"+{round(pelnas, 2)} €",
            "Sprendimas": "LAIKYTI" if f_price > resistance_level else "LAUKTI"
        })
    st.dataframe(pd.DataFrame(logic_table[::2]), use_container_width=True)

    # --- VAIZDINĖ LOGIKA ---
    fig, ax = plt.subplots(figsize=(10, 4))
    hist = df.tail(8)
    ax.plot(hist['time'], hist['close'], color='white', label='Istorija (2 val.)')
    
    # Prognozės linija
    f_times = [hist['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 17)]
    f_vals = [cur_p + (vol * 0.25 * i) for i in range(1, 17)]
    ax.plot(f_times, f_vals, color='#ffcc00', linestyle='--', label='Loginis kelias')
    
    ax.axhline(support_level, color='red', linestyle=':', label='STOP LOSS (1746€)')
    ax.axhline(resistance_level, color='cyan', linestyle=':', label='BREAKOUT (1758€)')
    
    ax.set_facecolor('#0E1117'); fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white'); ax.legend(facecolor='#0E1117', labelcolor='white')
    st.pyplot(fig)
