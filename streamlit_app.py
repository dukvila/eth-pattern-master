import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V109 PRO-ACCOUNTANT", layout="wide")
st_autorefresh(interval=60000, key="v109_refresh")

# SAUGIKLIS: Išvalome seną atmintį, kad pridėtume naują stulpelį "Pelnas/Nuostolis"
if 'trades_log' in st.session_state and len(st.session_state.trades_log) > 0:
    if "Pelnas/Nuostolis" not in st.session_state.trades_log[0]:
        st.session_state.trades_log = []
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
    
    # Rezultatų tikrinimas ir pelno skaičiavimas
    for t in st.session_state.trades_log:
        if t['Rezultatas'] == "Tikrinama...":
            pelnas = 0
            if (t['Signal'] == "🟢 PIRKTI" and cur_p >= t['Tikslas (TP)']):
                t['Rezultatas'] = "✅ LAIMĖTA"
                t['Pelnas/Nuostolis'] = f"+{round(t['Tikslas (TP)'] - t['Kaina (Įėjimas)'], 2)}€"
                st.session_state.stats["Laimėta"] += 1
            elif (t['Signal'] == "🟢 PIRKTI" and cur_p <= t['Riba (SL)']):
                t['Rezultatas'] = "❌ STOP LOSS"
                t['Pelnas/Nuostolis'] = f"{round(t['Riba (SL)'] - t['Kaina (Įėjimas)'], 2)}€"
            elif (t['Signal'] == "🔴 PARDUOTI" and cur_p <= t['Tikslas (TP)']):
                t['Rezultatas'] = "✅ LAIMĖTA"
                t['Pelnas/Nuostolis'] = f"+{round(t['Kaina (Įėjimas)'] - t['Tikslas (TP)'], 2)}€"
                st.session_state.stats["Laimėta"] += 1
            elif (t['Signal'] == "🔴 PARDUOTI" and cur_p >= t['Riba (SL)']):
                t['Rezultatas'] = "❌ STOP LOSS"
                t['Pelnas/Nuostolis'] = f"{round(t['Kaina (Įėjimas)'] - t['Riba (SL)'], 2)}€"

    # Žurnalo pildymas
    now_t = datetime.now().strftime("%H:%M")
    if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
        if cmd != "STEBĖTI":
            st.session_state.stats["Viso"] += 1
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t, 
                "Signal": cmd, 
                "Kaina (Įėjimas)": round(cur_p, 2), 
                "Tikslas (TP)": round(tp, 2), 
                "Riba (SL)": round(sl, 2), 
                "Pelnas/Nuostolis": "—",
                "Rezultatas": "Tikrinama..."
            })

    # --- VAIZDAVIMAS ---
    wr = (st.session_state.stats["Laimėta"] / st.session_state.stats["Viso"] * 100) if st.session_state.stats["Viso"] > 0 else 0
    st.title(f"📊 Patikimumas: {wr:.1f}%")
    st.info(f"Dabartinė ETH Kaina: {cur_p:.2f}€ | Signalas: {cmd}")
    
    # Išplėstas žurnalas
    st.write("### 📜 Detalus Prekybos Žurnalas")
    if st.session_state.trades_log:
        log_df = pd.DataFrame(st.session_state.trades_log)
        st.table(log_df[['Laikas', 'Signal', 'Kaina (Įėjimas)', 'Tikslas (TP)', 'Riba (SL)', 'Pelnas/Nuostolis', 'Rezultatas']].head(15))

    # Grafikas apačioje
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df['time'].tail(20), df['close'].tail(20), label='Kaina', marker='o', markersize=3)
    ax.legend()
    st.pyplot(fig)
