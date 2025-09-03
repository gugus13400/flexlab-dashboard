# app.py
import streamlit as st
import pandas as pd
from utils import (
    SALES_PATH, load_sales_fixed, styled_title, inject_background,
    kpi_row, stacked_bar_with_cumulative, simple_line_growth,
    weekly_packs_vs_clients, arpu_line, share_area, pie_split,
    warn_if_missing_cols
)

st.set_page_config(page_title="FlexLab Dashboard", layout="wide")

# Branding (background + logo if present)
inject_background()         # uses assets/bg.jpg if available
styled_title(logo_path="assets/logo.png", title="FlexLab Dashboard",
             subtitle="Ventes, croissance et traction client — <b>Not an AI startup</b>")

# Info + refresh
colA, colB = st.columns([3,1])
with colA:
    st.info(f"📄 Fichier ventes chargé automatiquement : <code>{SALES_PATH}</code>", icon="ℹ️")
with colB:
    if st.button("🔁 Rafraîchir les données"):
        st.cache_data.clear()

@st.cache_data(show_spinner=False)
def _load_sales():
    return load_sales_fixed()

# Load data
try:
    df = _load_sales()
except Exception as e:
    st.error(f"Erreur chargement ventes : {e}")
    st.stop()

# Date filters
c1, c2 = st.columns(2)
date_min = c1.date_input("Date de début", value=None)
date_max = c2.date_input("Date de fin", value=None)
if date_min:
    df = df[df["Date"] >= pd.to_datetime(date_min)]
if date_max:
    df = df[df["Date"] <= pd.to_datetime(date_max)]

# ---------- KPI CARDS ----------
kpis = kpi_row(df)  # returns dict
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("CA total (€)", kpis["ca_total_fmt"])
c2.metric("Séances totales", kpis["qty_total_fmt"])
c3.metric("Clients uniques (approx.)", kpis["clients_uniques_fmt"], help=kpis["clients_help"])
c4.metric("Packs vendus (sem. courante)", kpis["packs_week_fmt"])
c5.metric("Taux Découverte → Pack", kpis["conv_discovery_to_pack_fmt"], help=kpis["conv_help"])
c6.metric("ARPU (€ / client)", kpis["arpu_fmt"])

# ---------- CHARTS (Sales) ----------
st.subheader("Ventes quotidiennes par service (stacked) + CA cumulatif")
fig1 = stacked_bar_with_cumulative(df, title="Quantités quotidiennes + CA cumulatif (été grisé)")
st.pyplot(fig1, use_container_width=True)

st.subheader("CA hebdomadaire (variation semaine / semaine)")
fig2 = simple_line_growth(df, title="CA hebdomadaire et croissance (%)")
st.pyplot(fig2, use_container_width=True)

st.subheader("Packs vendus vs Clients uniques (hebdomadaire)")
fig3 = weekly_packs_vs_clients(df, title="Packs vs Clients uniques — et % conversion hebdo")
st.pyplot(fig3, use_container_width=True)

st.subheader("ARPU (CA / client) — hebdomadaire & cumul")
fig4 = arpu_line(df, title="ARPU hebdomadaire (et ligne de tendance)")
st.pyplot(fig4, use_container_width=True)

colA, colB = st.columns([2,1])
with colA:
    st.subheader("Part des revenus par type (aire empilée)")
    fig5 = share_area(df, title="Répartition du CA dans le temps")
    st.pyplot(fig5, use_container_width=True)
with colB:
    st.subheader("Répartition cumulée du CA")
    fig6 = pie_split(df.groupby("Groupe")["Montant total"].sum(), "CA total par type")
    st.pyplot(fig6, use_container_width=True)

# Warn if missing columns for deeper metrics
warn_if_missing_cols(df)
