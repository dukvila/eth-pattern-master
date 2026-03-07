import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V116 PRO-RESPONSIBILITY", layout="wide")
st_autorefresh(interval=60000, key="v116_refresh")

# --- ATMINTIES VALDYMAS (Tavo Piniginė) ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0
if 'balance' not in st.session_state:
    st.session_state.balance = 0.0

st.sidebar.header("💼 Boso Valdymas")
if st.sidebar.button("🗑️ NULINTI VISKĄ IR PRADĖTI IŠ NAUJO"):
    st.session_state.trades_log = []
    st.session_state.total_pnl = 0.0
    st.session_state.balance = 0.0
    st.rerun()

st.sidebar.subheader("💰 Skirti biudžetą")
start_sum = st.sidebar.number_input("Investicijų suma (€):", value=st.session_state.balance, step=100.0)
if start_sum != st.session_state.balance:
    st.session_state.balance = start_sum

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

# 3. Profesionali Logika
if not df.empty:
    cur_p = df.iloc[-1]['close']
    vol = df['close'].tail(15).std()
    
    # 24h Langas (4h istorija + 20h prognozė)
    hist_df = df.tail(16)
    last_time = hist_df.iloc[-1]['time']
    future_times = [last_time + timedelta(minutes=15 * i) for i in range(1, 81)]
    trend = (df['close'].iloc[-1] - df['close'].iloc[-12]) / 12
    future_prices = [cur_p + (trend * i) for i in range(1, 81)]

    # --- ATSAKOMYBĖ: Tikriname sandorius ---
    for t in st.session_state.trades_log:
        if t['Rezultatas'] == "Tikrinama...":
            # Jei PIRKOME (tikimės kilimo)
            if t['Signal'] == "🟢 PIRKTI":
                if cur_p >= t['Parduoti už']:
                    pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (cur_p - t['Kaina (Įėjimas)'])
                    t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                    st.session_state.total_pnl += pelnas
                elif cur_p <= t['Stop Loss']:
                    nuostolis = (t['Investuota'] / t['Kaina (Įėjimas)']) * (cur_p - t['Kaina (Įėjimas)'])
                    t['Rezultatas'] = f"❌ {round(nuostolis, 2)}€"
                    st.session_state.total_pnl += nuostolis
            # Jei PARDAVĖME (tikimės kritimo)
            elif t['Signal'] == "🔴 PARDUOTI":
                if cur_p <= t['Parduoti už']:
                    pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (t['Kaina (Įėjimas)'] - cur_p)
                    t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                    st.session_state.total_pnl += pelnas

    # --- VAIZDAVIMAS ---
    c1, c2 = st.columns(2)
    c1.metric("💰 Turimas biudžetas", f"{round(st.session_state.balance, 2)}€")
    c2.metric("📈 Bendras Pelno/Nuostolio santykis", f"{round(st.session_state.total_pnl, 2)}€", delta=f"{round(st.session_state.total_pnl, 2)}€")

    st.write(f"🕒 Lietuvos laikas: {datetime.now().strftime('%H:%M:%S')} | ETH: {cur_p:.2f}€")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(hist_df['time'], hist_df['close'], color='#1f77b4', label='Istorija (4h)', marker='o', markersize=3)
    ax.plot(future_times, future_prices, color='#ff7f0e', linestyle='--', label='Prognozė (20h)')
    ax.set_facecolor('#f9f9f9')
    ax.legend()
    st.pyplot(fig)

    # Signalas tik su logika (jei prognozė rodo kritimą, bet RSI sveikas - parduodame short)
    signal = "🟢 PIRKTI" if trend > 0 else "🔴 PARDUOTI"
    now_t = datetime.now().strftime("%H:%M")

    if st.session_state.balance > 0:
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            target_price = cur_p + (vol * 2) if signal == "🟢 PIRKTI" else cur_p - (vol * 2)
            stop_price = cur_p - (vol * 1.5) if signal == "🟢 PIRKTI" else cur_p + (vol * 1.5)
            
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Signal": signal,
                "Investuota": round(st.session_state.balance, 2),
                "Kaina (Įėjimas)": round(cur_p, 2),
                "Parduoti už": round(target_price, 2), # Tavo prašytas "pardavimo" nustatymas
                "Stop Loss": round(stop_price, 2),
                "Rezultatas": "Tikrinama..."
            })

    st.subheader("📜 Atskaitomybės Žurnalas (Boso patikrai)")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(15))
