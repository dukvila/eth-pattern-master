import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V114 CLEAN RESTART", layout="wide")
st_autorefresh(interval=60000, key="v114_refresh")

# --- VISIŠKAS NULINIMAS IR ATMINTIS ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'balance' not in st.session_state:
    st.session_state.balance = 0.0  # Pradedame nuo nulio

st.sidebar.header("⚙️ Valdymas")
if st.sidebar.button("🗑️ IŠVALYTI VISKĄ (NULINTI)"):
    st.session_state.trades_log = []
    st.session_state.balance = 0.0
    st.rerun()

st.sidebar.subheader("💰 Piniginė")
user_sum = st.sidebar.number_input("Įvesk savo pradinę sumą (€):", value=st.session_state.balance, step=100.0)
if user_sum != st.session_state.balance:
    st.session_state.balance = user_sum

# 2. Duomenų gavimas
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2) # Lietuvos laikas
            return df
    except:
        return pd.DataFrame()

df = get_data()

# 3. Logika ir 24 valandų prognozė
if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # Grafiko paruošimas: 4h istorija + 20h ateitis
    hist_4h = df.tail(16) # 16 žvakių po 15min = 4h
    last_time = hist_4h.iloc[-1]['time']
    
    # Paprasta tendencijos prognozė likusiai parai (20h)
    future_times = [last_time + timedelta(minutes=15 * i) for i in range(1, 81)]
    trend = (df['close'].iloc[-1] - df['close'].iloc[-20]) / 20
    future_prices = [cur_p + (trend * i) for i in range(1, 81)]

    # --- VAIZDAVIMAS ---
    st.header(f"💼 Balansas: {round(st.session_state.balance, 2)}€")
    st.info(f"🕒 Laikas: {datetime.now().strftime('%H:%M:%S')} | Kaina: {cur_p:.2f}€")

    # 24 Valandų Grafikas (4h tikra kaina | 20h prognozė)
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(hist_4h['time'], hist_4h['close'], color='#1f77b4', label='Istorija (4h)', marker='o', markersize=4)
    ax.plot(future_times, future_prices, color='#ff7f0e', linestyle='--', label='Prognozė (Ateitis)')
    
    ax.set_facecolor('#f0f2f6')
    ax.legend()
    st.pyplot(fig)

    # Prekybos signalas (tik jei yra biudžetas)
    signal = "🟢 PIRKTI" if df.iloc[-1]['close'] > df.iloc[-1]['open'] else "🔴 PARDUOTI"
    now_t = datetime.now().strftime("%H:%M")

    if st.session_state.balance > 0:
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Signal": signal,
                "Investuota": round(st.session_state.balance, 2),
                "Kaina (Įėjimas)": round(cur_p, 2),
                "Rezultatas": "Tikrinama..."
            })

    # Ataskaitos lentelė
    st.write("### 📜 Prekybos Žurnalas")
    if st.session_state.trades_log:
        log_df = pd.DataFrame(st.session_state.trades_log)
        st.table(log_df.head(10))
    else:
        st.warning("Laukiama pirmojo signal
