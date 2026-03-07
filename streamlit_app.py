import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V120 PROFIT LOGIC", layout="wide")
st_autorefresh(interval=60000, key="v120_refresh")

# --- ATMINTIES VALDYMAS (Saugikliai) ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'wallet' not in st.session_state:
    st.session_state.wallet = 0.0
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0

st.sidebar.header("🕹️ Boso Valdymas")
if st.sidebar.button("🗑️ NULINTI VISKĄ (IŠVALYTI KLAIDAS)"):
    st.session_state.trades_log = []
    st.session_state.wallet = 0.0
    st.session_state.total_pnl = 0.0
    st.rerun()

st.sidebar.subheader("💰 Tavo Investicija")
user_sum = st.sidebar.number_input("Pradinė suma (€):", value=float(st.session_state.wallet), step=100.0)
if user_sum != st.session_state.wallet:
    st.session_state.wallet = user_sum

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

# 3. Darbas ir Atskaitomybė
if not df.empty:
    cur_p = df.iloc[-1]['close']
    vol = df['close'].tail(15).std()
    
    # 24h Prognozė
    hist_df = df.tail(16)
    trend = (df['close'].iloc[-1] - df['close'].iloc[-12]) / 12
    future_times = [hist_df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 81)]
    future_prices = [cur_p + (trend * i) for i in range(1, 81)]

    # --- PELNO FIKSAVIMO LOGIKA ---
    active_log = []
    for t in st.session_state.trades_log:
        if t['Rezultatas'] == "Tikrinama...":
            pelnas = 0.0
            uždaryta = False
            
            # Žalias signalas: Uždirbame, kai kaina kyla virš pirkimo kainos
            if t['Signal'] == "🟢 PIRKTI" and cur_p >= t['Tikslas (Profit)']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (cur_p - t['Kaina (Įėjimas)'])
                uždaryta = True
            # Raudonas signalas: Uždirbame, kai kaina krenta žemiau pardavimo kainos
            elif t['Signal'] == "🔴 PARDUOTI" and cur_p <= t['Tikslas (Profit)']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (t['Kaina (Įėjimas)'] - cur_p)
                uždaryta = True
            
            if uždaryta:
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_pnl += pelnas
                st.session_state.wallet += pelnas
        active_log.append(t)
    st.session_state.trades_log = active_log

    # --- VAIZDAVIMAS ---
    c1, c2 = st.columns(2)
    c1.metric("💼 Piniginėje", f"{round(st.session_state.wallet, 2)}€")
    c2.metric("📈 Uždirbta tau", f"{round(st.session_state.total_pnl, 2)}€")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(hist_df['time'], hist_df['close'], color='#1f77b4', label='Istorija', marker='o', markersize=3)
    ax.plot(future_times, future_prices, color='#ff7f0e', linestyle='--', label='Prognozė')
    ax.legend()
    st.pyplot(fig)

    # Strateginis sprendimas
    signal = "🟢 PIRKTI" if trend > 0.05 else "🔴 PARDUOTI"
    if abs(trend) < 0.02: signal = "LAUKTI"

    now_t = datetime.now().strftime("%H:%M")
    if st.session_state.wallet > 0 and signal != "LAUKTI":
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            # Jei Parduodame (short), tikslas yra ŽEMESNĖ kaina
            target = cur_p + (vol * 2.0) if signal == "🟢 PIRKTI" else cur_p - (vol * 2.0)
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Signal": signal,
                "Investuota": round(st.session_state.wallet, 2),
                "Kaina (Įėjimas)": round(cur_p, 2),
                "Tikslas (Profit)": round(target, 2),
                "Rezultatas": "Tikrinama..."
            })

    st.subheader("📊 Verslo Ataskaita (Kaip aš tau uždirbu)")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(10))
