
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="FlexLab Sales & Attendance", layout="wide")

st.title("FlexLab — Ventes & Présences")

# --- Uploaders ---
sales_file = st.file_uploader("Uploader le fichier Ventes (Sales by Service Report ... .xlsx)", type=["xlsx"])
att_file = st.file_uploader("Uploader le fichier Présences (Attendance Analysis ... .xlsx)", type=["xlsx"])

@st.cache_data
def load_sales(file):
    df = pd.read_excel(file, sheet_name=None)
    # try to find the right sheet
    sheet = None
    for k in df.keys():
        if "service" in k.lower() or "vente" in k.lower():
            sheet = k
            break
    if sheet is None:
        sheet = list(df.keys())[0]
    data = df[sheet].copy()
    # Normalize columns
    if "Date d'achat" in data.columns:
        data["Date"] = pd.to_datetime(data["Date d'achat"], errors="coerce")
    elif "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    else:
        data["Date"] = pd.NaT
    data["Nom"] = data["Nom"].astype(str)
    # Group types
    def group_service(n):
        x = str(n).lower()
        if "découverte" in x:
            return "Découverte (nouveaux clients)"
        if "pack" in x or "recharge" in x:
            return "Packs (fidélisation)"
        if "4 x 50" in x:
            return "Abonnement (4 x 50’)"
        return "Séances unitaires"
    data["Groupe"] = data["Nom"].apply(group_service)
    return data

@st.cache_data
def load_attendance(file):
    df = pd.read_excel(file, sheet_name=None)
    # find attendance-like sheet
    sheet = None
    for k in df.keys():
        if "présence" in k.lower() or "attendance" in k.lower():
            sheet = k
            break
    if sheet is None:
        sheet = list(df.keys())[0]
    data = df[sheet].copy()
    # try to normalize time column
    time_col = None
    for c in data.columns:
        if "Heure" in c or "Time" in c:
            time_col = c
            break
    if time_col:
        data["Heure"] = pd.to_datetime(data[time_col], errors="coerce")
        data["heure_label"] = data["Heure"].dt.strftime("%H:%M")
    return data

if sales_file:
    sales = load_sales(sales_file)
    st.subheader("KPIs par type de service")
    kpi = sales.groupby("Groupe").agg(
        ventes_totales=("Montant total","sum"),
        nb_total=("Quantité","sum")
    ).reset_index()
    st.dataframe(kpi)

    # Daily stacked bars with cumulative revenue
    daily = sales.groupby([pd.Grouper(key="Date", freq="D"), "Groupe"]).agg(
        quantite=("Quantité","sum"),
        ventes=("Montant total","sum")
    ).reset_index()
    daily_pivot = daily.pivot(index="Date", columns="Groupe", values="quantite").fillna(0)
    st.subheader("Quantités quotidiennes par service (stacked) + CA cumulatif")
    fig, ax1 = plt.subplots(figsize=(12,5))
    bottom = None
    for col in daily_pivot.columns:
        vals = daily_pivot[col].values
        ax1.bar(daily_pivot.index, vals, bottom=bottom, label=col)
        bottom = vals if bottom is None else bottom + vals
    ax1.set_ylabel("Quantité / jour")
    ax1.legend(loc="upper left")
    # cumulative revenue
    rev = sales.groupby(pd.Grouper(key="Date", freq="D"))["Montant total"].sum().reset_index()
    rev["cumul"] = rev["Montant total"].cumsum()
    ax2 = ax1.twinx()
    ax2.plot(rev["Date"], rev["cumul"], linewidth=2, marker="o")
    ax2.set_ylabel("CA cumulatif (€)")
    st.pyplot(fig)

    # Weekly revenue by type
    weekly = sales.groupby([pd.Grouper(key="Date", freq="W-MON"), "Groupe"]).agg(
        ventes=("Montant total","sum")
    ).reset_index()
    weekly_pivot = weekly.pivot(index="Date", columns="Groupe", values="ventes").fillna(0)
    st.subheader("Ventes hebdomadaires par type de service")
    fig2, ax = plt.subplots(figsize=(12,5))
    for col in weekly_pivot.columns:
        ax.plot(weekly_pivot.index, weekly_pivot[col], marker="o", label=col)
    ax.set_ylabel("Ventes (€)")
    ax.legend()
    st.pyplot(fig2)

    # Pie chart revenue split
    st.subheader("Répartition du CA par type de service")
    ca_split = sales.groupby("Groupe")["Montant total"].sum()
    fig3, ax = plt.subplots(figsize=(5,5))
    ax.pie(ca_split.values, labels=ca_split.index, autopct="%1.1f%%")
    st.pyplot(fig3)

    # Simple churn approximation (needs client column)
    churn_rate = None
    if "Client" in sales.columns:
        grp = sales.groupby("Client")["Groupe"].apply(list)
        churned = grp.apply(lambda lst: ("Découverte (nouveaux clients)" in lst) and (all(("Pack" not in s and "Abonnement" not in s) for s in lst)))
        churn_rate = (churned.sum()/len(grp)) if len(grp)>0 else None
    st.markdown(f"**Churn (approx.)**: {churn_rate:.0%}" if churn_rate is not None else "_Churn non calculable (pas de colonne client)._")

if att_file:
    att = load_attendance(att_file)
    st.subheader("Présences par créneau horaire")
    if "Nombre total de sessions" in att.columns and "heure_label" in att.columns:
        fig4, ax = plt.subplots(figsize=(12,5))
        bars = ax.bar(att["heure_label"], att["Nombre total de sessions"])
        for b in bars:
            h = b.get_height()
            if h>0:
                ax.text(b.get_x()+b.get_width()/2, h+0.1, f"{int(h)}", ha="center", va="bottom", fontsize=8)
        ax.set_ylabel("Nombre de sessions")
        plt.xticks(rotation=45)
        st.pyplot(fig4)
    else:
        st.write("Colonnes nécessaires non trouvées dans le fichier de présence.")
