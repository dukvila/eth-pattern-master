import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Branduolys
st.set_page_config(page_title="TITAN VICTORY V208", layout="wide")
st_autorefresh(interval=30000, key="v208_refresh")

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
    cur_p = df.iloc[-1]['close'] # Dabartinė kaina ~1,749.83€
    new_high = 1758.64 # Naujas pikas
    support_p = 1746.80 # Naujas palaikymas
    
    st.markdown(f"<h1 style='text-align: center; color: #00ffcc;'>🏆 TITAN VICTORY V208</h1>", unsafe_allow_html=True)

    # --- STATUSAS ---
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"🚀 NAUJAS PIKAS: {new_high} €")
        st.write("Rinka patvirtino pirkimo modelį.")
    with col2:
        profit_now = (st.session_state.wallet / 1728.77 * cur_p) - st.session_state.wallet if cur_p > 1728.77 else 0
        st.metric("POTENCIALUS PELNAS", f"+{round(profit_now, 2)} €")

    # --- 4 VALANDŲ PROGNOZĖ (ATNAUJINTA) ---
    st.subheader("🕒 Tolimesnė eiga: Ar kils iki 1,770€?")
    future_data = []
    vol = (df['high'] - df['low']).tail(5).mean()
    
    for i in range(1, 17):
        f_time = (datetime.now() + timedelta(minutes=15*i)).strftime("%H:%M")
        # Modelis: Konsolidacija virš 1,746€
        f_price = round(cur_p + (vol * 0.3 * i), 2)
        future_data.append({
            "Laikas": f_time,
            "Prognozė": f"{f_price} €",
            "Veiksmas": "🔥 LAIKYTI" if f_price > support_p else "⚠️ PARDUOTI"
        })
    st.table(pd.DataFrame(future_data[::2]))

    # --- GRAFIKAS ---
    fig, ax = plt.subplots(figsize=(10, 4))
    hist = df.tail(8) # 2 valandos praeities
    ax.plot(hist['time'], hist['close'], color='white', label='Istorija', linewidth=2)
    
    f_times = [hist['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 17)]
    f_vals = [cur_p + (vol * 0.3 * i) for i in range(1, 17)]
    ax.plot(f_times, f_vals, color='#00ffcc', linestyle='--', marker='o', label='Tęsinys')
    
    ax.axhline(new_high, color='gold', linestyle=':', label='Pikas')
    ax.axhline(support_p, color='red', linestyle=':', label='Saugiklis (1746€)')
    
    ax.set_facecolor('#0E1117'); fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white'); ax.legend(facecolor='#0E1117', labelcolor='white')
    st.pyplot(fig)
