import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# 1. Priverstinis teksto rodymas (kad žinotume, jog programa veikia)
st.write("🔄 Programa paleista. Tikrinami duomenys...")

# 2. Bibliotekų tikrinimas
try:
    import ccxt
    import pandas_ta
    st.sidebar.success("✅ Bibliotekos rastos")
except Exception as e:
    st.error(f"❌ Trūksta bibliotekų! Įsitikink, kad faile requirements.txt įrašei: ccxt, pandas_ta. Klaida: {e}")
    st.stop()

# 3. Saugi duomenų gavimo funkcija
def get_data_simple():
    try:
        exchange = ccxt.binance()
        # Bandome gauti tik vieną skaičių testui
        ticker = exchange.fetch_ticker('ETH/EUR')
        price = ticker['last']
        
        # Gauname žvakes
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Skaičiuojame tik tai, kas būtina
        df['rsi'] = ta.rsi(df['close'], length=6)
        return df, price
    except Exception as e:
        st.error(f"❌ Nepavyko prisijungti prie Binance: {e}")
        return None, None

df, current_price = get_data_simple()

if df is not None:
    st.header(f"ETH Kaina: {current_price} EUR")
    
    rsi_val = df['rsi'].iloc[-1]
    if rsi_val < 70:
        st.success(f"Signalas: PIRKTI (RSI: {rsi_val:.2f})")
    else:
        st.warning(f"Signalas: LAUKTI (RSI: {rsi_val:.2f})")

    # Paprastas grafikas
    fig = go.Figure(data=[go.Candlestick(x=df['time'],
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'])])
    fig.update_layout(template="plotly_dark", title="ETH/EUR 15m")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Duomenys nerodomi. Patikrinkite pranešimą viršuje.")
