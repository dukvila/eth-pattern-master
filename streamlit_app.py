import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Pagrindinė sąranka
st.set_page_config(page_title="V136 COMPOUND MASTER", layout="wide")
st_autorefresh(interval=60000, key="v136_refresh")

# --- PINIGINĖS VALDYMAS IR REINVESTAVIMAS ---
if 'wallet' not in st.session_state:
    st.session_state.wallet = 1700.0  # Tavo pradinis kapitalas
if 'active_trade' not in st.session_state:
    st.session_state.active_trade = None # Ar pinigai išleisti?
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'total_pelled' not in st.session_state:
    st.session_state.total_pelled = 0.0

def reset_all():
    st.session_state.wallet = 1700.0
    st.session_state.active_trade = None
    st.session_state.trades_log = []
    st.session_state.total_pelled = 0.0
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

# --- PREKYBOS LOGIKA ---
if not df.empty:
    cur_p = df.iloc[-1]['close']
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # Prognozės
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 81)]
    future_prices = [cur_p + (trend_4h * i) for i in range(1, 81)]
    max_20h = max(future_prices)
    
    # 4h "Dugnas" pirkimui
    future_4h = [cur_p + (trend_4h * i) for i in range(1, 17)]
    dip_price = min(future_4h)

    # VAIZDAVIMAS
    st.title(f"💰 Balansas: {round(st.session_state.wallet, 2)}€")
    col1, col2 = st.columns(2)
    col1.metric("Sukauptas pelnas", f"{round(st.session_state.total_pelled, 2)}€")
    col2.metric("ETH Kaina", f"{round(cur_p, 2)}€")

    # Tikriname aktyvų sandorį
    if st.session_state.active_trade:
        trade = st.session_state.active_trade
        st.warning(f"⏳ ĮDARBINTA: {round(trade['invested'], 2)}€. Nupirkta už {trade['buy_p']}€. Tikslas: {trade['target']}€")
        
        # PARDAVIMO TIKRINIMAS (Automatinis reinvestavimas)
        if cur_p >= trade['target']:
            pelnas = (trade['invested'] / trade['buy_p']) * (cur_p - trade['buy_p'])
            st.session_state.wallet += pelnas
            st.session_state.total_pelled += pelnas
            st.session_state.active_trade = None
            st.session_state.trades_log.insert(0, {
                "Laikas": datetime.now().strftime("%H:%M"),
                "Veiksmas": "✅ PARDUOTA",
                "Kaina": round(cur_p, 2),
                "Pelnas": f"+{round(pelnas, 2)}€",
                "Balansas": f"{round(st.session_state.wallet, 2)}€"
            })
            st.balloons()
    
    # GRAFIKAS
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['time'].tail(16), df['close'].tail(16), label="Istorija (4h)", marker='o')
    ax.plot(future_times, future_prices, '--', color='orange', label="Prognozė (20h)")
    if trend_4h < 0:
        ax.scatter(df.iloc[-1]['time'] + timedelta(minutes=60), dip_price, color='green', s=100, label="Pirkimo 'Limit'")
    ax.legend()
    st.pyplot(fig)

    # PIRKIMO PAIEŠKA (Tik jei piniginė ne tuščia)
    potential_profit = (st.session_state.wallet / dip_price) * (max_20h - dip_price)
    
    if st.session_state.active_trade is None:
        if potential_profit >= 10.0:
            buy_limit = dip_price if trend_4h < -0.01 else cur_p
            sell_limit = max_20h if max_20h > (buy_limit + 5) else (buy_limit + (10 / (st.session_state.wallet / buy_limit)))
            
            st.success(f"💎 RASTA PROGA! Galimas pelnas: {round(potential_profit, 2)}€")
            
            if st.button(f"SUDARYTI SANDORĮ UŽ {round(st.session_state.wallet, 2)}€"):
                st.session_state.active_trade = {
                    "buy_p": round(buy_limit, 2),
                    "target": round(sell_limit, 2),
                    "invested": st.session_state.wallet
                }
                st.session_state.trades_log.insert(0, {
                    "Laikas": datetime.now().strftime("%H:%M"),
                    "Veiksmas": "🛒 PIRKTI (Limit)",
                    "Kaina": round(buy_limit, 2),
                    "Tikslas": round(sell_limit, 2),
                    "Būsena": "Laukiama atpirkimo"
                })
                st.rerun()
        else:
            st.info(f"Laukiama progos uždirbti min 10€. Potencialas dabar: {round(potential_profit, 2)}€")

    if st.sidebar.button("🗑️ NULINTI VISKĄ"): reset_all()
    st.subheader("📜 Pinigų Augimo Istorija")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(10))
