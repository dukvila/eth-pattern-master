import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V137 PROGNOZĖS VARIKLIS", layout="wide")
st_autorefresh(interval=60000, key="v137_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trade' not in st.session_state: st.session_state.active_trade = None
if 'trades_log' not in st.session_state: st.session_state.trades_log = []

# 2. Duomenų gavimas ir paruošimas prognozei
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

if not df.empty:
    # --- MATEMATINIS MODELIS (Linear Regression pagrindas) ---
    y = df['close'].tail(20).values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1) # Skaičiuojame kainos krypties kampą
    
    cur_p = df.iloc[-1]['close']
    # 20 valandų prognozė (80 žvakių po 15min)
    future_steps = np.arange(len(y), len(y) + 80)
    future_prices = slope * future_steps + intercept
    
    max_f = np.max(future_prices)
    min_f = np.min(future_prices)
    
    # 3. Vaizdavimas
    st.title(f"📊 Prognozės Modelis: {round(st.session_state.wallet, 2)}€")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Dabartinė Kaina", f"{round(cur_p, 2)}€")
    col2.metric("Prognozuojama 20h", f"{round(future_prices[-1], 2)}€", f"{round(slope*80, 2)}€")
    col3.metric("Trendo Jėga", "STIPRUS" if abs(slope) > 0.5 else "SILPNAS")

    # Grafikas su pasikliautinuoju intervalu
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'].tail(20), y, label="Faktinė kaina (5h)", marker='o', linewidth=2)
    
    f_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 81)]
    ax.plot(f_times, future_prices, '--', color='red' if slope < 0 else 'green', label="Modelio prognozė (20h)")
    ax.fill_between(f_times, future_prices - 5, future_prices + 5, color='gray', alpha=0.1, label="Paklaida")
    ax.legend()
    st.pyplot(fig)

    # 4. PREKYBOS SIGNALAS PAGAL MODELĮ
    # Ieškome progos nupirkti pigiau (dip) ir parduoti su +10€
    target_dip = min_f if slope < 0 else cur_p
    potential_exit = max_f if max_f > target_dip else target_dip + (10 / (st.session_state.wallet / target_dip))
    est_profit = (st.session_state.wallet / target_dip) * (potential_exit - target_dip)
