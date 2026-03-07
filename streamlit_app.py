import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Pagrindinė Konfigūracija
st.set_page_config(page_title="ETH V126 REVOLUT MASTER", layout="wide")
st_autorefresh(interval=60000, key="v126_refresh")

# --- ATMINTIES APSAUGA ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'wallet' not in st.session_state:
    st.session_state.wallet = 200.0  # Pradinė suma pagal tavo nuotrauką
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0

# Švarus perkrovimas
def reset_all():
    st.session_state.trades_log = []
    st.session_state.total_pnl = 0.0
    st.rerun()

# --- ŠONINIS MENIU ---
with st.sidebar:
    st.header("🕹️ Boso Kontrolė")
    st.session_state.wallet = st.number_input("Piniginė (EUR):", value=float(st.session_state.wallet), step=10.0)
    if st.button("🗑️ NULINTI ISTORIJĄ"):
        reset_all()
    st.info("Minimalus pelno tikslas: 10€")

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

# 3. Logika ir skaičiavimai
if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # 4 valandų tendencija (16 žvakių)
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # AUTOMATINIS KLAIDŲ VALYMAS (Ištaiso KeyError iš tavo nuotraukų)
    valid_log = []
    for t in st.session_state.trades_log:
        # Tikriname ar sandoris turi visus reikiamus laukus
        required = ['Laikas', 'Signal', 'Investuota', 'Kaina (Įėjimas)', 'Tikslas']
        if not all(k in t for k in required): continue
            
        if t['Rezultatas'] == "Tikrinama...":
            pelnas = 0.0
            uždaryta = False
            
            if t['Signal'] == "🟢 PIRKTI" and cur_p >= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (cur_p - t['Kaina (Įėjimas)'])
                uždaryta = True
            elif t['Signal'] == "🔴 PARDUOTI" and cur_p <= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (t['Kaina (Įėjimas)'] - cur_p)
                uždaryta = True
            
            if uždaryta:
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_pnl += pelnas
                st.session_state.wallet += pelnas # Reinvestuojame
        valid_log.append(t)
    st.session_state.trades_log = valid_log

    # --- VAIZDAVIMAS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Balansas", f"{round(st.session_state.wallet, 2)}€")
    c2.metric("📈 Pelnas", f"{round(st.session_state.total_pnl, 2)}€")
    c3.metric("⏱️ 4h Trendas", f"{round(trend_4h, 2)} €/15min")

    # Grafikas
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 17)]
    future_prices = [cur_p + (trend_4h * i) for i in range(1, 17)]
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df['time'].tail(25), df['close'].tail(25), label="Dabar", marker='o', markersize=3)
    ax.plot(future_times, future_prices, '--', color='orange', label="4h Prognozė")
    ax.legend()
    st.pyplot(fig)

    # --- 10€ PELNO FILTRAS ---
    predicted_move = abs(trend_4h * 16)
    est_profit = (st.session_state.wallet / cur_p) * predicted_move
    
    signal = "👀 LAUKTI"
    target = cur_p
    
    if est_profit >= 10.0:
        if trend_4h > 0.04:
            signal = "🟢 PIRKTI"
            target = cur_p + predicted_move
        elif trend_4h < -0.04:
            signal = "🔴 PARDUOTI"
            target = cur_p - predicted_move

    # Registracija
    now_t = datetime.now().strftime("%H:%M")
    if st.session_state.wallet > 0 and signal != "👀 LAUKTI":
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Signal": signal,
                "Investuota": round(st.session_state.wallet, 2),
                "Kaina (Įėjimas)": round(cur_p, 2),
                "Tikslas": round(target, 2),
                "Prognozė": f"{round(est_profit, 2)}€",
                "Rezultatas": "Tikrinama..."
            })

    st.subheader("📜 Detali Prekybos Ataskaita")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(15))
    else:
        st.write("Laukiama prognozės su bent 10€ uždarbiu...")
