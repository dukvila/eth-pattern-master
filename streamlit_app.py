import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="ETH V105 TRUST-FIX", layout="wide")
st_autorefresh(interval=60000, key="v105_refresh")

if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"Laimėta": 0, "Viso": 0}

def get_live_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            if 'result' in res:
                d = res['result']['XETHZEUR'][-160:]
                df = pd.DataFrame(d, columns=['time','open','high','low','close','vwap','vol','count']).astype(float)
                df['time'] = pd.to_datetime(df['time'], unit='s') + timedelta(hours=2)
                return df
    except: return pd.DataFrame()

df = get_live_data()

def analyze_logic(data):
    if data.empty: return None
    l, p = data.iloc[-1], data.iloc[-2]
    cur_p = l['close']
    vol = data['close'].tail(12).std()
    
    # Paprasta bet tvirta pirkimo logika
    cmd = "STEBĖTI"
    score = 0
    if l['close'] > l['open'] and l['close'] > p['open']:
        cmd, score = "🟢 PIRKTI", 3.5
    elif l['close'] < l['open'] and l['close'] < p['open']:
        cmd, score = "🔴 PARDUOTI", -3.5

    tp = cur_p + (vol * 2.2) if score > 0 else cur_p - (vol * 2.2)
    sl = cur_p - (vol * 1.5) if score > 0 else cur_p + (vol * 1.5)
    
    now_str = datetime.now().strftime("%H:%M")
    
    # Rezultatų tikrinimas
    for t in st.session_state.trades_log:
        if t['Rezultatas'] == "Tikrinama...":
            if (t['Signal'] == "🟢 PIRKTI" and cur_p >= t['TP']):
                t['Rezultatas'] = "✅ LAIMĖTA"
                st.session_state.stats["Laimėta"] += 1
            elif (t['Signal'] == "🟢 PIRKTI" and cur_p <= t['SL']):
                t['Rezultatas'] = "❌ STOP LOSS"
            elif (t['Signal'] == "🔴 PARDUOTI" and cur_p <= t['TP']):
                t['Rezultatas'] = "✅ LAIMĖTA"
                st.session_state.stats["Laimėta"] += 1
            elif (t['Signal'] == "🔴 PARDUOTI" and cur_p >= t['SL']):
                t['Rezultatas'] = "❌ STOP LOSS"

    if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_str:
        if cmd != "STEBĖTI":
            st.session_state.stats["Viso"] += 1
            st.session_state.trades_log.insert(0, {"Laikas": now_str, "Signal": cmd, "Kaina": cur_p, "TP": tp, "SL": sl, "Rezultatas": "Tikrinama..."})

    return {"cmd": cmd, "p": cur_p, "tp": tp, "sl": sl, "score": score}

res = analyze_logic(df)

if res:
    wr = (st.session_state.stats["Laimėta"] / st.session_state.stats["Viso"] * 100) if st.session_state.stats["Viso"] > 0 else 0
    st.subheader(f"📊 Patikimumas: {wr:.1f}% (Laimėta {st.session_state.stats['Laimėta']} iš {st.session_state.stats['Viso']})")
