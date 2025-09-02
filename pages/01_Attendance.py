# pages/01_Attendance.py
import streamlit as st
from utils import load_attendance_fixed, bar_by_hour, ATT_PATH

st.set_page_config(page_title="FlexLab — Attendance", layout="wide")

st.markdown("""
<h1 style='margin-bottom:0'>Présences & Créneaux</h1>
<p style='color:#9bb7ff;margin-top:2px'>Optimisez vos slots et votre staffing</p>
""", unsafe_allow_html=True)

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

st.subheader("Sessions par créneau horaire")
fig_a = bar_by_hour(att, "Nombre total de sessions", "Sessions par créneau", "Nombre de sessions")
st.pyplot(fig_a, use_container_width=True)

st.subheader("Clients uniques par créneau horaire")
fig_b = bar_by_hour(att, "Clients uniques", "Clients uniques par créneau", "Clients uniques")
st.pyplot(fig_b, use_container_width=True)

st.caption("💡 Utilisez ces graphes pour renforcer les créneaux forts et remplir les créneaux faibles (offres, contenus, B2B).")
