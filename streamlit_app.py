import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

st.set_page_config(page_title="ETH Live", layout="wide")
st.title("📊 ETH/EUR 15m Analizė")

# Saugus duomenų gavimas
def get_data():
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Tik tai, ko tau reikia
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        return df
    except Exception as e:
        st.error(f"Klaida: {e}")
        return None

df = get_data()

if df is not None:
    last_rsi = df['rsi'].iloc[-1]
    st.metric("Esamas RSI(6)", f"{last_rsi:.2f}")

    if last_rsi < 70:
        st.success("✅ PIRKIMO ZONA")
    else:
        st.warning("⚠️ PERPIRKTA")

    # Paprastas interaktyvus grafikas
    fig = go.Figure(data=[go.Candlestick(x=df['time'],
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'], name='ETH')])
    
    fig.add_trace(go.Scatter(x=df['time'], y=df['sma20'], line=dict(color='yellow'), name='SMA20'))
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
