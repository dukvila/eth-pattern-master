import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V117 CEO EDITION", layout="wide")
st_autorefresh(interval=60000, key="v117_refresh")

# --- ATMINTIS (Saugikliai nuo KeyError) ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'wallet' not in st.session_state:
    st.session_state.wallet = 0.0
if 'total_profit' not in st.session_state:
    st.session_state.total_profit = 0.0

st.sidebar.header("🕹️ Boso Kontrolė")
if st.sidebar.button("🗑️ NULINTI VISKĄ"):
    st.session_state.trades_log = []
    st.session_state.wallet = 0.0
    st.session_state.total_profit = 0.0
    st.rerun()

st.sidebar.subheader("💰 Skirti biudžetą")
budget = st.sidebar.number_input("Investicinė suma (€):", value=st.session_state.wallet, step=100.0)
if budget != st.session_state.wallet:
    st.session_state.wallet = budget

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

# 3. Logika ir Veiksmai
if not df.empty:
    cur_p = df.iloc[-1]['close']
    vol = df['close'].tail(15).std()
    
    # 24h Langas (4h istorija + 20h prognozė)
    hist_df = df.tail(16)
    last_time = hist_df.iloc[-1]['time']
    future_times = [last_time + timedelta(minutes=15 * i) for i in range(1, 81)]
    # Tendencijos skaičiavimas
    trend = (df['close'].iloc[-1] - df['close'].iloc[-12]) / 12
    future_prices = [cur_p + (trend * i) for i in range(1, 81)]

    # --- SANDORIŲ TIKRINIMAS (Atskaitomybė) ---
    for t in st.session_state.trades_log:
        if t['Rezultatas'] == "Tikrinama...":
            if t['Signal'] == "🟢 PIRKTI" and cur_p >= t['Parduoti už']:
                diff = cur_p - t['Kaina (Įėjimas)']
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * diff
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_profit += pelnas
            elif t['Signal'] == "🔴 PARDUOTI" and cur_p <= t['Parduoti už']:
                diff = t['Kaina (Įėjimas)'] - cur_p
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * diff
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_profit += pelnas
            elif abs(cur_p - t['Kaina (Įėjimas)']) > (vol * 3): # Stop Loss
                nuostolis = -2.0 # Supaprastintas nuostolis
                t['Rezultatas'] = "❌ NUOSTOLIS"
                st.session_state.total_profit += nuostolis

    # --- VAIZDAVIMAS ---
    st.header(f"💼 Balansas: {round(st.session_state.wallet, 2)}€")
    st.metric("📈 Bendras Uždarbis", f"{round(st.session_state.total_profit, 2)}€")
    
    st.write(f"🕒 Lietuvos laikas: {datetime.now().strftime('%H:%M:%S')} | ETH: {cur_p:.2f}€")

    # Grafikas
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(hist_df['time'], hist_df['close'], color='#1f77b4', label='Istorija (4h)', marker='o', markersize=3)
    ax.plot(future_times, future_prices, color='#ff7f0e', linestyle='--', label='Prognozė (20h)')
    ax.set_facecolor('#f9f9f9')
    ax.legend()
    st.pyplot(fig)

    # Tikslingas pirkimas/pardavimas
    signal = "🟢 PIRKTI" if trend > 0.1 else "🔴 PARDUOTI"
    if abs(trend) < 0.05: signal = "STEBĖTI" # Neliečiame pinigų, jei nėra aišku

    now_t = datetime.now().strftime("%H:%M")
    if st.session_state.wallet > 0 and signal != "STEBĖTI":
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            target = cur_p + (vol * 2) if signal == "🟢 PIRKTI" else cur_p - (vol * 2)
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Signal": signal,
                "Investuota": round(st.session_state.wallet, 2),
                "Kaina (Įėjimas)": round(cur_p, 2),
                "Parduoti už": round(target, 2),
                "Rezultatas": "Tikrinama..."
            })

    st.subheader("📜 Detali Prekybos Ataskaita")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(10))
