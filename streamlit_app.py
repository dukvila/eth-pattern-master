import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# Puslapio nustatymai
st.set_page_config(page_title="ETH Strategija", layout="wide")
st.title("🚀 ETH/EUR: RSI + SMA + EMA Strategija")

# 1. Duomenų gavimas
def get_data():
    try:
        exchange = ccxt.binance()
        # Imame 100 paskutinių 15min žvakių
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Indikatoriai
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        df['ema9'] = ta.ema(df['close'], length=9) # Greitoji EMA linija
        return df
    except Exception as e:
        st.error(f"Klaida jungiantis prie biržos: {e}")
        return None

df = get_data()

if df is not None:
    last_price = df['close'].iloc[-1]
    last_rsi = df['rsi'].iloc[-1]

    # 2. Sprendimo blokas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Esama Kaina", f"{last_price} EUR")
    with col2:
        if last_rsi < 70:
            st.success(f"✅ VERTA PIRKTI: RSI yra {last_rsi:.2f} (Saugi zona)")
        else:
            st.warning(f"⚠️ ATSARGIAI: RSI yra {last_rsi:.2f} (Rinka perkaista)")

    # 3. Pagrindinis grafikas
    fig = go.Figure()

    # Žvakės
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name='Kaina'
    ))

    # SMA 20 (Geltona linija - lėtesnė)
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['sma20'], 
        line=dict(color='yellow', width=2), name='SMA 20'
    ))

    # EMA 9 (Žydra linija - greita, reaguoja iškart)
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['ema9'], 
        line=dict(color='cyan', width=2), name='EMA 9'
    ))

    fig.update_layout(xaxis_rangeslider_visible=False, height=500, title="Kaina + SMA20 + EMA9")
    st.plotly_chart(fig, use_container_width=True)

    # 4. RSI Grafikas
    st.subheader("RSI (6) Indikatorius")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df['time'], y=df['rsi'], line=dict(color='purple'), name='RSI'))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="70 Riba")
    fig_rsi.update_layout(height=250)
    st.plotly_chart(fig_rsi, use_container_width=True)

    st.caption(f"Atnaujinta: {datetime.now().strftime('%H:%M:%S')}")
