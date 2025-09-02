# app.py
import streamlit as st
import pandas as pd
from utils import load_sales_fixed, stacked_bar_with_cumulative, simple_line, pie_split, SALES_PATH

st.set_page_config(page_title="FlexLab — Sales", layout="wide")

st.markdown("""
<h1 style='margin-bottom:0'>FlexLab — Sales</h1>
<p style='color:#9bb7ff;margin-top:2px'>Assisted Stretching for Europe — <b>Not an AI startup</b></p>
""", unsafe_allow_html=True)

colA, colB = st.columns([3,1])
with colA:
    st.info(f"📄 Fichier ventes chargé automatiquement : <code>{SALES_PATH}</code>", icon="ℹ️")
with colB:
    if st.button("🔁 Rafraîchir les données"):
        st.cache_data.clear()

@st.cache_data(show_spinner=False)
def _load_sales():
    return load_sales_fixed()

try:
    df = _load_sales()
except Exception as e:
    st.error(f"Erreur chargement ventes : {e}")
    st.stop()

# Filtres période
c1, c2 = st.columns(2)
date_min = c1.date_input("Date de début", value=None)
date_max = c2.date_input("Date de fin", value=None)
if date_min:
    df = df[df["Date"] >= pd.to_datetime(date_min)]
if date_max:
    df = df[df["Date"] <= pd.to_datetime(date_max)]

# KPIs
total_rev = float(df["Montant total"].sum())
total_qty = int(df["Quantité"].sum())
by_group = df.groupby("Groupe").agg(rev=("Montant total","sum"), qty=("Quantité","sum"))

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("CA total (€)", f"{total_rev:,.0f}".replace(",", " "))
k2.metric("Séances totales", f"{total_qty:,}".replace(",", " "))
k3.metric("Découverte (qty)", int(by_group.get("qty").get("Découverte", 0)))
k4.metric("Packs (qty)", int(by_group.get("qty").get("Packs", 0)))
k5.metric("Abonnement 4×50’ (qty)", int(by_group.get("qty").get("Abonnement 4×50’", 0)))

# Journalière empilée + CA cumulatif
daily = df.groupby([pd.Grouper(key="Date", freq="D"), "Groupe"]).agg(
    quantite=("Quantité","sum"),
    ventes=("Montant total","sum")
).reset_index()
daily_pivot = daily.pivot(index="Date", columns="Groupe", values="quantite").fillna(0)
rev = df.groupby(pd.Grouper(key="Date", freq="D"))["Montant total"].sum().reset_index()
rev["cumul"] = rev["Montant total"].cumsum()

st.subheader("Ventes quotidiennes par service (stacked) + CA cumulatif")
fig1 = stacked_bar_with_cumulative(daily_pivot, rev, "Quantités quotidiennes + CA cumulatif")
st.pyplot(fig1, use_container_width=True)

# Hebdo
weekly = df.groupby([pd.Grouper(key="Date", freq="W-MON"), "Groupe"]).agg(
    ventes=("Montant total","sum")
).reset_index()
weekly_pivot = weekly.pivot(index="Date", columns="Groupe", values="ventes").fillna(0)

st.subheader("Ventes hebdomadaires par type (tendance)")
fig2 = simple_line(weekly_pivot, "Ventes hebdomadaires par type", "Ventes (€)")
st.pyplot(fig2, use_container_width=True)

# Pie
st.subheader("Répartition du CA par type de service")
fig3 = pie_split(df.groupby("Groupe")["Montant total"].sum(), "Répartition du CA")
st.pyplot(fig3)
