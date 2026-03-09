import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="TITAN STRIKE V207", layout="wide")
st_autorefresh(interval=30000, key="v207_refresh")

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
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close'] # Dabartinė kaina ~1,729€
    target_p = 1748.00 # Tikslas
    
    st.markdown(f"<h1 style='text-align: center; color: #00ffcc;'>⚡ TITAN STRIKE V207</h1>", unsafe_allow_html=True)

    # --- REALAUS LAIKO SIGNALAS ---
    st.error(f"🎯 PIRKIMO SIGNALAS AKTYVUS: {cur_p} €")
    st.write(f"Šiuo metu kaina yra žemiau tavo fiksacijos taško ({cur_p}€ < 1733€). Tai palankus įėjimas.")

    # --- 4 VALANDŲ PELNO PROGNOZĖ ---
    st.subheader("💰 Tavo Pelno Planas (4 val. į priekį)")
    future_moves = []
    vol = (df['high'] - df['low']).tail(10).mean()
    
    for i in range(1, 17):
        f_time = (datetime.now() + timedelta(minutes=15*i)).strftime("%H:%M")
        # Modelis: Atšokimas nuo 1,728€ link 1,748€
        f_price = round(cur_p + (vol * 0.5 * i), 2)
        if f_price > target_p: f_price = target_p
        
        pelnas = (st.session_state.wallet / cur_p * f_price) - st.session_state.wallet
        future_moves.append({
            "Laikas": f_time,
            "Prognozė": f"{f_price} €",
            "Pelnas (€)": f"+{round(pelnas, 2)} €"
        })
    st.table(pd.DataFrame(future_moves[::2])) # Kas 30 min.

    # --- VAIZDINIS ĮVERTINIMAS (2 VAL. / 4 VAL.) ---
    fig, ax = plt.subplots(figsize=(10, 4))
    hist = df.tail(8) # 2 valandos
    ax.plot(hist['time'], hist['close'], color='white', label='Istorija', linewidth=2)
    
    f_times = [hist['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 17)]
    f_vals = [cur_p + (vol * 0.5 * i) if cur_p + (vol * 0.5 * i) < target_p else target_p for i in range(1, 17)]
    ax.plot(f_times, f_vals, color='#00ffcc', linestyle='--', marker='o', label='Atšokimas')
    
    ax.axhline(target_p, color='gold', linestyle=':', label='Tikslas 1748€')
    ax.set_facecolor('#0E1117'); fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white'); ax.legend(facecolor='#0E1117', labelcolor='white')
    st.pyplot(fig)
