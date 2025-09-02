# utils.py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplcyberpunk  # pip install mplcyberpunk
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime

PRIMARY = "#0f6fff"
BG_DARK = "#0b1224"

# --------------------
# FIXED FILE PATHS
# --------------------
SALES_PATH = os.path.join("data", "sales.xlsx")
ATT_PATH   = os.path.join("data", "attendance.xlsx")

# --------------------
# HELPERS
# --------------------
def _ensure_renamed(df, candidates, target, must_exist=True):
    """Rename first matching candidate column to target name."""
    if target in df.columns:
        return
    for c in candidates:
        if c in df.columns:
            df.rename(columns={c: target}, inplace=True)
            return
    if must_exist:
        raise KeyError(f"Required column missing: {target} (accepted: {candidates})")

def _brand_cmap():
    # gradient from very light to brand blue
    return LinearSegmentedColormap.from_list("flexlab_cmap",
        [(0.85, 0.92, 1.0, 1.0), _hex_to_rgba(PRIMARY, 1.0)], N=256)

def _hex_to_rgba(h, alpha=1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16)/255.0 for i in (0,2,4)) + (alpha,)

def _apply_style():
    plt.style.use("cyberpunk")

def shade_closed_period(ax, start="2025-08-02", end="2025-08-24", label="Studio fermé (été)"):
    try:
        s = pd.to_datetime(start); e = pd.to_datetime(end)
        ax.axvspan(s, e, color="grey", alpha=0.25, label=label)
    except Exception:
        pass

# --------------------
# LOADERS
# --------------------
def load_sales_fixed():
    """Load data/sales.xlsx and normalize for Mindbody 'Sales by Service'."""
    if not os.path.exists(SALES_PATH):
        raise FileNotFoundError("Missing file: data/sales.xlsx")
    xls = pd.read_excel(SALES_PATH, sheet_name=None)
    # pick plausible sheet
    sheet = None
    for k in xls.keys():
        lk = k.lower()
        if "service" in lk or "vente" in lk:
            sheet = k; break
    if sheet is None:
        sheet = list(xls.keys())[0]
    df = xls[sheet].copy()

    # normalize columns
    _ensure_renamed(df, ["Date d'achat","Date de vente","Date","Sale Date","Date commande"], "Date")
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    _ensure_renamed(df, ["Nom","Service","Service Name","Nom du service"], "Nom")
    _ensure_renamed(df, ["Quantité","Qty","Quantity","Nombre"], "Quantité")
    _ensure_renamed(df, ["Montant total","Montant","Total","Amount","CA"], "Montant total")

    df["Nom"] = df["Nom"].astype(str)

    def group_service(n):
        x = str(n).lower()
        if "découverte" in x:
            return "Découverte"
        if "pack" in x or "recharge" in x:
            return "Packs"
        if "4 x 50" in x or "4x50" in x:
            return "Abonnement 4×50’"
        # everything else in one bucket to stay readable
        return "Unitaire (autres)"

    df["Groupe"] = df["Nom"].apply(group_service)
    return df

def load_attendance_fixed():
    """Load data/attendance.xlsx and normalize for time-slot analysis."""
    if not os.path.exists(ATT_PATH):
        raise FileNotFoundError("Missing file: data/attendance.xlsx")
    xls = pd.read_excel(ATT_PATH, sheet_name=None)
    # pick plausible sheet
    sheet = None
    for k in xls.keys():
        lk = k.lower()
        if "présence" in lk or "presence" in lk or "attendance" in lk:
            sheet = k; break
    if sheet is None:
        sheet = list(xls.keys())[0]
    df = xls[sheet].copy()

    # date column (optional but useful)
    _ensure_renamed(df, ["Date du service","Date","Service Date","Date de séance"], "Date", must_exist=False)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Jour"] = df["Date"].dt.day_name()
        # French ordering
        mapping = {
            "Monday":"Lundi","Tuesday":"Mardi","Wednesday":"Mercredi","Thursday":"Jeudi",
            "Friday":"Vendredi","Saturday":"Samedi","Sunday":"Dimanche"
        }
        df["JourFR"] = df["Jour"].map(mapping)
        df["JourFR"] = pd.Categorical(df["JourFR"],
                        categories=["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"],
                        ordered=True)

    # hour / slot
    _ensure_renamed(df, ["Heure du service","Heure","Time","Créneau","Slot","Start Time"], "Heure du service", must_exist=False)
    if "Heure du service" in df.columns:
        df["HeureDT"] = pd.to_datetime(df["Heure du service"], errors="coerce")
        df["HeureHM"] = df["HeureDT"].dt.strftime("%H:%M")
        if df["HeureHM"].isna().all():
            df["HeureHM"] = df["Heure du service"].astype(str)
    else:
        df["HeureHM"] = ""

    # metrics
    _ensure_renamed(df, ["Nombre total de sessions","Total Sessions","Sessions","Nombre de sessions","Total des sessions"],
                    "Nombre total de sessions", must_exist=False)
    _ensure_renamed(df, ["Clients uniques","Unique Clients","Clients","Unique"], "Clients uniques", must_exist=False)

    return df

