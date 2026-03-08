import streamlit as st
import pandas as pd
import numpy as np
import time
import random

st.set_page_config(page_title="AMD SNIPER GAME", layout="centered")

# --- ŽAIDIMO LOGIKA ---
if 'score' not in st.session_state: st.session_state.score = 0
if 'high_score' not in st.session_state: st.session_state.high_score = 0
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'chart_data' not in st.session_state: st.session_state.chart_data = [1700.0]

def start_game():
    st.session_state.game_active = True
    st.session_state.chart_data = [1700.0]
    st.session_state.current_step = 0

st.title("🎯 AMD Sniper Simulator")
st.write("Tavo tikslas: Paspausti **PIRKTI**, kai kaina pasiekia manipuliacijos dugną!")

if not st.session_state.game_active:
    if st.button("PRADĖTI MEDŽIOKLĘ", use_container_width=True):
        start_game()
        st.rerun()
else:
    # Generuojame "krentantį" grafiką (Accumulation/Manipulation)
    last_val = st.session_state.chart_data[-1]
    new_val = last_val - random.uniform(2, 8) if len(st.session_state.chart_data) < 15 else last_val + random.uniform(10, 30)
    st.session_state.chart_data.append(new_val)
    
    # Rodome grafiką
    df = pd.DataFrame(st.session_state.chart_data, columns=["Kaina"])
    st.line_chart(df, height=300)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🛒 PIRKTI DABAR!", use_container_width=True):
            # Tikriname ar pataikė į dugną
            lowest_point = min(st.session_state.chart_data)
            pirkimo_kaina = st.session_state.chart_data[-1]
            
            if abs(pirkimo_kaina - lowest_point) < 5:
                st.success(f"🔥 IDEALU! Pagavai dugną ties {round(pirkimo_kaina, 2)}€!")
                st.session_state.score += 100
            else:
                st.error(f"Pramiegojai... Pirkai už {round(pirkimo_kaina, 2)}€, o dugnas buvo {round(lowest_point, 2)}€.")
                st.session_state.score -= 50
            
            st.session_state.game_active = False
            time.sleep(2)
            st.rerun()

    with col2:
        st.metric("Taškai", st.session_state.score)

    # Automatinis atnaujinimas imitacijai
    if len(st.session_state.chart_data) < 20:
        time.sleep(0.3)
        st.rerun()
    else:
        st.warning("Rinka nuvažiavo be tavęs...")
        st.session_state.game_active = False
        time.sleep(2)
        st.rerun()

st.divider()
st.info("Šis žaidimas moko kantrybės – nepirk, kol kaina tiesiog 'krenta', lauk kol ji 'lūžta' (Liquidity Sweep).")
