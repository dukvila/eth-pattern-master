import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V112 PRO-STRATEGY", layout="wide")
st_autorefresh(interval=60000, key="v112_refresh")

# ATMINTIES VALDYMAS (Saugiklis nuo KeyError)
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'balance' not in st.session_state:
    st.session_state.balance = 1000.0

# Rankinis balanso papildymas
st.sidebar.header("💰 Piniginė")
input_bal = st.sidebar.number_input("Tavo turima suma (€):", value=st.session_state.balance, step=50.0)
if input_bal != st.session_state.balance:
    st.session_state.balance = input_bal

# 2. Duomenų gavimas ir techniniai indikatoriai (RSI)
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI Skaičiavimas (Rizikos vertinimui)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            return df
    except: return pd.DataFrame()

df = get_data()

# 3. Strategijos logika
if not df.empty:
    l = df.iloc[-1]
    p = df.iloc[-2]
    cur_p = l['close']
    rsi = l['rsi']
    vol = df['close'].tail(10).std()

    # SPRENDIMAS: Ar verta pirkti dabar, ar laukti?
    signal = "STEBĖTI"
    if l['close'] > l['open'] and rsi < 65: # Perkame tik jei nėra "perkaitę"
        signal = "🟢 PIRKTI"
    elif l['close'] < l['open'] and rsi > 35:
        signal = "🔴 PARDUOTI"

    # Pelno taškai (Trumpalaikis ir Ilgalaikis)
    t1 = cur_p + (vol * 1.5) if "PIRKTI" in signal else cur_p - (vol * 1.5)
    t2 = cur_p + (vol * 3.5) if "PIRKTI" in signal else cur_p - (vol * 3.5)
    sl = cur_p - (vol * 2.0) if "PIRKTI" in signal else cur_p + (vol * 2.0)

    # Tikriname senus sandorius
    for t in st.session_state.trades_log:
        if t['Rezultatas'] == "Tikrinama...":
            if (t['Signal'] == "🟢 PIRKTI" and cur_p >= t['Target 2']):
                pelnas = (t['Kiekis'] * t['Target 2']) - t['Investuota']
                t['Rezultatas'] = "✅ MAX PELNAS"; st.session_state.balance += pelnas
            elif (t['Signal'] == "🟢 PIRKTI" and cur_p <= t['Stop Loss']):
                nuostolis = (t['Kiekis'] * t['Stop Loss']) - t['Investuota']
                t['Rezultatas'] = "❌ STOP LOSS"; st.session_state.balance += nuostolis

    # Naujo signalo registravimas
    now_t = datetime.now().strftime("%H:%M")
    if signal != "STEBĖTI" and (not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t):
        invest = st.session_state.balance
        st.session_state.trades_log.insert(0, {
            "Laikas": now_t, "Signal": signal, "Investuota": round(invest, 2),
            "Kiekis": round(invest/cur_p, 4), "Target 1": round(t1, 2),
            "Target 2": round(t2, 2), "Stop Loss": round(sl, 2), "Rezultatas": "Tikrinama..."
        })

    # --- VAIZDAVIMAS ---
    st.header(f"💰 Balansas: {round(st.session_state.balance, 2)}€")
    
    # Prognozės vizualizacija
    st.info(f"Kaina: {cur_p:.2f}€ | RSI: {rsi:.1f} | Signalas: {signal}")
    
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df['time'].tail(25), df['close'].tail(25), marker='o', label='Kaina')
    if signal != "STEBĖTI":
        ax.axhline(t1, color='lightgreen', linestyle='--', label='Target 1 (15m)')
        ax.axhline(t2, color='green', linestyle='-', label='Target 2 (1h+)')
        ax.axhline(sl, color='red', linestyle='--', label='Stop Loss')
    ax.legend()
    st.pyplot(fig)

    st.write("### 📜 Detali Prekybos Ataskaita")
    if st.session_state.trades_log:
        log_df = pd.DataFrame(st.session_state.trades_log)
        st.table(log_df.head(10))
