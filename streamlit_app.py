import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# Puslapio nustatymai - PRIVALOMA DALIS
st.set_page_config(page_title="ETH-Master", layout="wide")
st.title("📈 Ethereum (ETH/EUR) 15m Grafikas")

# Funkcija duomenims gauti
@st.cache_data(ttl=20)
def get_crypto_data():
    try:
        # Jungiamės prie Binance
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Apskaičiuojame rodiklius (RSI 6, SMA 20, EMA 9)
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        df['ema9'] = ta.ema(df['close'], length=9)
        return df
    except Exception as e:
        return None

df = get_crypto_data()

if df is not None:
    # Dabartinė būsena
    last_rsi = df['rsi'].iloc[-1]
    last_price = df['close'].iloc[-1]

    # Signalas viršuje
    col1, col2 = st.columns(2)
    col1.metric("Kaina", f"{last_price} EUR")
    
    if last_rsi < 70:
        col2.success(f"✅ RSI: {last_rsi:.2f} - SAUGI ZONA PIRKTI")
    else:
        col2.warning(f"⚠️ RSI: {last_rsi:.2f} - PERPIRKTA (ATSARGIAI)")

    # GRAFIKAS (Naudojame Plotly, kad nebūtų ax.plot klaidų)
    fig = go.Figure()
    
    # Žvakės
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name='Kaina'
    ))

    # SMA 20 (Geltona)
    fig.add_trace(go.Scatter(x=df['time'], y=df['sma20'], 
                             line=dict(color='yellow', width=2), name='SMA 20'))
    
    # EMA 9 (Žydra)
    fig.add_trace(go.Scatter(x=df['time'], y=df['ema9'], 
                             line=dict(color='cyan', width=2), name='EMA 9'))

    fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # RSI Grafikas apačioje
    st.subheader("RSI (6) Indikatorius")
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=df['time'], y=df['rsi'], line=dict(color='purple')))
    rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
    rsi_fig.update_layout(height=200, template="plotly_dark")
    st.plotly_chart(rsi_fig, use_container_width=True)
    
    st.caption(f"Atnaujinta: {datetime.now().strftime('%H:%M:%S')}")
else:
    st.error("Nepavyko gauti duomenų. Patikrink interneto ryšį arba Binance pasiekiamumą.")
