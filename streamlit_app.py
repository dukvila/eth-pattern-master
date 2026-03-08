import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
import math
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V174 TITAN STRIKE", layout="wide")
st_autorefresh(interval=30000, key="v174_refresh") # Tikrina kas 30 sek.

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
    
    # AGRESYVI PROGNOZĖ (remiantis paskutinėmis 2 valandomis)
    y = df['close'].tail(8).values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    # Prognozuojame artimiausią atšokimą (po 30 min)
    prediction_next = round(slope * 10 + intercept + (abs(slope) * 2), 2)

    # --- STRATEGINĖS REKOMENDACIJOS ---
    # Perkam šiek tiek žemiau dabartinės, kad pagautumėm "adatą"
    rec_buy = round(cur_p - 1.50, 2) 
    # Parduodam ties prognozuojamu atšokimu (+ ~10€ pelno nuo 1700€ investicijos)
    rec_sell = round(rec_buy + 6.50, 2) 

    st.title(f"⚡ TITAN STRIKE: {round(st.session_state.wallet, 2)}€")
    
    # PROGNOZĖS SKYDELIS
    st.error(f"🎯 DABARTINĖ PROGNOZĖ: Kaina turėtų atšokti iki **{prediction_next}€** per artimiausias 45 min.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("ETH KAINA", f"{cur_p}€")
    col2.metric("REKOMENDUOJAMAS PIRKIMAS", f"{rec_buy}€")
    col3.metric("REKOMENDUOJAMAS PARDAVIMAS", f"{rec_sell}€")

    st.divider()

    # VALDYMO PULTAS
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🚀 Vykdyti operaciją")
        in_buy = st.number_input("Pirkimo kaina (€)", value=rec_buy, key="b_strike")
        in_sell = st.number_input("Pardavimo kaina (€)", value=rec_sell, key="s_strike")
        in_sum = st.number_input("Suma (€)", value=1000.0)
        
        if st.button("🔥 PALEISTI REIDĄ", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.active_trades.append({
                    "buy_p": in_buy, "sell_p": in_sell, "amount": in_sum, 
                    "status": "LAUKIA", "start_p": cur_p
                })
                st.session_state.wallet -= in_sum
                st.rerun()

    with c2:
        # Vizualus prognozės indikatorius
        st.write("📈 **Trendo jėga:**")
        diff = prediction_next - cur_p
        if diff > 0: st.success(f"KYLA (+{round(diff, 2)}€)")
        else: st.warning(f"KRINTA ({round(diff, 2)}€)")

    # GRAFIKAS SU PROGNOZĖS LINIJA
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['time'].tail(30), df['close'].tail(30), color="#1f77b4", label="Kaina")
    ax.axhline(y=in_buy, color='green', linestyle='--', alpha=0.6, label="Tavo Pirkimas")
    ax.axhline(y=in_sell, color='red', linestyle='--', alpha=0.6, label="Tavo Pardavimas")
    # Prognozės taškas
    ax.scatter(df['time'].iloc[-1] + timedelta(minutes=30), prediction_next, color='yellow', zorder=5, label="Prognozė")
    
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    plt.legend()
    st.pyplot(fig)

    # LOGIKA (Vykdymas)
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA" and cur_p <= trade['buy_p']:
            trade['status'] = "🚀 VYKDOMAS"
        if trade['status'] == "🚀 VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "✅ PELNAS"
            st.balloons()
