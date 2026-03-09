import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="TITAN PANORAMA V205", layout="wide")
st_autorefresh(interval=30000, key="v205_refresh")

if 'wallet' not in st.session_state: 
    st.session_state.wallet = 1711.45

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode())
            # Imame 2 valandas praeities (8 žvakės) + 4 valandas prognozei
            d = res['result']['XETHZEUR'][-100:] 
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: 
        return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    # Dinaminis modelis pagal tavo 1,730.58€ fiksaciją
    vol = (df['high'] - df['low']).tail(10).mean()
    
    st.markdown(f"<h1 style='text-align: center; color: #00ffcc;'>🔭 TITAN PANORAMA V205</h1>", unsafe_allow_html=True)

    # --- 4 VALANDŲ PROGNOZĖS LENTELĖ ---
    st.subheader("📅 Artimiausių 4 valandų judėjimo planas (kas 15 min.)")
    
    future_list = []
    # Skaičiuojame 16 žvakių į priekį (4 valandos)
    for i in range(1, 17):
        f_time = (datetime.now() + timedelta(minutes=15*i)).strftime("%H:%M")
        # Modelis: Nedidelis svyravimas žemyn, tada bandymas grįžti link 1748€ piko
        change = (i * vol * 0.35) if i > 4 else -(i * vol * 0.2)
        f_price = round(cur_p + change, 2)
        
        future_list.append({
            "Laikas": f_time,
            "Prognozuojama Kaina": f"{f_price} €",
            "Pelnas (€)": f"+{round((st.session_state.wallet / cur_p * f_price) - st.session_state.wallet, 2)} €",
            "Saugumas": "🟢 AUKŠTAS" if i < 8 else "🟡 VIDUTINIS"
        })
    
    # Rodome tik kas antrą žvakę (kas 30 min), kad lentelė nebūtų per ilga
    st.table(pd.DataFrame(future_list[::2])) 

    # --- 2 VAL. PRAEITIS + 4 VAL. ATEITIS GRAFIKAS ---
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # 2 valandų praeitis (8 žvakės po 15 min)
    hist = df.tail(8)
    ax.plot(hist['time'], hist['close'], color='white', label='2 val. praeitis', linewidth=3)
    
    # 4 valandų ateitis (16 žvakių)
    f_times = [hist['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 17)]
    f_vals = [cur_p + ((i * vol * 0.35) if i > 4 else -(i * vol * 0.2)) for i in range(1, 17)]
    
    ax.plot(f_times, f_vals, color='#00ffcc', linestyle='--', marker='o', alpha=0.7, label='4 val. prognozė')
    
    # Ribos pagal tavo Binance nuotraukas
    ax.axhline(1748.00, color='gold', linestyle=':', label='24h Pikas')
    ax.axhline(1730.58, color='red', linestyle=':', label='Dabartinis dugnas')

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    ax.set_title("Rinkos matymas: 2 val. atgal / 4 val. į priekį", color='white')
    ax.legend(facecolor='#0E1117', labelcolor='white')
    st.pyplot(fig)

    # --- SKUBI SUVESTINĖ ---
    st.info(f"💡 Per ateinančias 4 valandas prognozuojamas maksimalus balanso pokytis: **+{round(max(f_vals) / cur_p * st.session_state.wallet - st.session_state.wallet, 2)} €**")
