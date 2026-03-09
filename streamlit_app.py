import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# Puslapio nustatymai
st.set_page_config(page_title="ETH Signalų Meistras", layout="wide")
st.title("📈 Ethereum (ETH/EUR) Analizatorius")

# 1. Funkcija duomenims gauti
def get_data(symbol='ETH/EUR', timeframe='15m'):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Techniniai indikatoriai
    df['RSI'] = ta.rsi(df['close'], length=6)
    df['SMA20'] = ta.sma(df['close'], length=20)
    return df

try:
    # Gauname duomenis
    df = get_data()
    last_row = df.iloc[-1]
    rsi_val = last_row['RSI']
    price = last_row['close']

    # 2. Viršutinė info skiltis (Metrikos)
    col1, col2, col3 = st.columns(3)
    col1.metric("Esama Kaina", f"{price} EUR")
    col2.metric("RSI (6)", f"{rsi_val:.2f}")
    
    # Logika, kurios prašei:
    if rsi_val < 70:
        status = "✅ VERTA PIRKTI (Saugi zona)"
        color = "green"
    elif 70 <= rsi_val < 80:
        status = "⚠️ STEBĖTI (Rinka kaista)"
        color = "orange"
    else:
        status = "❌ NEBEPIRKTI (Perpirkta)"
        color = "red"
        
    col3.markdown(f"### <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)

    # 3. Grafiko braižymas (naudojant Plotly, kad būtų interaktyvu)
    fig = go.Figure()

    # Žvakių grafikas
    fig.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name='ETH/EUR'
    ))

    # SMA20 linija (kurioje buvo klaida)
    fig.add_trace(go.Scatter(
        x=df['time'], 
        y=df['SMA20'], 
        line=dict(color='yellow', width=1.5), 
        name='SMA 20'
    ))

    fig.update_layout(title="ETH/EUR 15min Grafikas", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)

    # 4. RSI Grafikas apačioje
    st.subheader("RSI Indikatorius")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df['time'], y=df['RSI'], line=dict(color='purple')))
    # Raudona riba ties 70
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Perpirkta (70)")
    fig_rsi.update_layout(height=300)
    st.plotly_chart(fig_rsi, use_container_width=True)

    st.write(f"Paskutinis atnaujinimas: {datetime.now().strftime('%H:%M:%S')}")

except Exception as e:
    st.error(f"Klaida gaunant duomenis: {e}")

# Automatinis persikrovimas kas 30 sekundžių
st.empty()
time_left = 30
if st.button('Atnaujinti dabar'):
    st.rerun()
