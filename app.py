
import streamlit as st
import pandas as pd
import numpy as np
from utils import load_sales, load_attendance, stacked_bar_with_cumulative, simple_line, pie_split, PRIMARY

st.set_page_config(page_title="FlexLab Dashboard", layout="wide")

st.markdown(f"""
<h1 style='margin-bottom:0'>FlexLab Dashboard</h1>
<p style='color:#9bb7ff;margin-top:2px'>Assisted Stretching for Europe — <b>Not an AI startup</b></p>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Paramètres")
    sales_file = st.file_uploader("Ventes — Excel (Sales by Service)", type=["xlsx"])
    date_min = st.date_input("Date de début", value=None)
    date_max = st.date_input("Date de fin", value=None)
    st.caption("Astuce : Laisse vide pour tout l'historique.")

if sales_file is None:
    st.info("Uploade le fichier **Sales by Service** (Excel) pour démarrer.")
    st.stop()

# Load & filter
df = load_sales(sales_file).copy()
if date_min:
    df = df[df["Date"] >= pd.to_datetime(date_min)]
if date_max:
    df = df[df["Date"] <= pd.to_datetime(date_max)]

# KPIs
total_rev = float(df["Montant total"].sum())
total_qty = int(df["Quantité"].sum())
by_group = df.groupby("Groupe").agg(rev=("Montant total","sum"), qty=("Quantité","sum"))
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("CA total (€)", f"{total_rev:,.0f}".replace(",", " "), help="Chiffre d'affaires total sur la période filtrée")
col2.metric("Séances totales", f"{total_qty:,}".replace(",", " "))
col3.metric("Découverte (qty)", int(by_group.get("qty").get("Découverte", 0)))
col4.metric("Packs (qty)", int(by_group.get("qty").get("Packs", 0)))
col5.metric("Abonnements 4×50’ (qty)", int(by_group.get("qty").get("Abonnement 4×50’", 0)))

# Daily stacked quantities + cumulative revenue
daily = df.groupby([pd.Grouper(key="Date", freq="D"), "Groupe"]).agg(
    quantite=("Quantité","sum"),
    ventes=("Montant total","sum")
).reset_index()

daily_pivot = daily.pivot(index="Date", columns="Groupe", values="quantite").fillna(0)
rev = df.groupby(pd.Grouper(key="Date", freq="D"))["Montant total"].sum().reset_index()
rev["cumul"] = rev["Montant total"].cumsum()

st.plotly_chart if False else None  # placeholder (we stick to matplotlib)

st.subheader("Ventes quotidiennes par service (stacked) + CA cumulatif")
fig1 = stacked_bar_with_cumulative(daily_pivot, rev, "Quantités quotidiennes par service + CA cumulatif")
st.pyplot(fig1, use_container_width=True)

# Weekly revenue by type
weekly = df.groupby([pd.Grouper(key="Date", freq="W-MON"), "Groupe"]).agg(
    ventes=("Montant total","sum")
).reset_index()
weekly_pivot = weekly.pivot(index="Date", columns="Groupe", values="ventes").fillna(0)

st.subheader("Ventes hebdomadaires par type (tendance)")
fig2 = simple_line(weekly_pivot, "Ventes hebdomadaires par type", "Ventes (€)")
st.pyplot(fig2, use_container_width=True)

# Pie split
st.subheader("Répartition du CA par type de service")
fig3 = pie_split(df.groupby("Groupe")["Montant total"].sum(), "Répartition du CA par type")
st.pyplot(fig3, use_container_width=False)

st.caption("Conseil investisseur : suivez la conversion Découverte → Packs/Abonnements pour maximiser la LTV et stabiliser le MRR.")
