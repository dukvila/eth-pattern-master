import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
import time

# Priverstinai nustatome puslapį
st.set_page_config(page_title="ETH-EUR Signalai", layout="wide")

# Funkcija, kuri pati ištaiso ryšio problemas
@st.cache_data(ttl=20)
def get_safe_data():
    try:
        ex = ccxt.binance()
        # Krauname 15min žvakes (kaip tavo nuotraukoje)
        ohlcv = ex.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Saugus indikatorių skaičiavimas
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        df['ema9'] = ta.ema(df['close'], length=9)
        return df.dropna()
    except Exception as e:
        st.error(f"⚠️ Ryšio klaida: {e}")
        return None

# Pagrindinis ekranas
st.title("🚀 Ethereum (ETH/EUR) Realaus Laiko Analizė")

data = get_safe_data()

if data is not None:
    # Rodikliai
    last_price = data['close'].iloc[-1]
    last_rsi = data['rsi'].iloc[-1]
    
    col1, col2 = st.columns(2)
    col1.metric("Esama Kaina", f"{last_price} EUR")
    
    # Tavo taisyklė dėl pirkimo
    if last_rsi < 70:
        col2.success(f"PIRKIMO ZONA (RSI: {last_rsi:.2f})")
    else:
        col2.warning(f"PERPIRKTA (RSI: {last_rsi:.2f})")

    # GRAFIKAS - naudojame Plotly, kad nebūtų jokių "ax.plot" klaidų
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data['time'], open=data['open'], high=data['high'], 
                                 low=data['low'], close=data['close'], name='Kaina'))
    
    # SMA20 ir EMA9 linijos
    fig.add_trace(go.Scatter(x=data['time'], y=data['sma20'], line=dict(color='yellow'), name='SMA 20'))
    fig.add_trace(go.Scatter(x=data['time'], y=data['ema9'], line=dict(color='cyan'), name='EMA 9'))
    
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption(f"Paskutinis atnaujinimas: {datetime.now().strftime('%H:%M:%S')}")
    
    # Automatinis atnaujinimas be tavo įsikišimo
    time.sleep(15)
    st.rerun()
else:
    st.warning("Laukiama duomenų iš biržos...")
