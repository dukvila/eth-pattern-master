import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. SISTEMOS PAMATAI
st.set_page_config(page_title="TITAN V7000", layout="wide")
st_autorefresh(interval=60000, key="titan_v7000")

# Tavo parametrai iš nuotraukų
SMA20_LEVEL = 1737.44
MY_BALANCE = 1711.45

# 2. DUOMENŲ APDOROJIMAS
def get_market_data():
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHEUR&interval=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            df = pd.DataFrame(res['result']['XETHZEUR'], 
                              columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
            df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
            
            # RSI(6) Perpirkimo indikatorius
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
            df['rsi6'] = 100 - (100 / (1 + (gain / loss)))
            
            # STABILI 4H PROGNOZĖ
            y = df['close'].tail(32).values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            future_idx = np.arange(len(y), len(y) + 16)
            preds = slope * future_idx + intercept
            
            return df, preds, slope
    except:
        return pd.DataFrame(), None, 0

# 3. VALDYMO SKYDELIS
df, prediction, slope = get_market_data()

if not df.empty:
    now = df.iloc[-1]
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🚀 TITAN V7000: STRATEGY COMMANDER</h1>", unsafe_allow_html=True)
    
    # ŠONINIS MENIU: TAVO KONTROLĖ
    st.sidebar.header("🛡️ Rizikos Valdymas")
    user_price = st.sidebar.number_input("Tavo Pirkimo Kaina (€):", value=now['close'])
    risk_pct = st.sidebar.slider("Leistina Rizika (%)", 0.5, 3.0, 1.5)
    
    # STOP LOSS
    sl_price = user_price * (1 - risk_pct / 100)
    
    st.sidebar.divider()
    st.sidebar.error(f"STOP LOSS: {round(sl_price, 2)} €")
    
    # PAGRINDINIAI RODIKLIAI
    c1, c2, c3 = st.columns(3)
    c1.metric("ESAMA KAINA", f"{now['close']} €")
    c2.metric("SMA20 AŠIS", f"{SMA20_LEVEL} €")
    c3.metric("BALANSAS", f"{MY_BALANCE} €")

    st.divider()

    # 4. GRAFIKAS (IŠTAISYTA 84 EILUTĖS KLAIDA)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    h = df.tail(60)

    # Tikroji kaina (skliaustai uždaryti!)
    ax.plot(h['time'], h['close'], color='#00ffcc', linewidth=2, label='Rinkos kaina')
    
    # Perpirkimas (Oranžinė)
    ob = h[h['rsi6'] > 70]
    ax.scatter(ob['time'], ob['close'], color='orange', s=60, label='Perpirkimas (RSI>70)')

    # Stabilizuota 4H prognozė
    f_times = [h['time'].iloc[-1] + timedelta(minutes=15 * i) for i in range(1, 17)]
    ax.plot(f_times, prediction, color='#ff00ff', linestyle='--', label='4H Prognozuojamas Trendas')
    
    # Linijos (Stop Loss ir SMA20)
    ax.axhline(sl_price, color='red', linestyle='-.', alpha=0.6, label='Tavo Stop Loss')
    ax.axhline(SMA20_LEVEL, color='white', alpha=0.3, label='SMA20 Pivot')

    # Rekomendaciniai taškai
    ax.scatter(f_times[0], prediction[0], color='lime', marker='P', s=200, label='PIRKTI (Prognozė)')
    ax.scatter(f_times[-1], prediction[-1], color='red', marker='X', s=200, label='PARDUOTI (Tikslas)')

    ax.set_facecolor('#0E1117')
    fig.patch.set_facecolor('#0E1117')
    ax.legend(loc='upper left', fontsize='small')
    st.pyplot(fig)

    # 5. SAVIANALIZĖ IR PALYGINIMAS
    st.subheader("🧬 Analitinis Verdiktas")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📝 Tavo įėjimas vs Prognozė:**")
        target = round(prediction[-1], 2)
        diff = round(target - user_price, 2)
        st.info(f"Tikslas po 4 val.: {target} € | Galimas pokytis: {diff} €")

    with col2:
        st.write("**🤖 Sistemos Mokymasis:**")
        if abs(slope) < 0.05:
            st.warning("Trendas silpnas. Prognozė gali būti netiksli.")
        else:
            st.success("Trendas stabilus. Sistema pasitiki kryptimi.")
