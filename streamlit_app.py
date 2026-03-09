import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Branduolys
st.set_page_config(page_title="TITAN CHRONOS V206", layout="wide")
st_autorefresh(interval=30000, key="v206_refresh")

if 'wallet' not in st.session_state: 
    st.session_state.wallet = 1711.45

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
    except: 
        return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close'] # Dabartinė kaina apie 1,733€
    vol = (df['high'] - df['low']).tail(10).mean()
    
    st.markdown(f"<h1 style='text-align: center; color: #00ffcc;'>⏳ TITAN CHRONOS V206</h1>", unsafe_allow_html=True)

    # --- TIKSLUS VEIKSMŲ PLANAS ---
    st.subheader("💰 KADA PIRKTI IR PARDUOTI (Modelis: Atšokimas į 1748€)")
    
    # Modelis remiasi tavo nuotraukose matytu 24h piku - 1,748€
    target_p = 1748.00
    expected_profit = (st.session_state.wallet / cur_p * target_p) - st.session_state.wallet
    
    c1, c2 = st.columns(2)
    c1.warning(f"📥 PIRKTI DABAR: {cur_p} €")
    c2.success(f"📤 PARDUOTI TIES: {target_p} € (Pelnas: +{round(expected_profit, 2)} €)")

    # --- 4 VALANDŲ PROGNOZĖS LENTELĖ (KAS 15 MIN.) ---
    st.subheader("📅 4 Valandų Detali Prognozė")
    future_data = []
    for i in range(1, 17): # 16 žvakių = 4 valandos
        f_time = (datetime.now() + timedelta(minutes=15*i)).strftime("%H:%M")
        # Modelis: lėtas kilimas po stabilizacijos
        f_price = round(cur_p + (vol * 0.45 * i), 2)
        pelnas = (st.session_state.wallet / cur_p * f_price) - st.session_state.wallet
        
        future_data.append({
            "Laikas": f_time,
            "Prognozė": f"{f_price} €",
            "Suma Balanse": f"{round(st.session_state.wallet + pelnas, 2)} €",
            "Grynas Pelnas": f"+{round(pelnas, 2)} €"
        })
    
    # Rodome visą lentelę su slinktimi
    st.dataframe(pd.DataFrame(future_data), use_container_width=True)

    # --- 2 VAL. PRAEITIS + 4 VAL. ATEITIS ---
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Rodome 8 žvakes (2 valandas) praeities
    hist = df.tail(8)
    ax.plot(hist['time'], hist['close'], color='white', label='Istorija (2 val.)', linewidth=2)
    
    # 4 valandų prognozės linija
    f_times = [hist['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 17)]
    f_vals = [cur_p + (vol * 0.45 * i) for i in range(1, 17)]
    ax.plot(f_times, f_vals, color='#00ffcc', linestyle='--', marker='o', label='Prognozė (4 val.)')
    
    # Kritinės ribos iš tavo grafikų
    ax.axhline(1748.00, color='gold', linestyle=':', label='Dienos pikas (1748€)')
    ax.axhline(1730.58, color='red', linestyle=':', label='Dabartinis palaikymas (1730€)')

    ax.set_facecolor('#0E1117'); fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white'); ax.legend(facecolor='#0E1117', labelcolor='white')
    st.pyplot(fig)
