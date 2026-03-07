import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Konfigūracija
st.set_page_config(page_title="ETH V128 BULL VISION", layout="wide")
st_autorefresh(interval=60000, key="v128_refresh")

# --- ATMINTIES VALDYMAS ---
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []
if 'wallet' not in st.session_state:
    st.session_state.wallet = 300.0 
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0

def reset_all():
    st.session_state.trades_log = []
    st.session_state.total_pnl = 0.0
    st.rerun()

# --- ŠONINIS MENIU ---
with st.sidebar:
    st.header("🕹️ Revolut X Kontrolė")
    st.session_state.wallet = st.number_input("Piniginė (EUR):", value=float(st.session_state.wallet), step=10.0)
    if st.button("🗑️ NULINTI VISKĄ"):
        reset_all()
    st.success("Strategija: TIK AUGIMAS 📈")

# 2. Duomenų gavimas (Kraken API)
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

# 3. Logika ir Atvaizdavimas
if not df.empty:
    cur_p = df.iloc[-1]['close']
    # Skaičiuojame trendą pagal paskutines 16 žvakių (4 valandas)
    trend_4h = (df['close'].iloc[-1] - df['close'].iloc[-16]) / 16
    
    # Sandorių tikrinimas (Ištaiso KeyError)
    valid_log = []
    for t in st.session_state.trades_log:
        if not all(k in t for k in ['Laikas', 'Veiksmas', 'Pirkti už', 'Tikslas']):
            continue
        if t['Rezultatas'] == "⏳ Tikrinama...":
            if cur_p >= t['Tikslas']:
                pelnas = (t['Investuota'] / t['Pirkti už']) * (cur_p - t['Pirkti už'])
                t['Rezultatas'] = f"✅ +{round(pelnas, 2)}€"
                st.session_state.total_pnl += pelnas
                st.session_state.wallet += pelnas
        valid_log.append(t)
    st.session_state.trades_log = valid_log

    # --- PAGRINDINIAI RODIKLIAI ---
    st.title(f"💼 Balansas: {round(st.session_state.wallet, 2)}€")
    st.write(f"🕒 Lietuvos laikas: {datetime.now().strftime('%H:%M:%S')} | ETH: {round(cur_p, 2)}€")

    # --- PROGNOZĖS GRAFIKAS (4 valandos praeities, 20 valandų ateities) ---
    # 4 valandos praeities = 16 žvakių po 15min
    # 20 valandų ateities = 80 žvakių po 15min
    future_times = [df.iloc[-1]['time'] + timedelta(minutes=15 * i) for i in range(1, 81)]
    future_prices = [cur_p + (trend_4h * i) for i in range(1, 81)]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['time'].tail(16), df['close'].tail(16), label="Istorija (4h)", marker='o', markersize=4)
    ax.plot(future_times, future_prices, '--', color='orange', label="Prognozė (20h)")
    ax.set_title("ETH/EUR 20 valandų prognozė pagal 4h tendenciją")
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)

    # --- TIK AUGIMO LOGIKA IR 10€ FILTRAS ---
    predicted_rise_20h = trend_4h * 80 # Kiek pakils per 20 valandų
    est_profit = (st.session_state.wallet / cur_p) * predicted_rise_20h
    
    if trend_4h > 0.03 and est_profit >= 10.0:
        signal = "🟢 PIRKTI"
        target = cur_p + (trend_4h * 16) # Trumpalaikis tikslas (po 4h)
        
        now_t = datetime.now().strftime("%H:%M")
        if not st.session_state.trades_log or st.session_state.trades_log[0]['Laikas'] != now_t:
            st.session_state.trades_log.insert(0, {
                "Laikas": now_t,
                "Veiksmas": signal,
                "Investuota": round(st.session_state.wallet, 2),
                "Pirkti už": round(cur_p, 2),
                "Tikslas": round(target, 2),
                "Prognozė (20h)": f"+{round(est_profit, 2)}€",
                "Rezultatas": "⏳ Tikrinama..."
            })

    st.subheader("📜 Boso Sandorių Žurnalas")
    if st.session_state.trades_log:
        st.table(pd.DataFrame(st.session_state.trades_log).head(10))
    else:
        st.info("Laukiama prognozuojamo augimo (min. 10€ pelnas per 20h).")
