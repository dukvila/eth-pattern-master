import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Pagrindinė sąranka
st.set_page_config(page_title="BOSO MASTER V130", layout="wide")
st_autorefresh(interval=60000, key="v130_refresh")

if 'trades_log' not in st.session_state: st.session_state.trades_log = []
if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0 # Tavo balansas iš foto
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

# 3. Analizė ir Grafikų kūrimas
if not df.empty:
    cur_p = df.iloc[-1]['close']
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16 # 4h tendencija
    
    # 20 valandų prognozė (80 žvakių)
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 81)]
    future_prices = [cur_p + (trend_4h * i) for i in range(1, 81)]
    predicted_change = trend_4h * 80
    est_profit = (st.session_state.wallet / cur_p) * abs(predicted_change)

    # VAIZDAVIMAS
    st.title(f"💼 Balansas: {round(st.session_state.wallet, 2)}€")
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'].tail(16), df['close'].tail(16), label="Istorija (4h)", marker='o')
    ax.plot(future_times, future_prices, '--', color='orange', label="Prognozė (20h)")
    ax.set_title(f"ETH Prognozė: {'KILIMAS' if trend_4h > 0 else 'KRITIMAS'}")
    ax.legend()
    st.pyplot(fig)

    # LOGIKA: AR VERTA ĮEITI?
    if est_profit >= 10.0:
        if trend_4h > 0:
            status = "🟢 PIRKTI (Kils)"
            target = cur_p + abs(predicted_change)
        else:
            status = "🔴 PARDUOTI (Kris)"
            target = cur_p - abs(predicted_change)
            
        now_t = datetime.now().strftime("%H:%M")
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Veiksmas": status,
                "Kaina dabar": round(cur_p, 2),
                "Tikslas": round(target, 2),
                "Prognoz. Pelnas": f"{round(est_profit, 2)}€",
                "Rezultatas": "⏳ Tikrinama..."
            })

    st.subheader("📜 Sandorių žurnalas")
    st.table(pd.DataFrame(st.session_state.trades_log).head(10))
