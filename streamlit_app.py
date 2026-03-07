import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Pagrindinė Konfigūracija
st.set_page_config(page_title="ETH V125 REVOLUT PRO", layout="wide")
st_autorefresh(interval=60000, key="v125_refresh")

# --- ATMINTIES APSAUGA (Sutvarko visas KeyError problemas) ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'wallet' not in st.session_state:
    st.session_state.wallet = 1000.0 
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0

# Funkcija, kurią BŪTINA paspausti, jei matai raudoną klaidą
def reset_all():
    st.session_state.trades_log = []
    st.session_state.total_pnl = 0.0
    st.rerun()

# --- ŠONINIS MENIU ---
with st.sidebar:
    st.header("🕹️ Boso Kontrolė")
    st.session_state.wallet = st.number_input("Tavo Revolut Balansas (€):", value=float(st.session_state.wallet), step=50.0)
    if st.button("🗑️ NULINTI ISTORIJĄ (FIX ERRORS)"):
        reset_all()
    st.markdown("---")
    st.write("🎯 Minimalus tikslas: **10€**")

# 2. Rinkos Duomenų Gavimas
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

# 3. Logika ir Skaičiavimai
if not df.empty:
    cur_p = df.iloc[-1]['close']
    vol = df['close'].tail(15).std()
    
    # Analizuojame 4 valandų tendenciją (16 žvakių po 15min)
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # AUTOMATINIS SENŲ SANDORIŲ VALYMAS (KeyError prevencija)
    valid_log = []
    for t in st.session_state.trades_log:
        # Jei sandoryje trūksta naujų stulpelių - jį ignoruojame, kad programa neužlūžtų
        if not all(k in t for k in ['Laikas', 'Veiksmas', 'Investuota', 'Kaina (Įėjimas)', 'Tikslas']):
            continue
            
        if t['Rezultatas'] == "⏳ Tikrinama...":
            pelnas = 0.0
            uždaryta = False
            
            # Pirkimo logika (Kilimas)
            if t['Veiksmas'] == "🟢 PIRKTI" and cur_p >= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (cur_p - t['Kaina (Įėjimas)'])
                uždaryta = True
            # Pardavimo logika (Kritimas)
            elif t['Veiksmas'] == "🔴 PARDUOTI" and cur_p <= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Kaina (Įėjimas)']) * (t['Kaina (Įėjimas)'] - cur_p)
                uždaryta = True
            
            if uždaryta:
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_pnl += pelnas
                st.session_state.wallet += pelnas # REINVESTAVIMAS
        valid_log.append(t)
    st.session_state.trades_log = valid_log

    # --- PAGRINDINIS EKRANAS ---
    col1, col2 = st.columns(2)
    col1.metric("💰 Balansas (Reinvestuojama)", f"{round(st.session_state.wallet, 2)}€")
    col2.metric("📈 Sukauptas Pelnas", f"{round(st.session_state.total_pnl, 2)}€")
    
    st.write(f"🕒 Laikas: {datetime.now().strftime('%H:%M:%S')} | ETH: **{cur_p:.2f}€**")

    # Grafikas su 4h prognoze
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 17)]
    future_prices = [cur_p + (trend_4h * i) for i in range(1, 17)]
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(df['time'].tail(25), df['close'].tail(25), label="Dabartinė kaina", marker='o', markersize=3)
    ax.plot(future_times, future_prices, '--', color='orange', label="4h Prognozė")
    ax.set_facecolor('#f0f2f6')
    ax.legend()
    st.pyplot(fig)

    # --- INTELEKTUALUS ĮĖJIMAS (10€ TAISYKLĖ) ---
    predicted_move = abs(trend_4h * 16) # Kiek kaina pasikeis per 4h
    est_profit = (st.session_state.wallet / cur_p) * predicted_move
    
    signal = "👀 STEBĖTI (Laukiama >10€ prognozės)"
    target = cur_p
    
    if est_profit >= 10.0:
        if trend_4h > 0.05:
            signal = "🟢 PIRKTI"
            target = cur_p + predicted_move
        elif trend_4h < -0.05:
            signal = "🔴 PARDUOTI"
            target = cur_p - predicted_move

    # Sandorio registravimas
    now_t = datetime.now().strftime("%H:%M")
    if st.session_state.wallet > 0 and "STEBĖTI" not in signal:
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Veiksmas": signal,
                "Investuota": round(st.session_state.wallet, 2),
                "Kaina (Įėjimas)": round(cur_p, 2),
                "Tikslas": round(target, 2),
                "Prognozė (4h)": f"+{round(est_profit, 2)}€",
                "Rezultatas": "⏳ Tikrinama..."
            })

    st.subheader("📜 Boso Detali Ataskaita")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(15))
    else:
        st.info("Laukiama stip
