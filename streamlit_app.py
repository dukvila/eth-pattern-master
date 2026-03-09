import ccxt
import pandas as pd
import pandas_ta as ta
import time

# 1. Prisijungiame prie Binance (tik duomenų skaitymui)
exchange = ccxt.binance()

def gauti_duomenis_ir_rsi(symbol='ETH/EUR', timeframe='15m'):
    print(f"\n--- Tikrinama kaina: {symbol} ({timeframe}) ---")
    
    # Gauname paskutines 100 žvakių
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Apskaičiuojame RSI (naudojame 6 periodus, kaip tavo nuotraukoje)
    df['RSI'] = ta.rsi(df['close'], length=6)
    
    paskutinis_rsi = df['RSI'].iloc[-1]
    dabartine_kaina = df['close'].iloc[-1]
    
    return dabartine_kaina, paskutinis_rsi

# Pagrindinis ciklas
while True:
    try:
        kaina, rsi = gauti_duomenis_ir_rsi()
        
        print(f"Kaina: {kaina} EUR | RSI: {rsi:.2f}")
        
        # Tavo logika: pirkti, jei RSI dar nepasiekė 70
        if rsi < 70:
            likutis = 70 - rsi
            print(f"✅ SIGNALAS: Saugi zona pirkimui. Iki perpirkimo ribos dar {likutis:.2f} punkto.")
        elif rsi >= 70 and rsi < 80:
            print("⚠️ ĮSPĖJIMAS: RSI virš 70. Rinka pradeda kaisti, būkite atsargūs.")
        else:
            print("❌ STOK: RSI virš 80! Labai didelė tikimybė, kad kaina tuoj kris.")
            
    except Exception as e:
        print(f"Klaida: {e}")

    # Laukiame 30 sekundžių prieš kitą patikrinimą
    print("Laukiama kito atnaujinimo...")
    time.sleep(30)
