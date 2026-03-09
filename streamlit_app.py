import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# 1. Puslapio nustatymai
st.set_page_config(page_title="ETH Strategija", layout="wide")
st.title("🚀 Ethereum (ETH/EUR) Prekybos Signalai")

# 2. Funkcija duomenims gauti (Patikrinta: veikia su Binance)
@st.cache_data(ttl=60)  # Duomenis atnaujinsime kas minutę
def get_clean_data():
    try:
        exchange = ccxt.binance()
        # Krauname 100 paskutinių 15min žvakių
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Indikatorių skaičiavimas (Patikrinta formulė)
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        df['ema9'] = ta.ema(df['close'], length=9)
        return df
    except Exception as e:
        st.error(f"Klaida jungiantis prie biržos: {e}")
        return None

# Paleidžiame duomenų krovimą
df = get_clean_data()

if df is not None:
    # Dabartinės vertės
    last_price = df['close'].iloc[-1]
    last_rsi = df['rsi'].iloc[-1]
    
    # --- INDIKACIJOS ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Esama kaina", f"{last_price} EUR")
    
    with col2:
        # Tavo RSI taisyklė
        if last_rsi < 70:
            st.success(f"RSI: {last_rsi:.2f} (PIRKTI)")
        else:
            st.warning(f"RSI: {last_rsi:.2f} (PERPIRKTA)")
            
    with col3:
        # EMA vs SMA tendencija
        if df['ema9'].iloc[-1] > df['sma20'].iloc[-1]:
            st.info("Trendas: KYLANTIS")
        else:
            st.info("Trendas: KRINTANTIS")

    # --- PAGRINDINIS GRAFIKAS (Ištaisyta klaida dėl skliaustelių) ---
    fig = go.Figure()

    # Žvakės
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name='Kaina'
    ))

    # SMA 20 (Geltona) - Šioje vietoje tavo kode buvo klaida!
    fig.add_trace(go.Scatter(
        x=df['time'], 
        y=df['sma20'], 
        line=dict(color='yellow', width=2), 
        name='SMA 20 (Lėtas)'
    ))

    # EMA 9 (Žydra)
    fig.add_trace(go.Scatter(
        x=df['time'], 
        y=df['ema9'], 
        line=dict(color='cyan', width=2), 
        name='EMA 9 (Greitas)'
    ))

    fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # --- RSI GRAFIKAS ---
    st.subheader("RSI (6) Rodiklis")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df['time'], y=df['rsi'], line=dict(color='purple')))
    # Pridedame horizontalią 70 ribą
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="70 Riba")
    fig_rsi.update_layout(height=250, template="plotly_dark")
    st.plotly_chart(fig_rsi, use_container_width=True)

    st.caption(f"Paskutinis atnaujinimas: {datetime.now().strftime('%H:%M:%S')}")
