import streamlit as st
import random
import time

# Žaidimo konfigūracija
st.set_page_config(page_title="Titan Cyber Tennis", layout="centered")

# Sesijos kintamieji
if 'ball_x' not in st.session_state:
    st.session_state.ball_x, st.session_state.ball_y = 50, 50
    st.session_state.ball_dx, st.session_state.ball_dy = 2, 2
    st.session_state.p1_y, st.session_state.p2_y = 40, 40
    st.session_state.score = [0, 0]
    st.session_state.game_over = False

def reset_ball():
    st.session_state.ball_x, st.session_state.ball_y = 50, 50
    st.session_state.ball_dx *= -1

# --- ŽAIDIMO VARIKLIS ---
def update_game():
    if st.session_state.game_over: return

    # Kamuoliuko judėjimas
    st.session_state.ball_x += st.session_state.ball_dx
    st.session_state.ball_y += st.session_state.ball_dy

    # Atšokimas nuo sienų (viršus/apačia)
    if st.session_state.ball_y <= 0 or st.session_state.ball_y >= 95:
        st.session_state.ball_dy *= -1

    # Kompiuterio (P2) judėjimas - bando sekti kamuoliuką
    if st.session_state.p2_y + 10 < st.session_state.ball_y:
        st.session_state.p2_y += 2
    elif st.session_state.p2_y > st.session_state.ball_y:
        st.session_state.p2_y -= 2

    # Atšokimas nuo raketų
    # Žaidėjas (P1)
    if st.session_state.ball_x <= 5:
        if st.session_state.p1_y <= st.session_state.ball_y <= st.session_state.p1_y + 25:
            st.session_state.ball_dx = abs(st.session_state.ball_dx) + 0.5 # Didinam greitį
        else:
            st.session_state.score[1] += 1
            reset_ball()

    # Kompiuteris (P2)
    if st.session_state.ball_x >= 95:
        if st.session_state.p2_y <= st.session_state.ball_y <= st.session_state.p2_y + 25:
            st.session_state.ball_dx = -abs(st.session_state.ball_dx) - 0.5
        else:
            st.session_state.score[0] += 1
            reset_ball()

# --- VIZUALIZACIJA ---
st.title("🎾 Titan Cyber Tennis")
st.write(f"### Rezultatas: Tu {st.session_state.score[0]} - {st.session_state.score[1]} Robotas")

# Sukuriame žaidimo lauką naudojant HTML/CSS
game_field = f"""
<div style="position: relative; width: 100%; height: 300px; background-color: #0E1117; border: 2px solid #00f2ff; border-radius: 10px; overflow: hidden;">
    <div style="position: absolute; left: 5px; top: {st.session_state.p1_y}%; width: 10px; height: 60px; background-color: #00f2ff; border-radius: 5px;"></div>
    <div style="position: absolute; right: 5px; top: {st.session_state.p2_y}%; width: 10px; height: 60px; background-color: #ff0055; border-radius: 5px;"></div>
    <div style="position: absolute; left: {st.session_state.ball_x}%; top: {st.session_state.ball_y}%; width: 15px; height: 15px; background-color: white; border-radius: 50%; box-shadow: 0 0 10px white;"></div>
    <div style="position: absolute; left: 50%; width: 2px; height: 100%; border-left: 2px dashed #2D323E;"></div>
</div>
"""
st.markdown(game_field, unsafe_allow_html=True)

# Valdymas
st.write("")
c1, c2, c3 = st.columns([1,1,1])
with c1:
    if st.button("⬆️ AUKŠTYN", use_container_width=True):
        st.session_state.p1_y = max(0, st.session_state.p1_y - 15)
with c2:
    if st.button("⬇️ ŽEMYN", use_container_width=True):
        st.session_state.p1_y = min(80, st.session_state.p1_y + 15)
with c3:
    if st.button("🔄 RESTART", use_container_width=True):
        st.session_state.score = [0, 0]
        reset_ball()
        st.rerun()

# Automatinis ciklas
update_game()
time.sleep(0.05)
st.rerun()
