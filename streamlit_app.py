import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# 1. Konfigūracija
st.set_page_config(page_title="ETH Pattern Master", layout="wide")
st.title("📊 Ethereum (ETH/EUR) Analizė")

# 2. Duomenų gavimas iš Binance API
@st.cache_data(ttl=30)
def get_live_data():
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Indikatoriai (RSI 6, SMA 20, EMA 9)
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        df['ema9'] = ta.ema(df['close'], length=9)
        return df
    except Exception as e:
        st.error(f"Klaida gaunant duomenis: {e}")
        return None

df = get_live_data()

if df is not None:
    # Dabartinės reikšmės
    last_row = df.iloc[-1]
    curr_rsi = last_row['rsi']
    curr_price = last_row['close']

    # 3. Viršutinė panelė
    c1, c2, c3 = st.columns(3)
    c1.metric("Kaina", f"{curr_price} EUR")
    c2.metric("RSI (6)", f"{curr_rsi:.2f}")
    
    # Tavo RSI < 70 taisyklė
    if curr_rsi < 70:
        c3.success("✅ PIRKIMO ZONA (RSI < 70)")
    else:
        c3.warning("⚠️ PERPIRKTA (RSI > 70)")

    # 4. Pagrindinis Grafikas (SUTVARKYTA: jokių ax.plot klaidų)
    fig = go.Figure()
    
    # Žvakės
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name='ETH'
    ))

    # SMA 20 (Geltona linija)
    fig.add_trace(go.Scatter(x=df['time'], y=df['sma20'], line=dict(color='yellow', width=2), name='SMA 20'))
    
    # EMA 9 (Žydra linija)
    fig.add_trace(go.Scatter(x=df['time'], y=df['ema9'], line=dict(color='cyan', width=2), name='EMA 9'))

    fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # 5. RSI Grafikas apačioje
    st.subheader("RSI Indikatorius")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df['time'], y=df['rsi'], line=dict(color='purple')))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
    fig_rsi.update_layout(height=250, template="plotly_dark")
    st.plotly_
