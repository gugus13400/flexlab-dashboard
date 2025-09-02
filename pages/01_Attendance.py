# pages/01_Attendance.py
import streamlit as st
from utils import load_attendance_fixed, heatmap_attendance, top_slots, ATT_PATH

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

st.subheader("Heatmap présences — Jour × Heure")
fig_hm = heatmap_attendance(att, metric="Nombre total de sessions")
st.pyplot(fig_hm, use_container_width=True)

st.subheader("Top 5 créneaux — Nombre de sessions")
fig_top = top_slots(att, metric="Nombre total de sessions", topn=5)
st.pyplot(fig_top, use_container_width=True)

st.caption("💡 Identifiez les heures à forte demande (staffing) et les heures à stimuler (offres, partenariats).")
