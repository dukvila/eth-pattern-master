import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V100.1 VALIDATOR", layout="wide")
st_autorefresh(interval=60000, key="v100_refresh")

if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []

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

def analyze_v100(data):
    if data.empty: return None
    l, p = data.iloc[-1], data.iloc[-2]
    
    # Tikslesni indikatoriai
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
    rsi = 100 - (100 / (1 + (gain / loss))) if loss > 0 else 50
    vol = data['close'].tail(12).std()

    cur_p = l['close']
    score, cmd = 0, "STEBĖTI"
    
    if l['close'] > l['open'] and l['close'] > p['open'] and rsi < 65:
        score, cmd = 3.2, "🟢 PIRKTI"
    elif l['close'] < l['open'] and l['close'] < p['open'] and rsi > 35:
        score, cmd = -3.2, "🔴 PARDUOTI"

    tp = cur_p + (vol * 2.5) if score > 0 else cur_p - (vol * 2.5)
    sl = cur_p - (vol * 1.8) if score > 0 else cur_p + (vol * 1.8)
    
    now = datetime.now()
    if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now.strftime("%H:%M"):
        st.session_state.trades_log.insert(0, {"Laikas": now.strftime("%H:%M"), "Signal": cmd, "Kaina": f"{cur_p:.2f}€"})

    return {"cmd": cmd, "p": cur_p, "rsi": rsi, "tp": tp, "sl": sl, "score": score, "vol": vol}

res = analyze_v100(df)

if res:
    color = "#28a745" if "PIRKTI" in res['cmd'] else "#dc3545" if "PARDUOTI" in res['cmd'] else "#343a40"
    st.markdown(f"""
    <div style="background-color:{color}; padding:25px; border-radius:15px; color:white; text-align:center; border: 4px solid white;">
        <h1 style="margin:0;">{res['cmd']} | {res['p']:.2f}€</h1>
        <p style="font-size:22px;">🎯 Target: {res['tp']:.2f}€ | 🛡️ Stop Loss: {res['sl']:.2f}€ | RSI: {res['rsi']:.1f}</p>
    </div>
    """, unsafe_allow_html=True)

    # GRAFIKO FIX
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('#0a0a0a')
    
    # 2 valandų praeitis (8 žvakės)
    hist_df = df.tail(8)
    ax.plot(hist_df['time'], hist_df['close'], color='white', linewidth=3, label="Analizė (2 val.)")
    
    # Paros prognozė
    last_time = df['time'].iloc[-1]
    fut_times = [last_time + timedelta(minutes=15*i) for i in range(1, 21)]
    fut_prices = [res['p'] + (res['score'] * i * 0.4) for i in range(1, 21)]
    ax.plot(fut_times, fut_prices, color='#00ffcc', linestyle='--', linewidth=4, label="Paros prognozė")
    
    # Vizualios ribos
    ax.axhline(res['tp'], color='#00ffcc', alpha=0.3, linestyle='--')
    ax.axhline(res['sl'], color='#ff4b4b', alpha=0.3, linestyle='--')
    
    ax.tick_params(colors='white', labelsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    plt.legend(facecolor='black', labelcolor='white')
    
    # Štai ši eilutė užtikrina, kad grafikas būtų parodytas!
    st.pyplot(fig)

    st.markdown("### 📈 Prekybos Žurnalas (Tikrinimas)")
    st.table(pd.DataFrame(st.session_state.trades_log).head(8))
