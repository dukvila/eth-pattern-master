import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Sąranka
st.set_page_config(page_title="V134 FLEXI-SCALPER", layout="wide")
st_autorefresh(interval=60000, key="v134_refresh")

if 'trades_log' not in st.session_state: st.session_state.trades_log = []
if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0

def reset_all():
    st.session_state.trades_log = []
    st.rerun()

# 2. Duomenų gavimas
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
    cur_p = df.iloc[-1]['close']
    # 4h Trendas (greitam reagavimui)
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # 20 valandų prognozė (maksimaliam pelnui)
    future_20h = [cur_p + (trend_4h * i) for i in range(1, 81)]
    max_20h = max(future_20h)
    
    # Randame žemiausią tašką per ateinančias 4 valandas (16 žvakių)
    future_4h = [cur_p + (trend_4h * i) for i in range(1, 17)]
    dip_price = min(future_4h)
    
    # Pelnas skaičiuojamas: nuo žemiausio pirkimo taško iki aukščiausio prognozuojamo taško
    potential_profit = (st.session_state.wallet / dip_price) * (max_20h - dip_price)

    # VAIZDAVIMAS
    st.title(f"🚀 Revolut X Scalper V134: {round(st.session_state.wallet, 2)}€")
    
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['time'].tail(16), df['close'].tail(16), label="Istorija (4h)", marker='o')
    
    # Prognozės linija
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 81)]
    ax.plot(future_times, future_20h, '--', color='orange', label="Prognozė (20h)")
    
    # Žymime pirkimo zoną (duobę)
    if trend_4h < 0:
        ax.scatter(df.iloc[-1]['time'] + timedelta(minutes=60), dip_price, color='green', s=100, label="Pirkimo „duobė“")
    
    ax.legend()
    st.pyplot(fig)

    # 3. LOGIKA: Jei rasime duobę, kuri po to atneš 10€ pelną
    if potential_profit >= 10.0:
        # Jei rinka dabar krenta, mes statome pirkimą žemiau
        action_price = dip_price if trend_4h < -0.01 else cur_p
        target_price = max_20h if max_20h > (action_price + 5) else (action_price + (10 / (st.session_state.wallet / action_price)))

        st.success(f"💎 RASTA PROGA! Galimas pelnas: {round(potential_profit, 2)}€")
        
        now_t = datetime.now().strftime("%H:%M")
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Veiksmas": "STATYTI PIRKIMĄ (Limit Buy)",
                "Kaina (PIRKTI)": round(action_price, 2),
                "Tikslas (PARDUOTI)": round(target_price, 2),
                "Pelnas (Prognozė)": f"{round(potential_profit, 2)}€",
                "Instrukcija": "Nustatyk 'Buy Limit' Revolute"
            })
    else:
        st.info(f"Laukiama geresnės kainos. Dabartinis potencialas: {round(potential_profit, 2)}€")

    if st.button("🗑️ VALYTI"): reset_all()
    st.table(pd.DataFrame(st.session_state.trades_log).head(5))
