# utils.py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplcyberpunk  # pip install mplcyberpunk

PRIMARY = "#0f6fff"

# --------------------
# FILE PATHS (fixed)
# --------------------
SALES_PATH = os.path.join("data", "sales.xlsx")
ATT_PATH   = os.path.join("data", "attendance.xlsx")

# --------------------
# LOADERS
# --------------------
def load_sales_fixed():
    """Charge data/sales.xlsx (Mindbody 'Sales by Service') et normalise."""
    if not os.path.exists(SALES_PATH):
        raise FileNotFoundError("Fichier ventes introuvable : data/sales.xlsx")

    xls = pd.read_excel(SALES_PATH, sheet_name=None)
    # Heuristique feuille
    sheet = None
    for k in xls.keys():
        lk = k.lower()
        if "service" in lk or "vente" in lk:
            sheet = k; break
    if sheet is None:
        sheet = list(xls.keys())[0]
    df = xls[sheet].copy()

    # Normalisation colonnes principales
    # Date
    date_cols = ["Date d'achat", "Date", "Date de vente", "Date commande", "Sale Date"]
    _ensure_renamed(df, date_cols, "Date")
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Nom du service
    name_cols = ["Nom", "Service", "Service Name", "Nom du service"]
    _ensure_renamed(df, name_cols, "Nom")
    df["Nom"] = df["Nom"].astype(str)

    # Quantité
    qty_cols = ["Quantité", "Qty", "Quantity", "Nombre"]
    _ensure_renamed(df, qty_cols, "Quantité")

    # Montant total
    amt_cols = ["Montant total", "Montant", "Total", "Amount", "CA"]
    _ensure_renamed(df, amt_cols, "Montant total")

    # Regroupement métier
    def group_service(n):
        x = str(n).lower()
        if "découverte" in x:
            return "Découverte"
        if "pack" in x or "recharge" in x:
            return "Packs"
        if "4 x 50" in x or "4x50" in x:
            return "Abonnement 4×50’"
        return "Unitaire"

    df["Groupe"] = df["Nom"].apply(group_service)
    return df


def load_attendance_fixed():
    """Charge data/attendance.xlsx et normalise (créneaux + métriques)."""
    if not os.path.exists(ATT_PATH):
        raise FileNotFoundError("Fichier présence introuvable : data/attendance.xlsx")

    xls = pd.read_excel(ATT_PATH, sheet_name=None)
    # Heuristique feuille
    sheet = None
    for k in xls.keys():
        lk = k.lower()
        if "présence" in lk or "presence" in lk or "attendance" in lk:
            sheet = k; break
    if sheet is None:
        sheet = list(xls.keys())[0]
    df = xls[sheet].copy()

    # Heure créneau (on accepte différents intitulés)
    time_cols = ["Heure du service", "Heure", "Time", "Créneau", "Slot", "Start Time"]
    _ensure_renamed(df, time_cols, "Heure du service", must_exist=False)
    if "Heure du service" in df.columns:
        # si c'est une heure sur la journée :
        df["HeureDT"] = pd.to_datetime(df["Heure du service"], errors="coerce")
        # si c'est juste "09:00" etc., ça passe aussi
        df["heure_label"] = df["HeureDT"].dt.strftime("%H:%M")
        # fallback si NaT partout mais texte dispo
        if df["heure_label"].isna().all():
            df["heure_label"] = df["Heure du service"].astype(str)
    else:
        # dernier recours : si une colonne ressemble à un créneau horaire
        for c in df.columns:
            if any(k in c.lower() for k in ["heure", "time", "slot", "créneau"]):
                df["heure_label"] = df[c].astype(str)
                break
        if "heure_label" not in df.columns:
            df["heure_label"] = ""

    # Sessions totales
    ses_cols = [
        "Nombre total de sessions", "Total Sessions", "Sessions", "Nombre de sessions",
        "Total des sessions"
    ]
    _ensure_renamed(df, ses_cols, "Nombre total de sessions", must_exist=False)

    # Clients uniques
    uniq_cols = ["Clients uniques", "Unique Clients", "Clients", "Unique"]
    _ensure_renamed(df, uniq_cols, "Clients uniques", must_exist=False)

    return df

def _ensure_renamed(df, candidates, target, must_exist=True):
    """Renomme la 1ère colonne trouvée dans candidates -> target."""
    if target in df.columns:
        return
    for c in candidates:
        if c in df.columns:
            df.rename(columns={c: target}, inplace=True)
            return
    if must_exist:
        raise KeyError(f"Colonne requise manquante : {target} (aliases acceptés : {candidates})")


# --------------------
# PLOTS (mplcyberpunk)
# --------------------
def _apply_style():
    plt.style.use("cyberpunk")

def stacked_bar_with_cumulative(daily_pivot, rev_df, title):
    _apply_style()
    fig, ax1 = plt.subplots(figsize=(12,5))
    bottom = np.zeros(len(daily_pivot.index))
    palette = {
        "Découverte": "#6aa6ff",
        "Packs": PRIMARY,
        "Abonnement 4×50’": "#0b4bcc",
        "Unitaire": "#99bbff",
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

    ax2 = ax1.twinx()
    ax2.plot(rev_df["Date"], rev_df["cumul"], linewidth=2.5, marker="o", color="#ffffff")
    ax2.set_ylabel("CA cumulatif (€)")

    mplcyberpunk.add_glow_effects(ax1)
    mplcyberpunk.add_glow_effects(ax2)
    ax1.set_title(title)
    ax1.legend(loc="upper left")
    fig.tight_layout()
    return fig

def simple_line(df_indexed, title, ylabel):
    _apply_style()
    fig, ax = plt.subplots(figsize=(12,5))
    for col in df_indexed.columns:
        ax.plot(df_indexed.index, df_indexed[col], marker="o", linewidth=2, label=col)
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

def bar_by_hour(att_df, col_name, title, ylabel):
    _apply_style()
    fig, ax = plt.subplots(figsize=(12,5))
    if "heure_label" not in att_df.columns:
        ax.text(0.5, 0.5, "Impossible d'identifier les créneaux horaires (heure_label manquante).",
                ha="center", va="center"); return fig
    if col_name not in att_df.columns:
        ax.text(0.5, 0.5, f"Colonne '{col_name}' absente dans le fichier.",
                ha="center", va="center"); return fig

    hours = att_df["heure_label"]
    vals = att_df[col_name].fillna(0).values
    bars = ax.bar(hours, vals, color=PRIMARY)
    for b, v in zip(bars, vals):
        if v > 0:
            ax.text(b.get_x()+b.get_width()/2, v+0.1, f"{int(v)}", ha="center", va="bottom", fontsize=8, color="white")

    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(title); ax.set_ylabel(ylabel)
    plt.xticks(rotation=45); fig.tight_layout()
    return fig
