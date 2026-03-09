import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="ETH Analizė", layout="wide")

# Funkcija patikrinti, ar viskas įrašyta
def check_setup():
    st.write("🔍 Tikrinama sistema...")
    try:
        import ccxt
        import pandas_ta
        st.success("Sistemos bibliotekos paruoštos!")
    except ImportError as e:
        st.error(f"Trūksta bibliotekos: {e}")

st.title("📊 ETH/EUR Realaus laiko grafikas")

# Debug mygtukas (jei nieko nematysi, paspausk)
if st.checkbox("Rodyti sistemos būseną"):
    check_setup()

@st.cache_data(ttl=15)
def get_data():
    try:
        ex = ccxt.binance()
        # Bandom gauti duomenis
        bars = ex.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Skaičiuojam indikatorius
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        df['ema9'] = ta.ema(df['close'], length=9)
        return df
    except Exception as e:
        st.error(f"Nepavyko gauti duomenų iš Binance: {e}")
        return None

data = get_data()

if data is not None:
    # Rodikliai
    c1, c2 = st.columns(2)
    c1.metric("Kaina", f"{data['close'].iloc[-1]} EUR")
    rsi_val = data['rsi'].iloc[-1]
    
    if rsi_val < 70:
        c2.success(f"RSI: {rsi_val:.2f} (PIRKTI)")
    else:
        c2.warning(f"RSI: {rsi_val:.2f} (PERPIRKTA)")

    # Grafikas
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data['time'], open=data['open'], high=data['high'], 
                                 low=data['low'], close=data['close'], name='ETH'))
    fig.add_trace(go.Scatter(x=data['time'], y=data['sma20'], line=dict(color='yellow'), name='SMA20'))
    fig.add_trace(go.Scatter(x=data['time'], y=data['ema9'], line=dict(color='cyan'), name='EMA9'))
    fig.update_layout(template="plotly_dark", height=600)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Laukiama duomenų... Jei langas tuščias ilgai, patikrink internetą.")
