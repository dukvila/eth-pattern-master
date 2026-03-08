import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija ir Stabilumas
st.set_page_config(page_title="V160 GROWTH ARCHITECT", layout="wide")
st_autorefresh(interval=60000, key="v160_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'history' not in st.session_state: st.session_state.history = []
if 'prediction_history' not in st.session_state: st.session_state.prediction_history = []
if 'equity_curve' not in st.session_state: st.session_state.equity_curve = [{"time": datetime.now(), "balance": 1700.0}]

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
    target_20h = slope * 96 + intercept
    
    # Paklaidos sekimas
    st.session_state.prediction_history.append({"time": df.iloc[-1]['time'], "pred": slope * 15 + intercept, "fact": cur_p})
    if len(st.session_state.prediction_history) > 50: st.session_state.prediction_history.pop(0)
    err_df = pd.DataFrame(st.session_state.prediction_history)
    reliability = max(0, (100 - ((err_df['fact'] - err_df['pred']).abs().mean() / cur_p * 2500)))

    # --- AUTOMATINIS VYKDYMAS IR KAPITALO FIKSAVIMAS ---
    for trade in st.session_state.active_trades:
        if trade['status'] == "LAUKIA" and cur_p <= trade['buy_p']:
            trade['status'] = "VYKDOMAS"
            
        if trade['status'] == "VYKDOMAS" and cur_p >= trade['sell_p']:
            profit = (trade['amount'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += (trade['amount'] + profit)
            trade['status'] = "PELNAS"
            trade['finish_time'] = datetime.now()
            trade['profit_eur'] = profit
            st.session_state.history.append(trade)
            # Fiksuojame naują balansą grafikui
            st.session_state.equity_curve.append({"time": datetime.now(), "balance": st.session_state.wallet})
            st.balloons()

    # --- PAGRINDINIS SKYDELIS ---
    st.title(f"🛡️ Growth Architect V160: {round(st.session_state.wallet, 2)}€")
    
    today = datetime.now().date()
    today_profit = sum([t['profit_eur'] for t in st.session_state.history if t['finish_time'].date() == today])
    st.info(f"📅 **Šios dienos rezultatas:** Uždirbta: **+{round(today_profit, 2)}€**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH KAINA", f"{round(cur_p, 2)}€")
    c2.metric("TRENDAS", "KYLA 📈" if cur_p > ma100 else "KRINTA 📉")
    c3.metric("PATIKIMUMAS", f"{round(reliability, 1)}%")
    c4.metric("20H TIKSLAS", f"{round(target_20h, 2)}€")

    # --- STRATEGINIS PLANAVIMAS (PATAISYTA) ---
    st.divider()
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        input_buy = st.number_input("Pirkimo kaina (€)", value=cur_p - 0.2, step=0.01, key="v160_buy")
        input_sum = st.number_input("Investuojama suma (€)", value=100.0, key="v160_sum")
    with col_b:
        prob = max(0, min(100, 100 - (abs(cur_p - input_buy) / std_val * 25)))
        st.write(f"📊 Tikimybė nupirkti: **{round(prob, 1)}%**")
        input_sell = st.number_input("Pardavimo kaina (€)", value=round(max(input_buy * 1.01, target_20h), 2), step=0.01, key="v160_sell")
    with col_c:
        st.write(" ")
        if st.button("🚀 UŽSTATYTI SANDORĮ", use_container_width=True):
            if st.session_state.wallet >= input_sum:
                st.session_state.active_trades.append({
                    "buy_p": input_buy, "sell_p": input_sell, "amount": input_sum, 
                    "status": "LAUKIA", "time": datetime.now().strftime("%H:%M")
                })
                st.session_state.wallet -= input_sum
                st.rerun()

    # --- VALDYMAS IR ATŠAUKIMAS ---
    active_view = [t for t in st.session_state.active_trades if t['status'] != "PELNAS"]
    if active_view:
        st.subheader("📑 Vykdomi sandoriai")
        for i, trade in enumerate(st.session_state.active_trades):
            if trade['status'] != "PELNAS":
                cols = st.columns([1, 1, 1, 1, 1])
                cols[0].write(f"Pirkimas: {trade['buy_p']}€")
                cols[1].write(f"Pardavimas: {trade['sell_p']}€")
                cols[2].write(f"Suma: {trade['amount']}€")
                cols[3].write(f"Būsena: {trade['status']}")
                if cols[4].button("❌ ATŠAUKTI", key=f"del_{i}"):
                    st.session_state.wallet += trade['amount']
                    st.session_state.active_trades.pop(i)
                    st.rerun()

    # --- TRIJŲ LYGIŲ MONITORINGAS ---
    st.divider()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1, 1.5]})
    
    # 1. Rinkos grafikas
    ax1.plot(df['time'].tail(60), df['close'].tail(60), color='#1f77b4', label="ETH Kaina")
    ax1.axhline(y=ma100, color='red', alpha=0.2, label="Trendas")
    ax1.set_title("Rinkos Pulsas")
    
    # 2. Paklaidos grafikas
    ax2.plot(err_df['time'], (err_df['fact'] - err_df['pred']).abs(), color='red', label="Klaida")
    ax2.set_title("Analitikos Tikslumas")
    
    # 3. NAUJAS: KAPITALO AUGIMO GRAFIKAS
    eq_df = pd.DataFrame(st.session_state.equity_curve)
    ax3.step(eq_df['time'], eq_df['balance'], where='post', color='green', linewidth=2, label="Balansas")
    ax3.fill_between(eq_df['time'], eq_df['balance'], 1700, color='green', alpha=0.1)
    ax3.set_title("Kapitalo Augimo Kreivė (Pelno Progresas)")
    
    plt.tight_layout()
    st.pyplot(fig)