# --------------------
# PLOTS
# --------------------
def stacked_bar_with_cumulative(daily_pivot, rev_df, title, shade_august=True):
    _apply_style()
    fig, ax1 = plt.subplots(figsize=(12,5))

    bottom = np.zeros(len(daily_pivot.index))
    palette = {
        "Découverte": "#6aa6ff",
        "Packs": PRIMARY,
        "Abonnement 4×50’": "#0b4bcc",
        "Unitaire (autres)": "#99bbff",
    }
    for lab in daily_pivot.columns:
        vals = daily_pivot[lab].values
        bars = ax1.bar(daily_pivot.index, vals, bottom=bottom, label=lab, color=palette.get(lab, "#6aa6ff"))
        bottom += vals
        for b, v in zip(bars, vals):
            if v >= 1:
                ax1.text(b.get_x()+b.get_width()/2, b.get_y()+b.get_height()/2, f"{int(v)}",
                         ha="center", va="center", fontsize=7, color="white")

    ax1.set_ylabel("Quantité / jour")

    # cumulative revenue line
    ax2 = ax1.twinx()
    ax2.plot(rev_df["Date"], rev_df["cumul"], linewidth=2.2, marker="o", color="#ffffff")
    ax2.set_ylabel("CA cumulatif (€)")

    if shade_august:
        shade_closed_period(ax1)

    mplcyberpunk.add_glow_effects(ax1)
    mplcyberpunk.add_glow_effects(ax2)
    ax1.set_title(title)
    ax1.legend(loc="upper left")
    fig.tight_layout()
    return fig

def simple_line(df_indexed, title, ylabel, shade_august=True):
    _apply_style()
    fig, ax = plt.subplots(figsize=(12,5))
    for col in df_indexed.columns:
        ax.plot(df_indexed.index, df_indexed[col], marker="o", linewidth=2, label=col)
    if shade_august:
        shade_closed_period(ax)
    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(title); ax.set_ylabel(ylabel); ax.legend()
    fig.tight_layout()
    return fig

def pie_split(series, title):
    _apply_style()
    fig, ax = plt.subplots(figsize=(6,6))
    wedges, texts, autotexts = ax.pie(series.values, labels=series.index, autopct="%1.1f%%")
    for t in autotexts: t.set_color("white")
    ax.set_title(title); fig.tight_layout()
    return fig

def heatmap_attendance(att_df, metric="Nombre total de sessions"):
    """Heatmap Jour (lignes) × Heure (colonnes)."""
    _apply_style()
    fig, ax = plt.subplots(figsize=(12,6))

    if "JourFR" not in att_df.columns:
        ax.text(0.5,0.5,"Pas de colonne date/jour trouvée pour construire la heatmap.\n"
                        "Ajoutez 'Date du service' dans attendance.xlsx.", ha="center", va="center")
        return fig
    if "HeureHM" not in att_df.columns:
        ax.text(0.5,0.5,"Pas de colonne heure trouvée (Heure du service / Time).", ha="center", va="center")
        return fig
    if metric not in att_df.columns:
        ax.text(0.5,0.5,f"Colonne '{metric}' introuvable.", ha="center", va="center")
        return fig

    P = att_df.pivot_table(index="JourFR", columns="HeureHM", values=metric, aggfunc="sum").fillna(0)
    # order hours
    try:
        cols_sorted = sorted(P.columns, key=lambda x: (int(x.split(':')[0]), int(x.split(':')[1])) if ':' in x else x)
        P = P[cols_sorted]
    except Exception:
        pass

    im = ax.imshow(P.values, aspect="auto", cmap=_brand_cmap())
    ax.set_yticks(range(P.shape[0])); ax.set_yticklabels(P.index)
    ax.set_xticks(range(P.shape[1])); ax.set_xticklabels(P.columns, rotation=45, ha="right", fontsize=8)
    for i in range(P.shape[0]):
        for j in range(P.shape[1]):
            val = int(P.values[i,j])
            if val>0:
                ax.text(j, i, str(val), ha="center", va="center", color="black", fontsize=7)
    ax.set_title(f"Heatmap présences — {metric}")
    fig.colorbar(im, ax=ax, shrink=0.8, label=metric)
    fig.tight_layout()
    return fig

def top_slots(att_df, metric="Nombre total de sessions", topn=5):
    """Top N créneaux horaires sur la période."""
    _apply_style()
    fig, ax = plt.subplots(figsize=(10,5))
    if "HeureHM" not in att_df.columns or metric not in att_df.columns:
        ax.text(0.5,0.5,"Colonnes nécessaires manquantes (HeureHM / metric).", ha="center", va="center")
        return fig

    s = att_df.groupby("HeureHM")[metric].sum().sort_values(ascending=False).head(topn)[::-1]
    bars = ax.barh(s.index, s.values, color=PRIMARY)
    for b, v in zip(bars, s.values):
        ax.text(v+0.2, b.get_y()+b.get_height()/2, f"{int(v)}", va="center", color="white")
    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(f"Top {topn} créneaux — {metric}")
    ax.set_xlabel(metric)
    fig.tight_layout()
    return fig
