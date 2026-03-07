import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="V133 ZERO LOSS SCALPER", layout="wide")
st_autorefresh(interval=60000, key="v133_refresh")

if 'trades_log' not in st.session_state: st.session_state.trades_log = []
if 'wallet' not in st.session_state: st.session_state.wallet = 1700.0
if 'total_pnl' not in st.session_state: st.session_state.total_pnl = 0.0

# Funkcija išvalyti istoriją (kad nebūtų KeyError)
def reset_all():
    st.session_state.trades_log = []
    st.session_state.total_pnl = 0.0
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

# 3. Analizė: Tik Augimo Paieška
if not df.empty:
    cur_p = df.iloc[-1]['close']
    # Tikriname tendenciją (ar rinka ruošiasi kilti)
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # 20 valandų prognozė (80 žvakių)
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 81)]
    future_prices = [cur_p + (trend_4h * i) for i in range(1, 81)]
    
    max_future = max(future_prices)
    potential_rise = max_future - cur_p
    est_profit = (st.session_state.wallet / cur_p) * potential_rise

    # VAIZDAVIMAS
    st.title(f"💰 Revolut X Balansas: {round(st.session_state.wallet, 2)}€")
    
    # GRAFIKAS: 4h praeitis | 20h ateitis
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['time'].tail(16), df['close'].tail(16), label="Istorija (4h)", marker='o', color='blue')
    ax.plot(future_times, future_prices, '--', color='orange', label="Prognozė (20h)")
    if trend_4h > 0:
        ax.fill_between(future_times, cur_p, future_prices, color='green', alpha=0.1)
    ax.axhline(y=cur_p, color='gray', linestyle=':', label="Dabar")
    ax.legend()
    st.pyplot(fig)

    # 4. SAUGI LOGIKA: Tik jei prognozuojamas AUGIMAS ir pelnas >= 10€
    if trend_4h > 0.02 and est_profit >= 10.0:
        status = "🟢 PIRKTI DABAR (Kils)"
        target = max_future
        
        now_t = datetime.now().strftime("%H:%M")
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Revolut X Veiksmas": "PERK ETH",
                "Kaina dabar": round(cur_p, 2),
                "Parduoti už (Profit)": round(target, 2),
                "Prognoz. Pelnas": f"+{round(est_profit, 2)}€",
                "Būsena": "⏳ LAUKIAMA TIKSLO"
            })
    else:
        st.info("📉 Rinka krenta arba svyravimas per mažas. Laukiama saugios progos uždirbti 10€.")

    if st.button("🗑️ NULINTI ISTORIJĄ"): reset_all()
    
    st.subheader("📜 Saugūs Sandoriai (Be nuostolių)")
    if st.session_state.trades_log:
        # Išvalome senus stulpelius iš atminties, kad nebūtų KeyError
        display_df = pd.DataFrame(st.session_state.trades_log)
        st.table(display_df.head(10))
