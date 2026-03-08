import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Konfigūracija
st.set_page_config(page_title="V158 TITAN TOTAL RECAP", layout="wide")
st_autorefresh(interval=60000, key="v158_refresh")

# Duomenų saugykla
if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []
if 'prediction_history' not in st.session_state: st.session_state.prediction_history = []

def play_alert():
    st.components.v1.html('<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg"></audio>', height=0)

# 2. Saugus Duomenų Gavimas
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
    
    # Prognozės logika
    y_vals = df['close'].tail(16).values 
    slope, intercept = np.polyfit(np.arange(len(y_vals)), y_vals, 1)
    target_20h = slope * 96 + intercept
    
    # Paklaidos fiksavimas
    st.session_state.prediction_history.append({"time": df.iloc[-1]['time'], "pred": slope * 15 + intercept, "fact": cur_p})
    if len(st.session_state.prediction_history) > 50: st.session_state.prediction_history.pop(0)
    err_df = pd.DataFrame(st.session_state.prediction_history)
    reliability = max(0, (100 - ((err_df['fact'] - err_df['pred']).abs().mean() / cur_p * 2500)))

    # --- AUTOMATINIS VYKDYMAS IR PELNO SKAIČIAVIMAS ---
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA" and cur_p <= trade['buy_p']:
            trade['status'] = "VYKDOMAS"
            play_alert()
            
        if trade['status'] == "VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "PELNAS"
            trade['finish_time'] = datetime.now()
            trade['profit_eur'] = profit
            st.session_state.history.append(trade)
            st.balloons()

    # --- DIENOS REZULTATAI ---
    today = datetime.now().date()
    today_trades = [t for t in st.session_state.history if t['finish_time'].date() == today]
    today_profit = sum([t['profit_eur'] for t in today_trades])

    # --- PAGRINDINIS SKYDELIS ---
    st.title(f"🛡️ Titan Total Recap V158: {round(st.session_state.wallet, 2)}€")
    
    # Dienos ataskaitos blokas
    st.info(f"📅 **Šios dienos rezultatas:** Atlikta sandorių: **{len(today_trades)}** | Uždirbta: **+{round(today_profit, 2)}€**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    c2.metric("TRENDAS", "KYLA 📈" if cur_p > ma100 else "KRINTA 📉")
    c3.metric("PATIKIMUMAS", f"{round(reliability, 1)}%")
    c4.metric("20H TIKSLAS", f"{round(target_20h, 2)}€")

    # --- STRATEGIJA ---
    st.divider()
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        trade_sum = st.number_input("Suma (€)", value=100.0)
        req_buy = st.number_input("Pirkimas (€)", value=cur_p - 0.5)
    with col_b:
        prob = max(0, min(100, 100 - (abs(cur_p - req_buy) / std_val * 25)))
        st.write(f"📊 Tikimybė: **{round(prob, 1)}%**")
        req_sell = st.number_input("Pardavimas (€)", value=round(max(req_buy * 1.01, target_20h), 2))
    with col_c:
        st.write(" ")
        if st.button("🚀 UŽSTATYTI"):
            if st.session_state.wallet >= trade_sum:
                st.session_state.active_trades.append({
                    "buy_p": req_buy, "sell_p": req_sell, "amount": trade_sum, 
                    "status": "LAUKIA", "start_time": datetime.now()
                })
                st.session_state.wallet -= trade_sum
                st.rerun()

    # --- LENTELĖS ---
    active_view = [t for t in st.session_state.active_trades if t['status'] != "PELNAS"]
    if active_view:
        st.subheader("📑 Vykdomi sandoriai")
        st.table(pd.DataFrame(active_view)[['buy_p', 'sell_p', 'amount', 'status']])

    # --- VIZUALIZACIJA ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(df['time'].tail(60), df['close'].tail(60), color='#1f77b4', label="Kaina")
    ax1.axhline(y=ma100, color='red', alpha=0.2, label="Trendas")
    ax1.plot([df.iloc[-1]['time'], df.iloc[-1]['time'] + timedelta(hours=20)], [cur_p, target_20h], 'o--', color='orange')
    ax2.plot(err_df['time'], (err_df['fact'] - err_df['pred']).abs(), color='red', label="Sistemos klaida")
    st.pyplot(fig)
