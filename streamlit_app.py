import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V124 10€ PROFIT", layout="wide")
st_autorefresh(interval=60000, key="v124_refresh")

# --- ATMINTIES VALDYMAS (Su Reinvestavimu) ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'wallet' not in st.session_state:
    st.session_state.wallet = 1000.0 
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0

def reset_all():
    st.session_state.trades_log = []
    st.session_state.total_pnl = 0.0
    st.rerun()

st.sidebar.header("🕹️ Boso Kontrolė")
st.session_state.wallet = st.sidebar.number_input("Piniginė (EUR):", value=float(st.session_state.wallet), step=50.0)
if st.sidebar.button("🗑️ NULINTI ISTORIJĄ"):
    reset_all()

# 2. Rinkos Duomenys
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

# 3. Strateginis Skaičiavimas
if not df.empty:
    cur_p = df.iloc[-1]['close']
    vol = df['close'].tail(15).std()
    
    # 4 valandų (16 žingsnių po 15min) tendencijos analizė
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # Tikriname aktyvius sandorius
    updated_log = []
    for t in st.session_state.trades_log:
        if t['Rezultatas'] == "⏳ Tikrinama...":
            uždaryta = False
            pelnas = 0.0
            
            # Pirkimo pelno fiksavimas (Parduodame brangiau)
            if t['Veiksmas'] == "🟢 PIRKTI" and cur_p >= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (cur_p - t['Kaina (Įėjimas)'])
                uždaryta = True
            # Pardavimo pelno fiksavimas (Atperkame pigiau)
            elif t['Veiksmas'] == "🔴 PARDUOTI" and cur_p <= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (t['Kaina (Įėjimas)'] - cur_p)
                uždaryta = True
            
            if uždaryta:
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_pnl += pelnas
                st.session_state.wallet += pelnas # AUTOMATINIS REINVESTAVIMAS
        updated_log.append(t)
    st.session_state.trades_log = updated_log

    # --- VAIZDAVIMAS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Balansas (Reinvestuotas)", f"{round(st.session_state.wallet, 2)}€")
    c2.metric("📈 Sukauptas Pelnas", f"{round(st.session_state.total_pnl, 2)}€")
    c3.metric("⏱️ 4h Trendas", f"{round(trend_4h, 2)} €/15min")

    # Prognozės grafikas
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 17)]
    future_prices = [cur_p + (trend_4h * i) for i in range(1, 17)]
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df['time'].tail(20), df['close'].tail(20), label="Dabar")
    ax.plot(future_times, future_prices, '--', color='orange', label="4h Prognozė")
    ax.legend()
    st.pyplot(fig)

    # --- INTELEKTUALI ĮĖJIMO LOGIKA ---
    # Skaičiuojame prognozuojamą pelną (kiek uždirbsime, jei trendas išsilaikys 4 valandas)
    predicted_move = abs(trend_4h * 16)
    potential_profit = (st.session_state.wallet / cur_p) * predicted_move
    
    signal = "👀 LAUKTI (Mažas pelnas)"
    target = cur_p
    
    # Tikriname 10€ taisyklę
    if potential_profit >= 10.0:
        if trend_4h > 0.04:
            signal = "🟢 PIRKTI"
            target = cur_p + predicted_move
        elif trend_4h < -0.04:
            signal = "🔴 PARDUOTI"
            target = cur_p - predicted_move

    now_t = datetime.now().strftime("%H:%M")
    if st.session_state.wallet > 0 and "LAUKTI" not in signal:
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Veiksmas": signal,
                "Investuota": round(st.session_state.wallet, 2),
                "Kaina (Įėjimas)": round(cur_p, 2),
                "Tikslas": round(target, 2),
                "Prognoz. Pelnas": f"{round(potential_profit, 2)}€",
                "Rezultatas": "⏳ Tikrinama..."
            })

    st.subheader("📜 Boso Sandorių Žurnalas")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(10))
