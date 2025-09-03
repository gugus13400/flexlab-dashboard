# pages/02_Growth.py
import streamlit as st
from utils import (
    SALES_PATH, load_sales_fixed, styled_title, inject_background,
    funnel_conversion, churn_block, cohort_note
)

st.set_page_config(page_title="FlexLab — Growth & Retention", layout="wide")
inject_background()
styled_title(logo_path="assets/logo.png", title="Growth & Retention",
             subtitle="Conversion, churn, rétention")

st.info(f"📄 Fichier ventes : <code>{SALES_PATH}</code>", icon="ℹ️")

@st.cache_data(show_spinner=False)
def _load_sales():
    return load_sales_fixed()

try:
    df = _load_sales()
except Exception as e:
    st.error(f"Erreur chargement ventes : {e}")
    st.stop()

st.subheader("Funnel — Découverte → Pack → Abonnement")
fig_f, notes = funnel_conversion(df)
st.pyplot(fig_f, use_container_width=False)
st.caption(notes)

st.subheader("Churn & rétention (approx.)")
st.markdown(churn_block(df), unsafe_allow_html=True)

st.subheader("Cohortes (note)")
st.info(cohort_note(), icon="ℹ️")
