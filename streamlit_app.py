import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Pagrindinė Konfigūracija
st.set_page_config(page_title="ETH V123 REVOLUT X", layout="wide")
st_autorefresh(interval=60000, key="v123_refresh")

# --- ATMINTIES VALDYMAS (Saugiklis nuo klaidų) ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'wallet' not in st.session_state:
    st.session_state.wallet = 1000.0  # Pradinis boso biudžetas
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0

# Funkcija švariam restartui (ištaiso KeyError)
def reset_system():
    st.session_state.trades_log = []
    st.session_state.total_pnl = 0.0
    st.rerun()

# 2. Šoninis Meniu (Duomenų įvedimas)
with st.sidebar:
    st.header("🕹️ Revolut X Kontrolė")
    new_wallet = st.number_input("Tavo Piniginė (€):", value=float(st.session_state.wallet), step=50.0)
    st.session_state.wallet = new_wallet
    
    if st.button("🗑️ IŠVALYTI VISĄ ISTORIJĄ"):
        reset_system()
    
    st.info("Ši programa analizuoja rinką ir prognozuoja, kada tau geriausia atlikti mainus Revolut X platformoje.")

# 3. Rinkos Duomenų Gavimas
def get_kraken_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            data = res['result']['XETHZEUR'][-100:]
            df = pd.DataFrame(data, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except:
        return pd.DataFrame()

df = get_kraken_data()

# 4. Analizė ir Veiksmai
if not df.empty:
    current_price = df.iloc[-1]['close']
    volatility = df['close'].tail(15).std()
    
    # Tikriname esamus sandorius (Apsauga nuo KeyError)
    updated_log = []
    for t in st.session_state.trades_log:
        # Praleidžiame senus, nesuderinamus įrašus
        if 'Tikslas' not in t or 'Veiksmas' not in t:
            continue
            
        if t['Rezultatas'] == "⏳ Tikrinama...":
            pelnas = 0.0
            uždaryta = False
            
            # Pirkimo logika (Uždirbame kilant)
            if t['Veiksmas'] == "🟢 PIRKTI" and current_price >= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (current_price - t['Kaina (Įėjimas)'])
                uždaryta = True
            # Pardavimo logika (Uždirbame krentant - Revolut X Spot stiliaus)
            elif t['Veiksmas'] == "🔴 PARDUOTI" and current_price <= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (t['Kaina (Įėjimas)'] - current_price)
                uždaryta = True
            
            if uždaryta:
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_pnl += pelnas
                st.session_state.wallet += pelnas
                
        updated_log.append(t)
    st.session_state.trades_log = updated_log

    # --- VAIZDINĖ ATASKAITA ---
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Balansas", f"{round(st.session_state.wallet, 2)}€")
    col2.metric("📈 Bendras Pelnas", f"{round(st.session_state.total_pnl, 2)}€")
    col3.metric("💎 ETH Kaina", f"{round(current_price, 2)}€")

    # Prognozės grafikas
    trend = (df['close'].iloc[-1] - df['close'].iloc[-12]) / 12
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 41)]
    future_prices = [current_price + (trend * i) for i in range(1, 41)]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['time'].tail(30), df['close'].tail(30), label="Istorinė kaina", marker='o', markersize=3)
    ax.plot(future_times, future_prices, label="Prognozė", linestyle='--', color='orange')
    ax.set_title("ETH/EUR Tendencijų Analizė")
    ax.legend()
    st.pyplot(fig)

    # Signalų generavimas pritaikytas Revolut X
    signal = "🟢 PIRKTI" if trend > 0.06 else "🔴 PARDUOTI"
    if abs(trend) < 0.03: signal = "👀 STEBĖTI"

    now_t = datetime.now().strftime("%H:%M")
    if st.session_state.wallet > 0 and signal != "👀 STEBĖTI":
        # Tikriname, ar šią minutę dar nebuvo sugeneruotas signalas
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            target_price = current_price + (volatility * 2) if signal == "🟢 PIRKTI" else current_price - (volatility * 2)
            
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Veiksmas": signal,
                "Investuota": round(st.session_state.wallet, 2),
                "Kaina (Įėjimas)": round(current_price, 2),
                "Tikslas": round(target_price, 2),
                "Rezultatas": "⏳ Tikrinama..."
            })

    st.subheader("📊 Detali Prekybos Ataskaita")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(15))
    else:
        st.info("Laukiama rinkos pokyčių prognozei sugeneruoti...")
