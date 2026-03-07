import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V106 RECOVERY", layout="wide")
st_autorefresh(interval=60000, key="v106_refresh")

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

# 3. Logika ir skaičiavimai
if not df.empty:
    l = df.iloc[-1]
    p = df.iloc[-2]
    cur_p = l['close']
    vol = df['close'].tail(10).std()
    
    # Signalo nustatymas
    cmd = "STEBĖTI"
    if l['close'] > l['open'] and l['close'] > p['open']: cmd = "🟢 PIRKTI"
    elif l['close'] < l['open'] and l['close'] < p['open']: cmd = "🔴 PARDUOTI"

    tp = cur_p + (vol * 2.1) if "PIRKTI" in cmd else cur_p - (vol * 2.1)
    sl = cur_p - (vol * 1.5) if "PIRKTI" in cmd else cur_p + (vol * 1.5)
    
    # Rezultatų tikrinimas
    for t in st.session_state.trades_log:
        if t['Rezultatas'] == "Tikrinama...":
            if (t['Signal'] == "🟢 PIRKTI" and cur_p >= t['TP_Kaina']):
                t['Rezultatas'] = "✅ LAIMĖTA"; st.session_state.stats["Laimėta"] += 1
            elif (t['Signal'] == "🟢 PIRKTI" and cur_p <= t['SL_Kaina']):
                t['Rezultatas'] = "❌ STOP LOSS"
            elif (t['Signal'] == "🔴 PARDUOTI" and cur_p <= t['TP_Kaina']):
                t['Rezultatas'] = "✅ LAIMĖTA"; st.session_state.stats["Laimėta"] += 1
            elif (t['Signal'] == "🔴 PARDUOTI" and cur_p >= t['SL_Kaina']):
                t['Rezultatas'] = "❌ STOP LOSS"

    # Naujo įrašo kūrimas
    now_t = datetime.now().strftime("%H:%M")
    if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
        if cmd != "STEBĖTI":
            st.session_state.stats["Viso"] += 1
            st.session_state.trades_log.insert(0, {"Laikas": now_t, "Signal": cmd, "Kaina": cur_p, "TP_Kaina": tp, "SL_Kaina": sl, "Rezultatas": "Tikrinama..."})

    # --- VAIZDAVIMAS ---
    wr = (st.session_state.stats["Laimėta"] / st.session_state.stats["Viso"] * 100) if st.session_state.stats["Viso"] > 0 else 0
    st.title(f"📊 Patikimumas: {wr:.1f}%")
    st.info(f"Dabartinis Signalas: {cmd} | Kaina: {cur_p:.2f}€")
    
    # Grafikas
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['time'].tail(15), df['close'].tail(15), label='ETH Kaina', marker='o')
    ax.axhline(tp, color='green', linestyle='--', label='Target')
    ax.axhline(sl, color='red', linestyle='--', label='Stop Loss')
    ax.legend()
    st.pyplot(fig)

    # Žurnalas
    st.write("### 📈 Prekybos Žurnalas (Paskutiniai 10)")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log)[['Laikas', 'Signal', 'Kaina', 'Rezultatas']].head(10))
