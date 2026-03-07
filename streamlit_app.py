import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V115 24H-STABLE", layout="wide")
st_autorefresh(interval=60000, key="v115_refresh")

# --- ATMINTIES VALDYMAS (Saugiklis nuo klaidų) ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'balance' not in st.session_state:
    st.session_state.balance = 0.0

# Šoninė juosta nustatymams
st.sidebar.header("⚙️ Nustatymai")
if st.sidebar.button("🗑️ NULINTI VISKĄ"):
    st.session_state.trades_log = []
    st.session_state.balance = 0.0
    st.rerun()

st.sidebar.subheader("💰 Piniginė")
new_bal = st.sidebar.number_input("Tavo pradinė suma (€):", value=st.session_state.balance, step=100.0)
if new_bal != st.session_state.balance:
    st.session_state.balance = new_bal

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
    except:
        return pd.DataFrame()

df = get_data()

# 3. Logika ir 24h Prognozė
if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # 24h Langas (4h istorija + 20h ateitis)
    hist_df = df.tail(16) # 4 valandos istorijos
    last_time = hist_df.iloc[-1]['time']
    
    # Ateities prognozė (20h)
    future_times = [last_time + timedelta(minutes=15 * i) for i in range(1, 81)]
    # Apskaičiuojame tendenciją pagal paskutines 2 valandas
    trend = (df['close'].iloc[-1] - df['close'].iloc[-8]) / 8
    future_prices = [cur_p + (trend * i) for i in range(1, 81)]

    # --- VAIZDAVIMAS ---
    st.title(f"💼 Balansas: {round(st.session_state.balance, 2)}€")
    st.write(f"🕒 Lietuvos laikas: {datetime.now().strftime('%H:%M:%S')} | ETH: {cur_p:.2f}€")

    # Grafikas
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(hist_df['time'], hist_df['close'], color='#1f77b4', label='Istorija (4h)', marker='o', markersize=4)
    ax.plot(future_times, future_prices, color='#ff7f0e', linestyle='--', label='Prognozė (20h)')
    ax.set_facecolor('#f9f9f9')
    ax.legend()
    st.pyplot(fig)

    # Prekybos signalas
    signal = "🟢 PIRKTI" if df.iloc[-1]['close'] > df.iloc[-1]['open'] else "🔴 PARDUOTI"
    now_t = datetime.now().strftime("%H:%M")

    # Automatinis žurnalo pildymas (tik jei biudžetas > 0)
    if st.session_state.balance > 0:
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Signal": signal,
                "Investuota": round(st.session_state.balance, 2),
                "Kaina (Įėjimas)": round(cur_p, 2),
                "Rezultatas": "Tikrinama..."
            })

    # Ataskaita
    st.subheader("📜 Prekybos Žurnalos Ataskaita")
    if st.session_state.trades_log:
        log_df = pd.DataFrame(st.session_state.trades_log)
        # Saugus stulpelių rodymas (prevencija KeyError)
        cols = ["Laikas", "Signal", "Investuota", "Kaina (Įėjimas)", "Rezultatas"]
        st.table(log_df[cols].head(10))
    else:
        st.info("Laukiama pirmojo signalo. Nustatykite biudžetą šoninėje juostoje.")
