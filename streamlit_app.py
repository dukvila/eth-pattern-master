import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V121 ULTIMATE", layout="wide")
st_autorefresh(interval=60000, key="v121_refresh")

# --- ATMINTIES VALDYMAS ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'wallet' not in st.session_state:
    st.session_state.wallet = 0.0
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0

st.sidebar.header("🕹️ Valdymas")
if st.sidebar.button("🗑️ NULINTI VISKĄ (IŠVALYTI KLAIDAS)"):
    st.session_state.trades_log = []
    st.session_state.wallet = 0.0
    st.session_state.total_pnl = 0.0
    st.rerun()

user_sum = st.sidebar.number_input("Tavo biudžetas (€):", value=float(st.session_state.wallet), step=100.0)
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

# 3. Prekybos Logika
if not df.empty:
    cur_p = df.iloc[-1]['close']
    vol = df['close'].tail(15).std()
    
    # Tikriname senus sandorius (Saugiklis nuo KeyError)
    valid_log = []
    for t in st.session_state.trades_log:
        if 'Tikslas' not in t or 'Kaina (Pradinė)' not in t: continue # Praleidžiame klaidingus senus sandorius
        
        if t['Rezultatas'] == "Tikrinama...":
            uždaryta = False
            pelnas = 0.0
            if t['Veiksmas'] == "📈 KILIMAS" and cur_p >= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Pradinė)']) * (cur_p - t['Kaina (Pradinė)'])
                uždaryta = True
            elif t['Veiksmas'] == "📉 KRITIMAS" and cur_p <= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Pradinė)']) * (t['Kaina (Pradinė)'] - cur_p)
                uždaryta = True
            
            if uždaryta:
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_pnl += pelnas
                st.session_state.wallet += pelnas
        valid_log.append(t)
    st.session_state.trades_log = valid_log

    # --- VAIZDAVIMAS ---
    col1, col2 = st.columns(2)
    col1.metric("💰 Laisvi pinigai", f"{round(st.session_state.wallet, 2)}€")
    col2.metric("📈 Uždirbtas Pelno Fondas", f"{round(st.session_state.total_pnl, 2)}€")

    # Prognozės grafikas
    trend = (df['close'].iloc[-1] - df['close'].iloc[-12]) / 12
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df['time'].tail(20), df['close'].tail(20), label="Kaina", marker='o')
    ax.set_title("ETH Tendencija")
    st.pyplot(fig)

    # Naujo sandorio atidarymas
    veiksmas = "📈 KILIMAS" if trend > 0.05 else "📉 KRITIMAS"
    if abs(trend) < 0.02: veiksmas = "LAUKTI"

    if st.session_state.wallet > 0 and veiksmas != "LAUKTI":
        now_t = datetime.now().strftime("%H:%M")
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            target = cur_p + (vol * 2) if veiksmas == "📈 KILIMAS" else cur_p - (vol * 2)
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Veiksmas": veiksmas,
                "Investuota": round(st.session_state.wallet, 2),
                "Kaina (Pradinė)": round(cur_p, 2),
                "Tikslas": round(target, 2),
                "Rezultatas": "Tikrinama..."
            })

    st.subheader("📋 Tavo Pelno Ataskaita")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(10))
