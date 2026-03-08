import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
import math
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V167 TITAN OVERLORD", layout="wide")
st_autorefresh(interval=60000, key="v167_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []
if 'equity_curve' not in st.session_state: st.session_state.equity_curve = [{"time": datetime.now(), "balance": 1700.0}]

# Matematika be klaidų
def get_probability(current, target, std):
    if std < 0.01: return 50.0
    z = (current - target) / std
    return 0.5 * (1 + math.erf(z / math.sqrt(2))) * 100

# 2. Duomenų Gavimas
def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-200:]
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            df['MA100'] = df['close'].rolling(window=100).mean()
            df['STD'] = df['close'].rolling(window=20).std()
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    ma100 = df.iloc[-1]['MA100']
    std_val = df.iloc[-1]['STD']
    
    # 20h Prognozė
    y_vals = df['close'].tail(16).values 
    slope, intercept = np.polyfit(np.arange(len(y_vals)), y_vals, 1)
    target_20h = slope * 80 + intercept

    # --- AGRESYVUMO VALDYMAS ---
    st.sidebar.title("🎮 Valdymo Centras")
    mode = st.sidebar.select_slider(
        "Pasirink Agresyvumą",
        options=["SAUGUS", "SUBALANSUOTAS", "AGRESYVUS"],
        value="SUBALANSUOTAS"
    )
    
    # Algoritmo korekcija pagal rėžimą
    if mode == "SAUGUS":
        buy_offset, profit_target = 0.8, 1.5  # Perka pigiau, parduoda greičiau
    elif mode == "AGRESYVUS":
        buy_offset, profit_target = 0.2, 5.0  # Perka brangiau, laukia didelio pelno
    else:
        buy_offset, profit_target = 0.5, 2.5  # Aukso vidurys
    
    smart_buy = round(cur_p - (std_val * buy_offset), 2)
    smart_sell = round(max(smart_buy + profit_target, target_20h), 2)

    # --- AUTOMATINIS VYKDYMAS ---
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA":
            if cur_p < trade['buy_p'] * 0.98: # Stop-Loss
                st.session_state.wallet += trade['amount']
                trade['status'] = "STOP-LOSS 🛡️"
            elif cur_p <= trade['buy_p']:
                trade['status'] = "VYKDOMAS 🚀"
        
        if trade['status'] == "VYKDOMAS 🚀" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "PELNAS ✅"
            trade['finish_time'] = datetime.now()
            trade['profit_eur'] = profit
            st.session_state.history.append(trade)
            st.session_state.equity_curve.append({"time": datetime.now(), "balance": st.session_state.wallet})
            st.balloons()

    # --- PAGRINDINIS SKYDELIS ---
    st.title(f"🚀 Titan Overlord V167: {round(st.session_state.wallet, 2)}€")
    
    week_profit = sum([t['profit_eur'] for t in st.session_state.history if t['finish_time'] > (datetime.now() - timedelta(days=7))])
    st.info(f"📍 Rėžimas: **{mode}** | Savaitės rezultatas: **+{round(week_profit, 2)}€**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    c2.metric("TRENDAS", "KYLA 📈" if cur_p > ma100 else "KRINTA 📉")
    c3.metric("TIKSLAS", f"{round(smart_sell, 2)}€")
    c4.metric("20H PROGNOZĖ", f"{round(target_20h, 2)}€")

    # --- AUTOPILOTO KONSOLE ---
    st.divider()
    col_x, col_y = st.columns([2, 1])
    with col_x:
        st.subheader("🤖 Autopiloto Siūlomas Sandoris")
        in_buy = st.number_input("Pirkimas", value=smart_buy)
        in_sell = st.number_input("Pardavimas", value=smart_sell)
        in_sum = st.number_input("Investicijos Suma (€)", value=1000.0)
    
    with col_y:
        p_buy = get_probability(cur_p, in_buy, std_val)
        st.metric("Pirkimo šansas", f"{round(min(p_buy, 99.9), 1)}%")
        p_sell = (100 - get_probability(target_20h, in_sell, std_val * 2))
        st.metric("Pardavimo šansas", f"{round(max(min(p_sell, 99.9), 0.1), 1)}%")
        
        if st.button("⚡ VYKDYTI REIDĄ", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.active_trades.append({"buy_p": in_buy, "sell_p": in_sell, "amount": in_sum, "status": "LAUKIA", "time": datetime.now().strftime("%H:%M")})
                st.session_state.wallet -= in_sum
                st.rerun()

    # --- MONITORIUS ---
    tab1, tab2 = st.tabs(["📉 Rinkos Pulsas", "📜 Žurnalas"])
    with tab1:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(df['time'].tail(50), df['close'].tail(50), color="white", alpha=0.8)
        ax.set_facecolor('#0E1117')
        fig.patch.set_facecolor('#0E1117')
        st.pyplot(fig)
    with tab2:
        if st.session_state.history: st.dataframe(pd.DataFrame(st.session_state.history).tail(10))
