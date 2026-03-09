import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# 1. Puslapio konfigūracija
st.set_page_config(page_title="ETH Master", layout="wide")
st.title("🚀 Ethereum (ETH/EUR) Analizatorius")

# 2. Duomenų gavimas iš Binance
@st.cache_data(ttl=30)
def get_data():
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Indikatoriai: RSI(6), SMA(20), EMA(9)
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        df['ema9'] = ta.ema(df['close'], length=9)
        return df
    except Exception as e:
        st.error(f"Klaida jungiantis prie Binance: {e}")
        return None

df = get_data()

if df is not None:
    # Dabartiniai skaičiai
    last_price = df['close'].iloc[-1]
    last_rsi = df['rsi'].iloc[-1]

    # Viršutinė info juosta
    c1, c2, c3 = st.columns(3)
    c1.metric("Kaina", f"{last_price} EUR")
    c2.metric("RSI (6)", f"{last_rsi:.2f}")
    
    # Tavo taisyklė: RSI < 70 = PIRKTI
    if last_rsi < 70:
        c3.success("✅ PIRKIMO ZONA")
    else:
        c3.warning("⚠️ PERPIRKTA (LAUKTI)")

    # 3. PAGRINDINIS GRAFIKAS (SUTVARKYTAS - jokių ax.plot klaidų)
    fig = go.Figure()

    # Žvakės
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name='Kaina'
    ))

    # SMA 20 (Geltona linija) - ČIA BUVO TAVO KLAIDA NUOTRAUKOJE
    fig.add_trace(go.Scatter(
        x=df['time'], 
        y=df['sma20'], 
        line=dict(color='yellow', width=2), 
        name='SMA 20'
    ))

    # EMA 9 (Žydra linija)
    fig.add_trace(go.Scatter(
        x=df['time'], 
        y=df['ema9'], 
        line=dict(color='cyan', width=2), 
        name='EMA 9'
    ))

    fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # 4. RSI Grafikas
    st.subheader("RSI (6) Indikatorius")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df['time'], y=df['rsi'], line=dict(color='purple')))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="70 Riba")
    fig_rsi.update_layout(height=250, template="plotly_dark")
    st.plotly_chart(fig_rsi, use_container_width=True)

    st.caption(f"Atnaujinta: {datetime.now().strftime('%H:%M:%S')}")
