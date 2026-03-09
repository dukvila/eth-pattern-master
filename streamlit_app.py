import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import urllib.request, json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# I. QUANTUM SISTEMINĖ ARCHITEKTŪRA (MEGA-CENTRAS)
# ==============================================================================
st.set_page_config(page_title="TITAN QUANT-CORE V600", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=30000, key="quant_core_refresh")

if 'wallet' not in st.session_state: 
    st.session_state.wallet = 1711.45 # Tavo portfelis

# ==============================================================================
# II. DUOMENŲ AGREGACIJA (MULTI-LAYER SCAN)
# ==============================================================================
class QuantDataEngine:
    @staticmethod
    def get_live_ohlc(pair="ETHEUR", interval=15):
        try:
            url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                res = json.loads(r.read().decode())
                data = res['result']['XETHZEUR']
                df = pd.DataFrame(data, columns=['t','open','high','low','close','vwap','vol','count']).astype(float)
                df['time'] = pd.to_datetime(df['t'], unit='s') + timedelta(hours=2)
                return df
        except Exception as e:
            st.error(f"ENGINE CRITICAL ERROR: {e}")
            return pd.DataFrame()

# ==============================================================================
# III. HOLOGRAFINIS MATEMATINIS MODELIS (ADVANCED MATH)
# ==============================================================================
def apply_holographic_logic(df):
    # Tikslus RSI(6) pagal Binance
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
    df['rsi6'] = 100 - (100 / (1 + (gain / loss)))

    # Tavo SMA20 stabilizatorius
    df['sma20'] = df['close'].rolling(20).mean()
    
    # EMA kaskada (Trendas)
    df['ema8'] = df['close'].ewm(span=8, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    return df

# ==============================================================================
# IV. VAIZDINĖ REVOLIUCIJA (TITAN HOLOGRAPHIC)
# ==============================================================================
df = QuantDataEngine.get_live_ohlc()

if not df.empty:
    df = apply_holographic_logic(df)
    now = df.iloc[-1]
    
    # Atramos taškai iš tavo nuotraukų
    TARGET_HIGH = 1758.64
    TARGET_LOW = 1660.00
    PIVOT_SMA20 = 1737.44

    # --- Pasaulinio lygio Mega-centras ---
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🚀 TITAN HOLOGRAPHIC V600</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # --- INFORMACINIS SKYDAS ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("SPOT KAINA", f"{now['close']} €", f"{round(now['close']-df.iloc[-2]['close'], 2)}")
    with c2:
        rsi_color = "🟢" if now['rsi6'] < 70 else "🔴"
        st.metric("RSI(6) IMPULSAS", f"{round(now['rsi6'], 2)}", rsi_color)
    with c3:
        trend = "🟢 BULIAI (Palaikymas)" if now['close'] > PIVOT_SMA20 else "🔴 MEŠKOS (Spaudimas)"
        st.metric("TRENDAS (SMA20)", trend)
    with c4:
        st.metric("TVARKOMAS BALANSAS", f"{st.session_state.wallet} €")

    # --- MULTI-DIMENSINIS ATVAZDAVIMAS (TABS) ---
    tab1, tab2, tab3 = st.tabs(["🧬 interaktyvi 3D HOLOGRAMA", "🕒 Detali 4H Prognozė", "🛡️ RIZIKOS MATRICA"])

    with tab1:
        # ČIA IŠTAISYTA VIZUALIZACIJA (IŠ 2D Į 3D HOLOGRAMĄ)
        hist = df.tail(40) # Imame 40 žvakių gylį hologramos formavimui
        
        fig = go.Figure()
        
        # Pagrindinis Interaktyvus Kripto-Cilindras
        fig.add_trace(go.Scatter3d(
            x=hist['time'],
            y=hist['rsi6'], # Y ašis: Impulsas (RSI)
            z=hist['close'], # Z ašis: Kaina
            mode='lines+markers',
            marker=dict(
                size=6,
                color=hist['rsi6'], # Spalva keičiasi pagal RSI impulsą
                colorscale='Viridis',
                opacity=0.8
            ),
            line=dict(
                color='#00ffcc',
                width=4
            ),
            label='Interaktyvus Kelias'
        ))
        
        # Horizontalūs Atramos Sluoksniai (3D plokštumos)
        # 1. Tavo 24h Pikas: 1,758.64€
        fig.add_trace(go.Scatter3d(
            x=hist['time'], y=hist['rsi6']*0 + 100, z=hist['close']*0 + TARGET_HIGH,
            mode='lines', line=dict(color='gold', width=2), label=f'TARGET HIGH {TARGET_HIGH}€'
        ))
        
        # 2. Tavo SMA20 Ašis: 1,737.44€
        fig.add_trace(go.Scatter3d(
            x=hist['time'], y=hist['rsi6']*0, z=hist['close']*0 + PIVOT_SMA20,
            mode='lines', line=dict(color='red', width=2), label=f'SMA20Support {PIVOT_SMA20}€'
        ))
        
        # 3. Saugumo Zona: 1,660.00€
        fig.add_trace(go.Scatter3d(
            x=hist['time'], y=hist['rsi6']*0, z=hist['close']*0 + TARGET_LOW,
            mode='lines', line=dict(color='cyan', width=1, dash='dash'), label=f'TARGET LOW {TARGET_LOW}€'
        ))

        fig.update_layout(
            scene=dict(
                xaxis_title='Laikas (3 val. gylis)',
                yaxis_title='Impulsas (RSI)',
                zaxis_title='Kaina (€)',
                bgcolor='#0E1117'
            ),
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117',
            font=dict(color='white'),
            margin=dict(l=0, r=0, b=0, t=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Algoritmine 4 Valandų Scenarijų Matrica")
        forecast_list = []
        atr = (df['high'] - df['low']).mean()
        
        for i in range(1, 17):
            future_time = (datetime.now() + timedelta(minutes=15*i)).strftime("%H:%M")
            # Logika pagal tavo duomenis: kilimas link 1,758€ arba korekcija iki 1,700€
            if now['close'] > PIVOT_SMA20 and rsi_val < 72:
                p_price = now['close'] + (atr * 0.4 * i)
                signal = "🟢 KILIMAS (Link Piko)"
            else:
                p_price = now['close'] - (atr * 0.3 * i)
                signal = "🔴 KOREKCIJA (Link SMA20)"
            
            p_pelnas = (st.session_state.wallet / now['close'] * p_price) - st.session_state.wallet
            forecast_list.append({"Laikas": future_time, "Kaina (€)": round(p_price, 2), "Pelnas (€)": f"+{round(p_pelnas, 2)}" if p_pelnas > 0 else f"{round(p_pelnas, 2)}", "Verdiktas": signal})
        st.dataframe(pd.DataFrame(forecast_list[::2]), use_container_width=True)

    with tab3:
        st.subheader("Institucinė Rizikos Kontrolė")
        c_l, c_r = st.columns(2)
        with c_l:
            st.warning(f"⚠️ **Target High: {TARGET_HIGH} €**")
            st.caption(f"Kaina šiuo metu testuoja paros piką. Galimas staigus apsisukimas, jei RSI pramuš 75-80 ribą.")
        with c_r:
            st.success(f"🛡️ **SMA20 Support: {PIVOT_SMA20} €**")
            st.caption(f"Tavo pagrindinė ašis. Kol kaina virš jos, buliai dominuoja rinkoje.")
