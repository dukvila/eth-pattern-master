import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from scipy.stats import norm

# 1. Konfigūracija
st.set_page_config(page_title="V164 TITAN ECHO", layout="wide")
st_autorefresh(interval=60000, key="v164_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []
if 'prediction_history' not in st.session_state: st.session_state.prediction_history = []
if 'equity_curve' not in st.session_state: st.session_state.equity_curve = [{"time": datetime.now(), "balance": 1700.0}]

# --- PRANEŠIMŲ FUNKCIJOS ---
def play_victory_sound():
    # Sugroja trumpą pergalės garsą per naršyklę
    st.components.v1.html("""
        <audio autoplay>
            <source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mpeg">
        </audio>
    """, height=0)

def play_alert_sound():
    st.components.v1.html("""
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/sounds/button-10.mp3" type="audio/mpeg">
        </audio>
    """, height=0)

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
    
    # Prognozė
    y_vals = df['close'].tail(16).values 
    slope, intercept = np.polyfit(np.arange(len(y_vals)), y_vals, 1)
    target_20h = slope * 80 + intercept
    
    # --- AUTOMATINIS VYKDYMAS IR SIGNALAI ---
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA":
            # Saugumo stabdys
            if cur_p < trade['buy_p'] * 0.98:
                st.session_state.wallet += trade['amount']
                trade['status'] = "ATŠAUKTA (SAUGUMAS)"
                play_alert_sound()
                st.toast(f"⚠️ SAUGUMAS: Sandoris atšauktas dėl staigaus kritimo!", icon="🚨")
            elif cur_p <= trade['buy_p']:
                trade['status'] = "VYKDOMAS"
                st.toast(f"📥 Nupirkta už {trade['buy_p']}€!", icon="💰")
            
        if trade['status'] == "VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "PELNAS"
            trade['finish_time'] = datetime.now()
            trade['profit_eur'] = profit
            st.session_state.history.append(trade)
            st.session_state.equity_curve.append({"time": datetime.now(), "balance": st.session_state.wallet})
            
            # Pergalės signalai
            play_victory_sound()
            st.balloons()
            st.toast(f"✅ PELNAS: +{round(profit, 2)}€!", icon="🥂")

    # --- PAGRINDINIS SKYDELIS ---
    st.title(f"🛡️ Titan Echo V164: {round(st.session_state.wallet, 2)}€")
    
    today_profit = sum([t['profit_eur'] for t in st.session_state.history if t['finish_time'].date() == datetime.now().date()])
    st.info(f"📅 **Šiandienos progresas:** Pelnas: **+{round(today_profit, 2)}€** | Aktyvūs signalai: ĮJUNGTI 🔔")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    c2.metric("TRENDAS", "KYLA 📈" if cur_p > ma100 else "KRINTA 📉")
    c3.metric("PATIKIMUMAS", f"{round(100 - (abs(cur_p - target_20h)/cur_p*1000), 1)}%")
    c4.metric("20H TIKSLAS", f"{round(target_20h, 2)}€")

    # --- PLANAVIMAS ---
    st.divider()
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        in_buy = st.number_input("Pirkimas (€)", value=cur_p - 0.1, key="v164_b")
        in_sum = st.number_input("Suma (€)", value=500.0, key="v164_s")
    with col_b:
        prob_b = norm.cdf(cur_p, loc=in_buy, scale=std_val) * 100
        st.write(f"📥 Pirkimo šansas: **{round(min(prob_b, 99.9), 1)}%**")
        in_sell = st.number_input("Pardavimas (€)", value=round(max(in_buy + 2.0, target_20h), 2), key="v164_p")
        prob_s = (1 - norm.cdf(in_sell, loc=target_20h, scale=std_val * 2)) * 100
        st.write(f"📤 Pardavimo šansas: **{round(max(min(prob_s, 99.9), 0.1), 1)}%**")
    with col_c:
        st.write(" ")
        if st.button("🚀 UŽSTATYTI SU SIGNALU", use_container_width=True):
            if st.session_state.wallet >= in_sum:
                st.session_state.active_trades.append({
                    "buy_p": in_buy, "sell_p": in_sell, "amount": in_sum, 
                    "status": "LAUKIA", "time": datetime.now().strftime("%H:%M")
                })
                st.session_state.wallet -= in_sum
                st.rerun()

    # --- VALDYMAS ---
    active_view = [t for t in st.session_state.active_trades if t['status'] not in ["PELNAS", "ATŠAUKTA (SAUGUMAS)"]]
    if active_view:
        st.subheader("📑 Stebimi sandoriai")
        for i, trade in enumerate(st.session_state.active_trades):
            if trade['status'] not in ["PELNAS", "ATŠAUKTA (SAUGUMAS)"]:
                cols = st.columns([1, 1, 1, 1, 1])
                cols[0].write(f"Pirkimas: {trade['buy_p']}€")
                cols[1].write(f"Pardavimas: {trade['sell_p']}€")
                cols[2].write(f"Būsena: {trade['status']}")
                cols[3].warning(f"Saugiklis: {round(trade['buy_p']*0.98, 2)}€")
                if cols[4].button("❌ ATŠAUKTI", key=f"del_{i}"):
                    st.session_state.wallet += trade['amount']
                    st.session_state.active_trades.pop(i)
                    st.rerun()

    # --- GRAFIKAI ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1.5]})
    ax1.plot(df['time'].tail(60), df['close'].tail(60), color='#1f77b4')
    ax1.axhline(y=ma100, color='red', alpha=0.1)
    eq_df = pd.DataFrame(st.session_state.equity_curve)
    ax2.step(eq_df['time'], eq_df['balance'], where='post', color='green', linewidth=2)
    ax2.fill_between(eq_df['time'], eq_df['balance'], 1700, color='green', alpha=0.1)
    st.pyplot(fig)
