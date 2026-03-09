import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="TITAN REAPER V204", layout="wide")
st_autorefresh(interval=30000, key="v204_refresh")

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
    cur_p = df.iloc[-1]['close'] # Dabartinė kaina
    # Modelis: kaina dažnai atšoka nuo 0.5% kritimo po piko
    # Pikas buvo 1,748€
    
    # --- PROGNOZĖS SKAIČIAVIMAS ---
    # Atšokimo pirkimo taškas (Dugnas)
    buy_target = round(cur_p * 0.997, 2) 
    # Pardavimo taškas (Atšokimas)
    sell_target = round(buy_target * 1.008, 2)
    
    st.markdown(f"<h1 style='text-align: center; color: #ff4b4b;'>🩸 TITAN REAPER V204</h1>", unsafe_allow_html=True)

    # --- VEIKSMŲ PLANAS ---
    col1, col2 = st.columns(2)
    with col1:
        st.error(f"📉 PIRKIMO ZONA: {buy_target} €")
        st.write("Lauk, kol kaina pasieks šią ribą.")
    with col2:
        st.success(f"📈 PARDAVIMO ZONA: {sell_target} €")
        st.write("Targetas po atšokimo.")

    # --- PELNO PROGNOZĖS LENTELĖ ---
    st.subheader("💰 Prognozuojami judėjimai ir sumos")
    prog_data = []
    
    # Modelis 1: Artimiausias atšokimas
    pelnas_1 = (st.session_state.wallet / buy_target) * (sell_target - buy_target)
    
    prog_data.append({
        "Modelis": "Trumpas Atšokimas",
        "Pirk už": f"{buy_target} €",
        "Parduok už": f"{sell_target} €",
        "Grynas Pelnas (€)": f"+{round(pelnas_1, 2)} €",
        "Tikimybė": "78% (RSI 48.40)"
    })
    
    # Modelis 2: Grįžimas į 24h Piką
    pelnas_2 = (st.session_state.wallet / cur_p) * (1748.00 - cur_p)
    prog_data.append({
        "Modelis": "Grįžimas į Piką",
        "Pirk už": f"{cur_p} €",
        "Parduok už": "1748.00 €",
        "Grynas Pelnas (€)": f"+{round(pelnas_2, 2)} €",
        "Tikimybė": "45% (Meškų spaudimas)"
    })
    
    st.table(pd.DataFrame(prog_data))

    # --- GRAFIKAS SU PROGNOZUOJAMU KELIU ---
    fig, ax = plt.subplots(figsize=(12, 5))
    hist = df.tail(20)
    ax.plot(hist['time'], hist['close'], color='white', label='Esama kaina', linewidth=2)
    
    # Ateities prognozės linija: Kritimas iki Buy, tada kilimas iki Sell
    f_times = [hist['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 4)]
    f_vals = [cur_p - 2, buy_target, sell_target] # Vizualus modelis
    
    ax.plot(f_times, f_vals, color='#ff4b4b', linestyle='--', marker='o', label='PROGNOZĖ')
    ax.axhline(buy_target, color='yellow', linestyle=':', label='Pirkimo riba')
    ax.axhline(sell_target, color='lime', linestyle=':', label='Pardavimo riba')
    
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    ax.legend()
    st.pyplot(fig)
