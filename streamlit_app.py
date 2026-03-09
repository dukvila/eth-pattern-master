import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="ETH Pro", layout="wide")

st.title("📊 ETH/EUR Realaus laiko analizė")

# Funkcija duomenims gauti
@st.cache_data(ttl=20)
def get_crypto_data():
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Indikatoriai
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        df['ema9'] = ta.ema(df['close'], length=9)
        return df.dropna()
    except Exception as e:
        st.error(f"Klaida: {e}")
        return None

df = get_crypto_data()

if df is not None:
    # Rodikliai viršuje
    last_price = df['close'].iloc[-1]
    last_rsi = df['rsi'].iloc[-1]
    
    c1, c2 = st.columns(2)
    c1.metric("Kaina", f"{last_price} EUR")
    
    if last_rsi < 70:
        c2.success(f"PIRKTI (RSI: {last_rsi:.2f})")
    else:
        c2.warning(f"PERPIRKTA (RSI: {last_rsi:.2f})")

    # Grafikas (Naudojame Plotly, kad nebūtų skliaustelių klaidų)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df['time'], open=df['open'], high=df['high'], 
                                 low=df['low'], close=df['close'], name='Žvakės'))
    fig.add_trace(go.Scatter(x=df['time'], y=df['sma20'], line=dict(color='yellow'), name='SMA 20'))
    fig.add_trace(go.Scatter(x=df['time'], y=df['ema9'], line=dict(color='cyan'), name='EMA 9'))
    
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption(f"Atnaujinta: {datetime.now().strftime('%H:%M:%S')}")
