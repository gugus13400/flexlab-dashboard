
import streamlit as st
import pandas as pd
from utils import load_attendance, bar_by_hour

st.set_page_config(page_title="FlexLab Attendance", layout="wide")

st.markdown(f"""
<h1 style='margin-bottom:0'>Présences & Créneaux</h1>
<p style='color:#9bb7ff;margin-top:2px'>Optimisez vos slots et staffing</p>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Paramètres")
    att_file = st.file_uploader("Présences — Excel (Attendance Analysis)", type=["xlsx"])

if att_file is None:
    st.info("Uploade le fichier **Attendance Analysis** (Excel) pour voir les présences par créneau.")
    st.stop()

att = load_attendance(att_file)

st.subheader("Sessions par créneau horaire")
fig_a = bar_by_hour(att, "Nombre total de sessions", "Sessions par créneau", "Nombre de sessions")
st.pyplot(fig_a, use_container_width=True)

st.subheader("Clients uniques par créneau horaire")
fig_b = bar_by_hour(att, "Clients uniques", "Clients uniques par créneau", "Clients uniques")
st.pyplot(fig_b, use_container_width=True)

st.caption("Astuce : utilisez ces graphiques pour renforcer les créneaux forts et proposer des offres sur les créneaux faibles.")
