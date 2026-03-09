import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
import time

# 1. Konfigūracija
st.set_page_config(page_title="ETH Pro Robot", layout="wide")

# Funkcija, kuri saugiai gauna duomenis ir automatiškai taiso logines klaidas
def fetch_safe_data():
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv('ETH/EUR', timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Automatinis indikatorių skaičiavimas su apsauga nuo tuščių duomenų
        df['rsi'] = ta.rsi(df['close'], length=6)
        df['sma20'] = ta.sma(df['close'], length=20)
        df['ema9'] = ta.ema(df['close'], length=9)
        
        return df.dropna() # Išmetame nepilnas eilutes, kad nekiltų braižymo klaidų
    except Exception as e:
        st.sidebar.error(f"Ryšio klaida: {e}. Bandau jungtis iš naujo...")
        return None

# Pagrindinė programos logika
def main():
    st.title("🚀 ETH/EUR Automatinė Analizė")
    
    # Sukuriame vietą, kuri bus nuolat atnaujinama be puslapio perkrovimo
    placeholder = st.empty()

    while True:
        df = fetch_safe_data()
        
        if df is not None:
            with placeholder.container():
                last_price = df['close'].iloc[-1]
                last_rsi = df['rsi'].iloc[-1]
                
                # Vizualūs indikatoriai
                m1, m2, m3 = st.columns(3)
                m1.metric("Kaina", f"{last_price} EUR")
                m2.metric("RSI (6)", f"{last_rsi:.2f}")
                
                if last_rsi < 70:
                    m3.success("✅ PIRKIMO SIGNALAS")
                else:
                    m3.warning("⚠️ PALAUŽKITE (PERPIRKTA)")

                # Grafikas naudojant Plotly (atspariausias klaidoms)
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Kaina'))
                fig.add_trace(go.Scatter(x=df['time'], y=df['sma20'], line=dict(color='yellow', width=2), name='SMA 20'))
                fig.add_trace(go.Scatter(x=df['time'], y=df['ema9'], line=dict(color='cyan', width=2), name='EMA 9'))
                
                fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                st.caption(f"Paskutinis sėkmingas atnaujinimas: {datetime.now().strftime('%H:%M:%S')}")

        # Programa "miega" 10 sekundžių ir pati save atnaujina be tavo įsikišimo
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()
