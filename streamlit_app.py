import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V127 BULL ONLY", layout="wide")
st_autorefresh(interval=60000, key="v127_refresh")

# --- ATMINTIES VALDYMAS ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'wallet' not in st.session_state:
    st.session_state.wallet = 300.0  # Tavo pradinis biudžetas
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0

def reset_all():
    st.session_state.trades_log = []
    st.session_state.total_pnl = 0.0
    st.rerun()

# --- ŠONINIS MENIU ---
with st.sidebar:
    st.header("🕹️ Revolut X Kontrolė")
    st.session_state.wallet = st.number_input("Piniginė (EUR):", value=float(st.session_state.wallet), step=10.0)
    if st.button("🗑️ NULINTI VISKĄ"):
        reset_all()
    st.success("Strategija: TIK AUGIMAS 📈")
    st.info("Minimalus pelnas: 10€")

# 2. Duomenų gavimas
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

# 3. Logika (Tik Augimas)
if not df.empty:
    cur_p = df.iloc[-1]['close']
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # Ištaisome KeyError ir tikriname sandorius
    valid_log = []
    for t in st.session_state.trades_log:
        if not all(k in t for k in ['Laikas', 'Veiksmas', 'Investuota', 'Pirkti už', 'Tikslas (Pelnas)']):
            continue
            
        if t['Rezultatas'] == "⏳ Tikrinama...":
            if cur_p >= t['Tikslas (Pelnas)']:
                pelnas = (t['Investuota'] / t['Pirkti už']) * (cur_p - t['Pirkti už'])
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_pnl += pelnas
                st.session_state.wallet += pelnas
        valid_log.append(t)
    st.session_state.trades_log = valid_log

    # --- VAIZDAVIMAS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Balansas", f"{round(st.session_state.wallet, 2)}€")
    c2.metric("📈 Sukauptas Pelnas", f"{round(st.session_state.total_pnl, 2)}€")
    c3.metric("⏱️ Dabartinė Kaina", f"{round(cur_p, 2)}€")

    # Augimo Grafikas
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df['time'].tail(25), df['close'].tail(25), label="ETH Kaina", marker='o', markersize=3)
    if trend_4h > 0:
        future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 17)]
        future_prices = [cur_p + (trend_4h * i) for i in range(1, 17)]
        ax.plot(future_times, future_prices, '--', color='green', label="Augimo Prognozė")
    ax.legend()
    st.pyplot(fig)

    # --- TIK AUGIMO FILTRAS ---
    predicted_rise = trend_4h * 16
    potential_profit = (st.session_state.wallet / cur_p) * predicted_rise
    
    # Tikriname: ar kils IR ar pelnas bus > 10€
    if trend_4h > 0.05 and potential_profit >= 10.0:
        signal = "🟢 PIRKTI (AUGIMAS)"
        target = cur_p + predicted_rise
        
        now_t = datetime.now().strftime("%H:%M")
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Veiksmas": signal,
                "Investuota": round(st.session_state.wallet, 2),
                "Pirkti už": round(cur_p, 2),
                "Tikslas (Pelnas)": round(target, 2),
                "Prognozė": f"+{round(potential_profit, 2)}€",
                "Rezultatas": "⏳ Tikrinama..."
            })

    st.subheader("📜 Revolut X Sandorių Žurnalas")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(10))
    else:
        st.info("Laukiama prognozuojamo kainos kilimo, kuris atneštų bent 10€ pelną.")
