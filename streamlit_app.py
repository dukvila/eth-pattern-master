import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sistemos Branduolys
st.set_page_config(page_title="TITAN APEX V185", layout="wide")
st_autorefresh(interval=30000, key="v185_refresh")

if 'wallet' not in st.session_state: st.session_state.wallet = 1711.45
if 'active_trades' not in st.session_state: st.session_state.active_trades = []
if 'last_price' not in st.session_state: st.session_state.last_price = 0
if 'op_log' not in st.session_state: st.session_state.op_log = []

def add_log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.op_log.insert(0, f"[{now}] {msg}")
    if len(st.session_state.op_log) > 15: st.session_state.op_log.pop()

def get_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            d = res['result']['XETHZEUR'][-120:] 
            df = pd.DataFrame(d, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            return df
    except: return pd.DataFrame()

df = get_data()

if not df.empty:
    cur_p = df.iloc[-1]['close']
    
    # --- KRITINIŲ ĮVYKIŲ ANALIZĖ ---
    price_change = 0
    if st.session_state.last_price > 0:
        price_change = ((cur_p - st.session_state.last_price) / st.session_state.last_price) * 100
    
    if price_change <= -1.0:
        add_log(f"🚨 ALERT: Flash Crash {round(price_change, 2)}%!")
    
    st.session_state.last_price = cur_p

    # Dinaminiai taškai (4h istorija / 20h ateitis)
    buy_p = round(df['low'].tail(16).min() - 0.5, 2)
    initial_sell_p = round(cur_p * 1.025, 2)

    st.markdown(f"<h1 style='text-align: center; color: #ff00ff;'>🚀 TITAN APEX V185</h1>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETH DABAR", f"{cur_p}€", f"{round(price_change, 2)}%")
    c2.metric("AMD BUY", f"{buy_p}€", "DUGNAS")
    c3.metric("APEX TARGET", f"{initial_sell_p}€", "DINAMINIS")
    c4.metric("PINIGINĖ", f"{round(st.session_state.wallet, 2)}€")

    # --- GRAFIKAS SU PROGNOZE ---
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['time'], df['close'], color='#ff00ff', label='4 val. Istorija', linewidth=1.5)
    
    # 20 valandų projekcija
    f_times = [df['time'].iloc[-1] + timedelta(minutes=15*i) for i in range(1, 81)]
    f_vals = np.linspace(cur_p, initial_sell_p, 80)
    ax.plot(f_times, f_vals, color='cyan', linestyle='--', alpha=0.4, label='20 val. Ateitis')
    
    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.tick_params(colors='white')
    plt.legend()
    st.pyplot(fig)

    # --- TRAILING STOP LOGIKA IR VYKDYMAS ---
    st.divider()
    col_log, col_status = st.columns([2, 1])
    
    with col_log:
        st.subheader("📝 Operacijų Žurnalas")
        for entry in st.session_state.op_log:
            st.text(entry)
            
    with col_status:
        st.subheader("📊 Pozicijos")
        for t in st.session_state.active_trades:
            if t['status'] == "HOLD":
                live_profit = (t['amt'] / t['buy']) * (cur_p - t['buy'])
                
                # TRAILING STOP: Jei kaina kyla, keliam pardavimo ribą
                if cur_p > t['highest_seen']:
                    t['highest_seen'] = cur_p
                    t['dynamic_sell'] = round(cur_p * 0.995, 2) # Parduoti, jei krenta 0.5% nuo piko
                    add_log(f"📈 Trailing Stop pakeltas iki {t['dynamic_sell']}€")

                st.info(f"Pelnas: **{round(live_profit, 2)}€**")
                st.write(f"Sustabdymo riba: {t['dynamic_sell']}€")
                
                if st.button("💰 FIKSUOTI DABAR", key=f"fix_{t['buy']}"):
                    st.session_state.wallet += (t['amt'] + live_profit)
                    t['status'] = "DONE"
                    add_log(f"💎 Rankinis fiksavimas: +{round(live_profit, 2)}€")
                    st.rerun()

    # Automatinis vykdymas
    for t in st.session_state.active_trades:
        if t['status'] == "WAIT" and cur_p <= t['buy']:
            t['status'] = "HOLD"
            t['highest_seen'] = cur_p
            t['dynamic_sell'] = round(cur_p * 0.99, 2)
            add_log(f"✅ Pirkimas atliktas ties {t['buy']}€.")
        
        if t['status'] == "HOLD" and cur_p <= t['dynamic_sell'] and cur_p > t['buy']:
            profit = (t['amt'] / t['buy']) * (cur_p - t['buy'])
            st.session_state.wallet += (t['amt'] + profit)
            t['status'] = "DONE"
            add_log(f"🚀 APEX PARDAVIMAS: +{round(profit, 2)}€")
            st.balloons()

    if st.button("🔱 PALEISTI APEX REIDĄ (1000€)", use_container_width=True):
        if st.session_state.wallet >= 1000:
            st.session_state.active_trades.append({
                "buy": buy_p, "amt": 1000.0, "status": "WAIT", 
                "highest_seen": 0, "dynamic_sell": 0
            })
            st.session_state.wallet -= 1000
            add_log(f"🎯 Medžioklė prasidėjo ties {buy_p}€.")
            st.rerun()
