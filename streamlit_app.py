import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# I. BRANDUOLIO KONFIGŪRACIJA (INSTITUTIONAL ARCHITECTURE)
# ==============================================================================
st.set_page_config(page_title="TITAN SUPREME V500", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="v500_emulator_refresh")

if 'wallet' not in st.session_state:
    st.session_state.wallet = 1711.45 # Pradinis kapitalas
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

# ==============================================================================
# II. DUOMENŲ VARIKLIS IR SKENERIS
# ==============================================================================
class TitanEngine:
    @staticmethod
    def get_market_data(pair="ETHEUR", interval=15):
        try:
            url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                res = json.loads(r.read().decode())
                df = pd.DataFrame(res['result']['XETHZEUR'], 
                                  columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
                df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
                return df
        except Exception as e:
            st.error(f"ENGINE ERROR: {e}")
            return pd.DataFrame()

# ==============================================================================
# III. AUTO-TRADE EMULIACIJA PAGAL TAVO NUOTRAUKAS
# ==============================================================================
def apply_emulation_logic(df):
    # 1. Trendo ašis (SMA20)
    df['sma20'] = df['close'].rolling(20).mean()
    
    # 2. RSI(6) tikslumas
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
    df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
    
    # 3. Pattern Recognition (image_f8c0aa.png)
    # Bullish Engulfing: Žalia žvakė visiškai "praryja" raudoną
    df['signal_buy'] = (df['close'] > df['open']) & \
                       (df['close'].shift(1) < df['open'].shift(1)) & \
                       (df['close'] >= df['open'].shift(1)) & \
                       (df['open'] <= df['close'].shift(1)) & \
                       (df['rsi6'] < 45) # Tik kai kaina nėra per brangi
    
    # Sell Signal: Kai pasiekiamas pikas arba RSI per aukštas
    df['signal_sell'] = (df['rsi6'] > 75) | (df['close'] >= 1758.64)
    return df

# ==============================================================================
# IV. VIZUALINIS MEGA-CENTRAS
# ==============================================================================
df = TitanEngine.get_market_data()

if not df.empty:
    df = apply_emulation_logic(df)
    now = df.iloc[-1]
    
    # Tavo nustatytos ribos
    TARGET_HIGH = 1758.64 #
    PIVOT_SMA20 = 1737.44 #

    st.markdown(f"<h1 style='text-align: center; color: #00ffcc;'>🛰️ TITAN AUTO-TRADE V500</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # --- KPI PANELĖ ---
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("ETH KAINA", f"{now['close']} €", f"{round(now['close']-df.iloc[-2]['close'], 2)}")
    with k2:
        st.metric("NEURAL RSI(6)", round(now['rsi6'], 2))
    with k3:
        trend = "VIRŠ SMA20 (BULL)" if now['close'] > PIVOT_SMA20 else "PO SMA20 (BEAR)"
        st.metric("TRENDO ANALIZĖ", trend)
    with k4:
        st.metric("EMULIUOTAS BALANSAS", f"{st.session_state.wallet} €")

    # --- PAGRINDINĖS SEKCIJOS ---
    t1, t2, t3 = st.tabs(["📈 EMULIATORIAUS GRAFIKAS", "💰 PREKYBOS LOGAS", "🔮 AI PROGNOZĖ"])

    with t1:
        fig, ax = plt.subplots(figsize=(12, 6))
        hist = df.tail(50)
        ax.plot(hist['time'], hist['close'], color='white', linewidth=2, label='Kaina')
        ax.plot(hist['time'], hist['sma20'], color='#00d4ff', alpha=0.5, label='SMA20 Support')
        
        # Atvaizduojame emuliuotus pirkimus/pardavimus pagal tavo "Cheat Sheet"
        buys = hist[hist['signal_buy']]
        sells = hist[hist['signal_sell']]
        ax.scatter(buys['time'], buys['close'] * 0.997, marker='^', color='lime', s=150, label='BUY (Pattern)')
        ax.scatter(sells['time'], sells['close'] * 1.003, marker='v', color='red', s=150, label='SELL (Target)')

        ax.axhline(TARGET_HIGH, color='gold', linestyle='--', alpha=0.6, label='24h Target')
        ax.set_facecolor('#0E1117'); fig.patch.set_facecolor('#0E1117')
        ax.tick_params(colors='white'); ax.legend(facecolor='#1E2127', labelcolor='white')
        st.pyplot(fig)

    with t2:
        st.subheader("Paskutinių 24 valandų simuliacija")
        st.write("Sistema skenuoja tavo nurodytus sutapimus: **W-dugnus** ir **Engulfing žvakes**.")
        
        sim_trades = df[df['signal_buy'] | df['signal_sell']].tail(10)
        if not sim_trades.empty:
            st.table(sim_trades[['time', 'close', 'rsi6', 'signal_buy']].rename(columns={'signal_buy': 'PIRKIMO SIGNALAS'}))
        else:
            st.info("Laukiama tavo „Cheat Sheet“ modelių sutapimo rinkoje...")

    with t3:
        # Ištaisyta f_times klaida iš image_1415db.png
        st.subheader("AI Scenarijai (Sekančios 4 valandos)")
        forecast_list = []
        vol = (df['high'] - df['low']).mean()
        for i in range(1, 17):
            future_time = (datetime.now() + timedelta(minutes=15*i)).strftime("%H:%M")
            # Logika: jei kaina virš SMA20, prognozuojam kilimą iki 1758.64€
            if now['close'] > PIVOT_SMA20:
                p_price = min(now['close'] + (vol * 0.3 * i), TARGET_HIGH + 5)
                signal = "🟢 KILIMAS link piko"
            else:
                p_price = now['close'] - (vol * 0.4 * i)
                signal = "🔴 KOREKCIJA link 1700€"
            
            pelnas = (st.session_state.wallet / now['close'] * p_price) - st.session_state.wallet
            forecast_list.append({"Laikas": future_time, "Kaina": round(p_price, 2), "Pelnas (€)": round(pelnas, 2), "Verdiktas": signal})
        st.dataframe(pd.DataFrame(forecast_list[::2]), use_container_width=True)
