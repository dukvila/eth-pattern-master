import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V110 REAL-CAPITAL", layout="wide")
st_autorefresh(interval=60000, key="v110_refresh")

# Šoninė juosta nustatymams
st.sidebar.header("💰 Piniginės nustatymai")
if 'balance' not in st.session_state:
    st.session_state.balance = 1000.0  # Pradinė suma

new_balance = st.sidebar.number_input("Tavo turima suma (€):", value=st.session_state.balance, step=10.0)
if new_balance != st.session_state.balance:
    st.session_state.balance = new_balance
    st.session_state.trades_log = [] # Išvalom, jei keičiam biudžetą
    st.session_state.stats = {"Laimėta": 0, "Viso": 0}

if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"Laimėta": 0, "Viso": 0}

# 2. Duomenų gavimas
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-100:]
            df = pd.DataFrame(d, columns=['time','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['time'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

df = get_data()

# 3. Logika
if not df.empty:
    l, p = df.iloc[-1], df.iloc[-2]
    cur_p = l['close']
    vol = df['close'].tail(10).std()
    
    cmd = "STEBĖTI"
    if l['close'] > l['open'] and l['close'] > p['open']: cmd = "🟢 PIRKTI"
    elif l['close'] < l['open'] and l['close'] < p['open']: cmd = "🔴 PARDUOTI"

    tp = cur_p + (vol * 2.1) if "PIRKTI" in cmd else cur_p - (vol * 2.1)
    sl = cur_p - (vol * 1.5) if "PIRKTI" in cmd else cur_p + (vol * 1.5)
    
    # Rezultatų tikrinimas ir Piniginės atnaujinimas
    for t in st.session_state.trades_log:
        if t['Rezultatas'] == "Tikrinama...":
            rez = 0
            baigta = False
            if (t['Signal'] == "🟢 PIRKTI" and cur_p >= t['Tikslas (TP)']):
                rez = (t['Kiekis (ETH)'] * t['Tikslas (TP)']) - t['Investuota']
                t['Rezultatas'] = "✅ LAIMĖTA"
                baigta = True
            elif (t['Signal'] == "🟢 PIRKTI" and cur_p <= t['Riba (SL)']):
                rez = (t['Kiekis (ETH)'] * t['Riba (SL)']) - t['Investuota']
                t['Rezultatas'] = "❌ STOP LOSS"
                baigta = True
            elif (t['Signal'] == "🔴 PARDUOTI" and cur_p <= t['Tikslas (TP)']):
                rez = t['Investuota'] - (t['Kiekis (ETH)'] * t['Tikslas (TP)'])
                t['Rezultatas'] = "✅ LAIMĖTA"
                baigta = True
            elif (t['Signal'] == "🔴 PARDUOTI" and cur_p >= t['Riba (SL)']):
                rez = t['Investuota'] - (t['Kiekis (ETH)'] * t['Riba (SL)'])
                t['Rezultatas'] = "❌ STOP LOSS"
                baigta = True
            
            if baigta:
                st.session_state.balance += rez
                t['Pelnas/Nuostolis'] = f"{round(rez, 2)}€"
                if "✅" in t['Rezultatas']: st.session_state.stats["Laimėta"] += 1

    # Naujo sandorio kūrimas
    now_t = datetime.now().strftime("%H:%M")
    if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
        if cmd != "STEBĖTI" and st.session_state.balance > 10:
            invest = st.session_state.balance # Investuojam viską, kas yra piniginėje
            kiekis = invest / cur_p
            st.session_state.stats["Viso"] += 1
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t, 
                "Signal": cmd, 
                "Investuota": round(invest, 2),
                "Kiekis (ETH)": round(kiekis, 4),
                "Tikslas (TP)": round(tp, 2), 
                "Riba (SL)": round(sl, 2), 
                "Pelnas/Nuostolis": "—",
                "Rezultatas": "Tikrinama..."
            })

    # --- VAIZDAVIMAS ---
    st.header(f"💼 Piniginė: {round(st.session_state.balance, 2)}€")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sistemos Patikimumas", f"{ (st.session_state.stats['Laimėta']/st.session_state.stats['Viso']*100 if st.session_state.stats['Viso']>0 else 0):.1f}%")
    with col2:
        profit_total = st.session_state.balance - new_balance
        st.metric("Bendras Pelnas", f"{round(profit_total, 2)}€", delta=f"{round(profit_total, 2)}€")

    st.write("### 📜 Detali Prekybos Ataskaita")
    if st.session_state.trades_log:
        log_df = pd.DataFrame(st.session_state.trades_log)
        st.table(log_df[['Laikas', 'Signal', 'Investuota', 'Kiekis (ETH)', 'Tikslas (TP)', 'Riba (SL)', 'Pelnas/Nuostolis', 'Rezultatas']].head(15))
