import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V113 24H-PREDICT", layout="wide")
st_autorefresh(interval=60000, key="v113_refresh")

# --- SISTEMOS VALYMAS IR PRADINIS BIUDŽETAS ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'balance' not in st.session_state:
    st.session_state.balance = 0.0  # Pradedame nuo nulio, kol neįvesi sumos

st.sidebar.header("⚙️ Nustatymai")
if st.sidebar.button("🗑️ Išvalyti visą žurnalą (NULINTI)"):
    st.session_state.trades_log = []
    st.session_state.balance = 0.0
    st.rerun()

st.sidebar.subheader("💰 Tavo Biudžetas")
user_sum = st.sidebar.number_input("Įvesk pradinę sumą (€):", value=st.session_state.balance, step=100.0)
if user_sum != st.session_state.balance:
    st.session_state.balance = user_sum

# 2. Duomenų gavimas (Kraken API)
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
    except: return pd.DataFrame()

df = get_data()

# 3. Strategija ir 24h Prognozė
if not df.empty:
    cur_p = df.iloc[-1]['close']
    vol = df['close'].tail(10).std()
    
    # 24h Prognozės kūrimas (4h istorija + 20h ateitis)
    hist_4h = df.tail(16) # 16 žvakių po 15min = 4h
    last_time = hist_4h.iloc[-1]['time']
    
    future_times = [last_time + timedelta(minutes=15 * i) for i in range(1, 81)] # 20h ateitis
    trend = (df['close'].iloc[-1] - df['close'].iloc[-10]) / 10
    future_prices = [cur_p + (trend * i) for i in range(1, 81)]
    
    # Signalo nustatymas
    signal = "STEBĖTI"
    if df.iloc[-1]['close'] > df.iloc[-1]['open']: signal = "🟢 PIRKTI"
    elif df.iloc[-1]['close'] < df.iloc[-1]['open']: signal = "🔴 PARDUOTI"

    # --- VAIZDAVIMAS ---
    st.header(f"💼 Balansas: {round(st.session_state.balance, 2)}€")
    
    # Viršutinė info juosta
    st.info(f"🕒 Realus laikas: {datetime.now().strftime('%H:%M:%S')} | ETH Kaina: {cur_p:.2f}€")

    # 24 Valandų Grafikas
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(hist_4h['time'], hist_4h['close'], color='white', label='Istorija (4h)', linewidth=2)
    ax.plot(future_times, future_prices, color='#00ffcc', linestyle='--', label='Prognozė (20h)', alpha=0.6)
    
    ax.set_facecolor('#1e1e1e')
    fig.patch.set_facecolor('#1e1e1e')
    ax.tick_params(colors='white')
    ax.legend()
    st.pyplot(fig)

    # Prekybos operacija
    now_t = datetime.now().strftime("%H:%M")
    if signal != "STEBĖTI" and st.session_state.balance > 0:
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            invest = st.session_state.balance
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Signal": signal,
                "Investuota": round(invest, 2),
                "Kaina": round(cur_p, 2),
                "Rezultatas": "Tikrinama..."
            })

    # Ataskaita
    st.write("### 📜 Detali Prekybos Ataskaita")
    if st.session_state.trades_log:
        log_df = pd.DataFrame(st.session_state.trades_log)
        st.table(log_df.head(10))
    else:
        st.write("Laukiama pirmojo signalo su tavo nustatytu biud
