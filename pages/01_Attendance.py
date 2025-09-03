# pages/01_Attendance.py
import streamlit as st
from utils import (
    ATT_PATH, load_attendance_fixed, styled_title, inject_background,
    heatmap_attendance, top_slots, weekly_unique_clients, occupancy_gauge
)

st.set_page_config(page_title="FlexLab — Attendance", layout="wide")
inject_background()
styled_title(logo_path="assets/logo.png", title="Présences & Créneaux",
             subtitle="Optimisez vos slots et votre staffing")

colA, colB = st.columns([3,1])
with colA:
    st.info(f"📄 Fichier présence chargé automatiquement : <code>{ATT_PATH}</code>", icon="ℹ️")
with colB:
    if st.button("🔁 Rafraîchir les données"):
        st.cache_data.clear()

@st.cache_data(show_spinner=False)
def _load_att():
    return load_attendance_fixed()

try:
    att = _load_att()
except Exception as e:
    st.error(f"Erreur chargement présence : {e}")
    st.stop()

# Sidebar controls for capacity (optional)
with st.sidebar:
    st.header("⚙️ Paramètres attendance")
    capacity = st.number_input("Capacité théorique/jour (sessions max)", min_value=0, value=0,
                               help="Si >0, un indicateur d'occupation sera affiché.")

st.subheader("Heatmap — Jour × Heure (nombre de sessions)")
fig_hm = heatmap_attendance(att, metric="Nombre total de sessions")
st.pyplot(fig_hm, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top 5 créneaux — Sessions")
    fig_top = top_slots(att, metric="Nombre total de sessions", topn=5)
    st.pyplot(fig_top, use_container_width=True)

with col2:
    st.subheader("Clients uniques / semaine (bar)")
    from utils import weekly_unique_clients_bar
    fig_wc = weekly_unique_clients_bar(att, title="Clients uniques par semaine (bar)")
    st.pyplot(fig_wc, use_container_width=True)


# Optional occupancy indicator
if capacity and capacity > 0:
    st.subheader("Taux d’occupation (approx.)")
    fig_occ = occupancy_gauge(att, capacity=capacity)
    st.pyplot(fig_occ, use_container_width=False)
