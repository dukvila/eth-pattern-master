import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# Puslapio konfigūracija
st.set_page_config(page_title="ETH/EUR Analizatorius", layout="wide")

st.title("📊 Ethereum (ETH/EUR) RSI Strategija")

# 1. Funkcija duomenų gavimui
def gauti_duomenis():
    try:
        exchange = ccxt.binance()
        # Gauname 100 paskutinių 15min žvakių
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Pridedame indikatorius (RSI 6 ir SMA 20)
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        return df
    except Exception as e:
        st.error(f"Nepavyko prisijungti prie biržos: {e}")
        return None

df = gauti_duomenis()

if df is not None:
    paskutine_kaina = df['close'].iloc[-1]
    dabartinis_rsi = df['rsi'].iloc[-1]

    # 2. Indikacijų blokas
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Esama Kaina", f"{paskutine_kaina} EUR")
        
    with col2:
        # Tavo strategijos logika: RSI < 70 yra pirkimo zona
        if dabartinis_rsi < 70:
            st.success(f"RSI: {dabartinis_rsi:.2f} — ✅ VERTA PIRKTI (dar nepasiekė 70)")
        else:
            st.warning(f"RSI: {dabartinis_rsi:.2f} — ⚠️ ATSARGIAI (perpirkta, virš 70)")

    # 3. Pagrindinis grafikas (Kaina + SMA20)
    fig = go.Figure()
    
    # Žvakės
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'], 
        low=df['low'], close=df['close'], name='Kaina'
    ))
    
    # SMA20 linija (čia buvo klaida tavo nuotraukoje)
    fig.add_trace(go.Scatter(
