import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Pagrindinė sąranka
st.set_page_config(page_title="V135 CAPITAL GROWTH", layout="wide")
st_autorefresh(interval=60000, key="v135_refresh")

# --- PINIGINĖS IR REINVESTAVIMO LOGIKA ---
if 'wallet' not in st.session_state:
    st.session_state.wallet = 1700.0  # Tavo pradinis kapitalas
if 'active_trade' not in st.session_state:
    st.session_state.active_trade = None # Ar šiuo metu pinigai "įdarbinti"?
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []

def reset_all():
    st.session_state.wallet = 1700.0
    st.session_state.active_trade = None
    st.session_state.trades_log = []
    st.rerun()

# --- DUOMENŲ GAVIMAS ---
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

# --- PREKYBOS PROCESAS ---
if not df.empty:
    cur_p = df.iloc[-1]['close']
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # 20h Prognozė maksimaliam pelnui
    future_20h = [cur_p + (trend_4h * i) for i in range(1, 81)]
    max_20h = max(future_20h)
    
    # 4h Prognozė artimiausiam "dugnui"
    future_4h = [cur_p + (trend_4h * i) for i in range(1, 17)]
    dip_price = min(future_4h)

    st.title(f"📈 Reinvestuojamas Balansas: {round(st.session_state.wallet, 2)}€")
    
    # Tikriname aktyvų sandorį (Ar jau parduota?)
    if st.session_state.active_trade:
        trade = st.session_state.active_trade
        st.warning(f"⏳ LAUKIAMA PARDAVIMO: Nupirkta už {trade['buy_p']}€. Tikslas: {trade['target']}€")
        
        if cur_p >= trade['target']:
            pelnas = (trade['invested'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += pelnas # PRIDEDAMAS PELNAS PRIE BALANSO
            st.session_state.active_trade = None
            st.session_state.trades_log.insert(0, {
                "Laikas": datetime.now().strftime("%H:%M"),
                "Veiksmas": "✅ PARDUOTA (Pelnas)",
                "Pelnas": f"+{round(pelnas, 2)}€",
                "Naujas Balansas": f"{round(st.session_state.wallet, 2)}€"
            })
            st.balloons()
    
    # --- GRAFIKAS ---
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['time'].tail(16), df['close'].tail(16), label="Istorija (4h)", marker='o')
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 81)]
    ax.plot(future_times, future_20h, '--', color='orange', label="Prognozė (20h)")
    ax.axhline(y=cur_p, color='gray', linestyle=':', label="Dabar")
    ax.legend()
    st.pyplot(fig)

    # --- NAUJO SANDORIO PAIEŠKA (Tik jei turime laisvų pinigų) ---
    potential_profit = (st.session_state.wallet / dip_price) * (max_20h - dip_price)
    
    if st.session_state.active_trade is None:
        if potential_profit >= 10.0:
            buy_p = dip_price if trend_4h < -0.01 else cur_p
            sell_p = max_20h if max_20h > (buy_p + 5) else (buy_p + (10 / (st.session_state.wallet / buy_p)))
            
            st.success(f"💎 Rasta proga! Nupirkus už {round(buy_p, 2)}€, uždirbsi {round(potential_profit, 2)}€")
            
            if st.button(f"SUDARYTI SANDORĮ UŽ {round(st.session_state.wallet, 2)}€"):
                st.session_state.active_trade = {
                    "buy_p": buy_p,
                    "target": sell_p,
                    "invested": st.session_state.wallet
                }
                st.session_state.trades_log.insert(0, {
                    "Laikas": datetime.now().strftime("%H:%M"),
                    "Veiksmas": "🛒 PIRKTI (Limit)",
                    "Kaina": round(buy_p, 2),
                    "Tikslas": round(sell_p, 2),
                    "Būsena": "Vykdoma..."
                })
                st.rerun()
        else:
            st.info(f"Laukiama pelno progos (>10€). Dabartinis potencialas: {round(potential_profit, 2)}€")

    if st.sidebar.button("🗑️ NULINTI BALANSĄ"): reset_all()
    st.subheader("📜 Pin
