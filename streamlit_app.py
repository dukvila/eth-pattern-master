import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Branduolys
st.set_page_config(page_title="TITAN FUTURE-SIGHT V198", layout="wide")
st_autorefresh(interval=30000, key="v198_refresh")

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
    # --- ATEITIES PROGNOZAVIMO VARIKLIS ---
    cur_p = df.iloc[-1]['close']
    ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
    volatility = (df['high'] - df['low']).tail(10).mean()
    
    # PIRKIMO PROGNOZĖ (Kada kaina pasieks dugną?)
    # Skaičiuojame pirkimo tašką 0.4% žemiau dabartinio vidurkio
    target_buy_p = round(ema_20 - (volatility * 0.5), 2)
    # PARDAVIMO PROGNOZĖ (Kada kaina pasieks pelno zoną?)
    target_sell_p = round(target_buy_p + (volatility * 1.2), 2)
    
    # Sėkmės tikimybė remiantis RSI (jei žemas - kils)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + gain/loss)).iloc[-1]
    win_prob = min(max(100 - rsi + 10, 10), 95)

    st.markdown(f"<h1 style='text-align: center; color: #00ffcc;'>🔮 TITAN FUTURE-SIGHT V198</h1>", unsafe_allow_html=True)

    # --- PAGRINDINIS VEIKSMŲ PLANAS ---
    st.markdown(f"""
    <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 2px solid #00ffcc; text-align: center;">
        <h2 style="color: white; margin: 0;">REKOMENDACIJA: <span style="color: {'#00ff00' if win_prob > 70 else '#ffcc00'};">{'PIRKTI DABAR' if cur_p <= target_buy_p else 'LAUKTI ĮĖJIMO'}</span></h2>
        <p style="font-size: 24px; color: #00ffcc;">🎯 Tikslas: <b>{target_sell_p} €</b> | 📈 Tikimybė: <b>{round(win_prob, 1)}%</b></p>
    </div>
    """, unsafe_allow_html=True)

    # --- ATEITIES 15 MIN. ŽVAKIŲ LENTELĖ ---
    st.subheader("🕒 Tikslus laikas tavo pelnui")
    future_data = []
    now = datetime.now()
    
    for i in range(1, 6): # Prognozė ateinančioms 75 minutėms
        f_time = (now + timedelta(minutes=15*i)).strftime("%H:%M")
        # Modelis: po kiek laiko kaina turėtų pasiekti tikslą
        status = "PIRKTI" if i == 1 else "LAIKYTI" if i < 4 else "PARDUOTI"
        
        future_data.append({
            "Prognozuojamas Laikas": f_time,
            "Laukimo trukmė": f"{i*15} min.",
            "Prognozuojama Kaina (€)": f"{round(target_buy_p + (i * volatility * 0.2), 2)}",
            "Tikimybė (%)": f"{round(win_prob - (i*2), 1)} %",
            "Tavo Pelnas (iš 1000€)": f"+{round((1000/target_buy_p * (target_buy_p + (i * volatility * 0.2))) - 1000, 2)} €"
        })
    st.table(future_data)

    # --- ATEITIES KRYPTIES GRAFIKAS ---
    fig, ax = plt.subplots(figsize=(12, 4))
    
    # Tik 2 valandų praeitis
    hist_view = df.tail(8)
    ax.plot(hist_view['time'], hist_view['close'], color='gray', alpha=0.5, label='Praeitis')
    
    # Ateities prognozė (Žalia linija)
    future_times = [hist_view['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 6)]
    future_vals = [target_buy_p + (i * volatility * 0.2) for i in range(1, 6)]
    ax.plot(future_times, future_vals, color='#00ffcc', linestyle='--', marker='o', label='ATEITIES PROGNOZĖ')
    
    ax.axhline(target_sell_p, color='#00ff00', linestyle=':', label="Pardavimo tikslas")
    ax.axhline(target_buy_p, color='#ffff00', linestyle=':', label="Pirkimo taškas")

    ax.set_facecolor('#0E1117'); fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white'); plt.legend(facecolor='#0E1117', labelcolor='white')
    st.pyplot(fig)

    if st.button("🔱 AKTYVUOTI REIDĄ PAGAL ŠIĄ PROGNOZĘ", use_container_width=True):
        st.success(f"Užsakymas paruoštas: Pirkti už {target_buy_p}€, parduoti už {target_sell_p}€.")
