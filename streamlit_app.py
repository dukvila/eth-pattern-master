import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="REVOLUT X SCALPER V132", layout="wide")
st_autorefresh(interval=60000, key="v132_refresh")

if 'trades_log' not in st.session_state: st.session_state.trades_log = []
if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'total_pnl' not in st.session_state: st.session_state.total_pnl = 0.0

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

# 3. Skalpingas ir Prognozė
if not df.empty:
    cur_p = df.iloc[-1]['close']
    # Analizuojame 4 valandų trendą (16 žvakių)
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # Generuojame 20 valandų (80 žvakių) ateities taškus
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 81)]
    future_prices = [cur_p + (trend_4h * i) for i in range(1, 81)]
    
    # Randame geriausią pirkimo ir pardavimo kainą per 20h
    min_future = min(future_prices)
    max_future = max(future_prices)
    
    st.title(f"🚀 Revolut X Scalper: {round(st.session_state.wallet, 2)}€")
    st.write(f"Dabartinė ETH kaina: **{round(cur_p, 2)}€**")

    # GRAFIKAS: 4h praeitis | 20h ateitis
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['time'].tail(16), df['close'].tail(16), label="Istorija (4h)", marker='o', color='blue')
    ax.plot(future_times, future_prices, '--', color='orange', label="Prognozė (20h)")
    ax.axhline(y=cur_p, color='gray', linestyle=':', label="Dabartinė kaina")
    ax.fill_between(future_times, cur_p, future_prices, where=(pd.Series(future_prices) > cur_p), color='green', alpha=0.1)
    ax.fill_between(future_times, cur_p, future_prices, where=(pd.Series(future_prices) < cur_p), color='red', alpha=0.1)
    ax.legend()
    st.pyplot(fig)

    # 4. LOGIKA: 10€ pelno paieška artimiausiu metu
    potential_rise = max_future - cur_p
    potential_drop = cur_p - min_future
    
    # Paskaičiuojame kiekviena kryptimi galimą pelną
    profit_buy = (st.session_state.wallet / cur_p) * potential_rise
    profit_sell = (st.session_state.wallet / cur_p) * potential_drop

    col1, col2 = st.columns(2)
    
    # Jei trendas kyla - siūlome pirkti dabar
    if trend_4h > 0 and profit_buy >= 10.0:
        col1.success(f"📈 PROGA PIRKTI! Galimas pelnas: {round(profit_buy, 2)}€")
        action, target, est_p = "🟢 PIRKTI", max_future, profit_buy
    # Jei trendas krenta - siūlome parduoti dabar ir atpirkti pigiau
    elif trend_4h < 0 and profit_sell >= 10.0:
        col2.warning(f"📉 PROGA PARDUOTI! Galimas pelnas: {round(profit_sell, 2)}€")
        action, target, est_p = "🔴 PARDUOTI", min_future, profit_sell
    else:
        action = None
        st.info("Laukiama progos su bent 10€ pelno potencialu...")

    # Registruojame sandorį
    if action:
        now_t = datetime.now().strftime("%H:%M")
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Revolut X Veiksmas": "PERK Į ETH" if action == "🟢 PIRKTI" else "PARDUOK Į EUR",
                "Kaina dabar": round(cur_p, 2),
                "Tikslas (Profit)": round(target, 2),
                "Prognoz. Pelnas": f"{round(est_p, 2)}€",
                "Būsena": "⏳ VYKDYTI REVOLUTE"
            })

    st.subheader("📜 Artimiausių sandorių planas")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(10))
