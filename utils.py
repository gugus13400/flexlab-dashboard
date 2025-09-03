# utils.py
import os, base64
import pandas as pd
import numpy as np

# ---------- CONSTANTS ----------
PRIMARY = "#0f6fff"
SALES_PATH = os.path.join("data", "sales.xlsx")
ATT_PATH   = os.path.join("data", "attendance.xlsx")

# ---------- LAZY MATPLOTLIB to avoid deploy issues ----------
def _mpl():
    import matplotlib
    matplotlib.use("Agg")  # headless backend for Streamlit Cloud
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    import mplcyberpunk
    return matplotlib, plt, LinearSegmentedColormap, mplcyberpunk

# ---------- BRANDING ----------
def styled_title(logo_path=None, title="FlexLab Dashboard", subtitle=""):
    import streamlit as st
    logo_html = ""
    if logo_path and os.path.exists(logo_path):
        encoded = base64.b64encode(open(logo_path, "rb").read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded}' style='height:38px;margin-right:8px;vertical-align:middle'/>"
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:2px">
        {logo_html}
        <h1 style='margin:0'>{title}</h1>
    </div>
    <p style='color:#9bb7ff;margin-top:0'>{subtitle}</p>
    """, unsafe_allow_html=True)

def inject_background(image_path="assets/bg.jpg"):
    import streamlit as st
    if not os.path.exists(image_path):
        return
    encoded = base64.b64encode(open(image_path, "rb").read()).decode()
    css = f"""
    <style>
      .stApp {{
         background: url('data:image/jpg;base64,{encoded}') no-repeat center fixed;
         background-size: cover;
      }}
      [data-testid="stSidebar"] > div:first-child {{
         background: rgba(16,26,51,0.9);
      }}
      .block-container {{
         background: rgba(11,18,36,0.82);
         border-radius: 16px;
         padding: 20px 30px;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ---------- HELPERS ----------
def _ensure_renamed(df, candidates, target, must_exist=True):
    if target in df.columns:
        return
    for c in candidates:
        if c in df.columns:
            df.rename(columns={c: target}, inplace=True)
            return
    if must_exist:
        raise KeyError(f"Required column missing: {target} (accepted: {candidates})")

def _brand_cmap():
    _, plt, LinearSegmentedColormap, _ = _mpl()
    return LinearSegmentedColormap.from_list(
        "flexlab_cmap",
        [(0.85, 0.92, 1.0, 1.0), _hex_to_rgba(PRIMARY, 1.0)],
        N=256
    )

def _hex_to_rgba(h, alpha=1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16)/255.0 for i in (0,2,4)) + (alpha,)

def shade_closed_period(ax, start="2025-08-02", end="2025-08-24", label="Studio fermé (été)"):
    import pandas as pd
    try:
        s = pd.to_datetime(start); e = pd.to_datetime(end)
        ax.axvspan(s, e, color="grey", alpha=0.25, label=label)
        # dedupe legend
        handles, labels = ax.get_legend_handles_labels()
        dedup = dict(zip(labels, handles))
        ax.legend(dedup.values(), dedup.keys(), loc="upper left")
    except Exception:
        pass

# ---------- LOADERS ----------
def load_sales_fixed():
    if not os.path.exists(SALES_PATH):
        raise FileNotFoundError("Missing file: data/sales.xlsx")
    xls = pd.read_excel(SALES_PATH, sheet_name=None)
    sheet = None
    for k in xls.keys():
        lk = k.lower()
        if "service" in lk or "vente" in lk:
            sheet = k; break
    if sheet is None:
        sheet = list(xls.keys())[0]
    df = xls[sheet].copy()

    _ensure_renamed(df, ["Date d'achat","Date de vente","Date","Sale Date","Date commande"], "Date")
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    _ensure_renamed(df, ["Nom","Service","Service Name","Nom du service"], "Nom")
    _ensure_renamed(df, ["Quantité","Qty","Quantity","Nombre"], "Quantité")
    _ensure_renamed(df, ["Montant total","Montant","Total","Amount","CA"], "Montant total")
    if "Client" not in df.columns:
        # try some typical client fields
        for c in df.columns:
            if "client" in c.lower() or "customer" in c.lower():
                df.rename(columns={c: "Client"}, inplace=True)
                break
    df["Nom"] = df["Nom"].astype(str)

    def group_service(n):
        x = str(n).lower()
        if "découverte" in x: return "Découverte"
        if "pack" in x or "recharge" in x: return "Packs"
        if "4 x 50" in x or "4x50" in x: return "Abonnement 4×50’"
        return "Unitaire (autres)"
    df["Groupe"] = df["Nom"].apply(group_service)
    return df

def load_attendance_fixed():
    if not os.path.exists(ATT_PATH):
        raise FileNotFoundError("Missing file: data/attendance.xlsx")
    xls = pd.read_excel(ATT_PATH, sheet_name=None)
    sheet = None
    for k in xls.keys():
        lk = k.lower()
        if "présence" in lk or "presence" in lk or "attendance" in lk:
            sheet = k; break
    if sheet is None:
        sheet = list(xls.keys())[0]
    df = xls[sheet].copy()

    # --- DATE ---
    # élargit la liste d’alias possibles
    date_alias = [
        "Date du service","Date","Service Date","Date de séance","Class Date",
        "Appointment Date","Schedule Date","Jour"
    ]
    _ensure_renamed(df, date_alias, "Date", must_exist=False)
    if "Date" in df.columns:
        # si c'est du texte type "2025-08-03" → to_datetime
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        # si tout est NaT mais une autre colonne contient une date, on ne force pas
    # Jour (FR)
    if "Date" in df.columns:
        df["Jour"] = df["Date"].dt.day_name()
        mapping = {"Monday":"Lundi","Tuesday":"Mardi","Wednesday":"Mercredi","Thursday":"Jeudi",
                   "Friday":"Vendredi","Saturday":"Samedi","Sunday":"Dimanche"}
        df["JourFR"] = df["Jour"].map(mapping)
        df["JourFR"] = pd.Categorical(df["JourFR"],
            categories=["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"],
            ordered=True)

    # --- HEURE / CRÉNEAU ---
    _ensure_renamed(df, ["Heure du service","Heure","Time","Créneau","Slot","Start Time"], "Heure du service", must_exist=False)
    if "Heure du service" in df.columns:
        # Essayez de parser une heure; sinon garder string
        tmp = pd.to_datetime(df["Heure du service"], errors="coerce")
        df["HeureHM"] = tmp.dt.strftime("%H:%M")
        if df["HeureHM"].isna().all():
            df["HeureHM"] = df["Heure du service"].astype(str)
    else:
        df["HeureHM"] = ""

    # --- MÉTRIQUES ---
    _ensure_renamed(df, ["Nombre total de sessions","Total Sessions","Sessions","Nombre de sessions","Total des sessions"],
                    "Nombre total de sessions", must_exist=False)
    _ensure_renamed(df, ["Clients uniques","Unique Clients","Clients","Unique"], "Clients uniques", must_exist=False)

    return df

# ---------- METRICS & CHARTS ----------
def kpi_row(df):
    ca_total = float(df["Montant total"].sum())
    qty_total = int(df["Quantité"].sum())
    # approx clients uniques (if Client column exists, use it)
    if "Client" in df.columns:
        clients_uniques = df["Client"].nunique()
        clients_help = "Basé sur la colonne Client."
    else:
        # fallback approx: count unique buyers per day then sum unique names if any, else estimate by Découverte count
        clients_uniques = int(df[df["Groupe"]=="Découverte"]["Quantité"].sum()) + int(df[df["Groupe"]!="Découverte"]["Quantité"].sum()*0.3)
        clients_help = "Approximation (pas de colonne Client)."

    # weekly packs sold (latest full week)
    weekly = df.groupby([pd.Grouper(key="Date", freq="W-MON"), "Groupe"]).agg(qty=("Quantité","sum"), rev=("Montant total","sum")).reset_index()
    if weekly.empty:
        packs_week = 0
    else:
        last_week = weekly["Date"].max()
        packs_week = int(weekly[(weekly["Date"]==last_week) & (weekly["Groupe"]=="Packs")]["qty"].sum())

    # conversion Découverte -> Pack (rough)
    if "Client" in df.columns:
        by_client = df.groupby("Client")["Groupe"].apply(set)
        converted = sum(1 for s in by_client if ("Découverte" in s and ("Packs" in s or "Abonnement 4×50’" in s)))
        tried = sum(1 for s in by_client if "Découverte" in s)
        conv = converted/ tried if tried else 0.0
        conv_help = "Clients ayant fait Découverte puis Pack/Abonnement (toutes périodes)."
    else:
        # fallback: packs qty / discovery qty (not exact clients)
        disc = df[df["Groupe"]=="Découverte"]["Quantité"].sum()
        packs = df[df["Groupe"].isin(["Packs","Abonnement 4×50’"])]["Quantité"].sum()
        conv = float(packs) / disc if disc else 0.0
        conv_help = "Approximation (pas de colonne Client)."

    # ARPU = CA / clients_uniques (period)
    arpu = ca_total / clients_uniques if clients_uniques else 0.0

    return {
        "ca_total_fmt": f"{ca_total:,.0f}".replace(",", " "),
        "qty_total_fmt": f"{qty_total:,}".replace(",", " "),
        "clients_uniques_fmt": f"{clients_uniques:,}".replace(",", " "),
        "clients_help": clients_help,
        "packs_week_fmt": f"{packs_week:,}".replace(",", " "),
        "conv_discovery_to_pack_fmt": f"{conv:.0%}",
        "conv_help": conv_help,
        "arpu_fmt": f"{arpu:,.0f}".replace(",", " ")
    }

def stacked_bar_with_cumulative(df, title):
    _, plt, _, mplcyberpunk = _mpl()
    plt.style.use("cyberpunk")

    daily = df.groupby([pd.Grouper(key="Date", freq="D"), "Groupe"]).agg(
        quantite=("Quantité","sum"), ventes=("Montant total","sum")).reset_index()
    pivot = daily.pivot(index="Date", columns="Groupe", values="quantite").fillna(0)

    fig, ax1 = plt.subplots(figsize=(12,5))
    bottom = np.zeros(len(pivot.index))
    palette = {"Découverte":"#6aa6ff","Packs":PRIMARY,"Abonnement 4×50’":"#0b4bcc","Unitaire (autres)":"#99bbff"}
    for lab in pivot.columns:
        vals = pivot[lab].values
        bars = ax1.bar(pivot.index, vals, bottom=bottom, label=lab, color=palette.get(lab, "#6aa6ff"))
        bottom += vals
        for b, v in zip(bars, vals):
            if v >= 1:
                ax1.text(b.get_x()+b.get_width()/2, b.get_y()+b.get_height()/2, f"{int(v)}",
                         ha="center", va="center", fontsize=7, color="white")
    ax1.set_ylabel("Quantité / jour")

    # cumulative revenue
    rev = df.groupby(pd.Grouper(key="Date", freq="D"))["Montant total"].sum().reset_index()
    rev["cumul"] = rev["Montant total"].cumsum()

    ax2 = ax1.twinx()
    ax2.plot(rev["Date"], rev["cumul"], linewidth=2.2, marker="o", color="#ffffff")
    ax2.set_ylabel("CA cumulatif (€)")

    shade_closed_period(ax1)
    mplcyberpunk.add_glow_effects(ax1); mplcyberpunk.add_glow_effects(ax2)
    ax1.set_title(title)
    handles, labels = ax1.get_legend_handles_labels()
    dedup = dict(zip(labels, handles))
    ax1.legend(dedup.values(), dedup.keys(), loc="upper left")
    fig.tight_layout()
    return fig

def simple_line_growth(df, title):
    _, plt, _, mplcyberpunk = _mpl()
    plt.style.use("cyberpunk")

    weekly = df.groupby(pd.Grouper(key="Date", freq="W-MON"))["Montant total"].sum()
    growth = weekly.pct_change().fillna(0)

    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(weekly.index, weekly.values, marker="o", linewidth=2, label="CA hebdo (€)")
    for x, y, g in zip(weekly.index, weekly.values, growth.values):
        ax.text(x, y, f"{g:+.0%}", ha="center", va="bottom", fontsize=8, color="white")
    shade_closed_period(ax)
    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(title); ax.set_ylabel("€"); ax.legend()
    fig.tight_layout()
    return fig

def weekly_packs_vs_clients(df, title):
    _, plt, _, mplcyberpunk = _mpl(); plt.style.use("cyberpunk")
    # clients uniques by week (true if Client exists)
    if "Client" in df.columns:
        cu = df.groupby([pd.Grouper(key="Date", freq="W-MON")])["Client"].nunique().rename("clients_uniques")
    else:
        # fallback: Découverte count proxy
        cu = df[df["Groupe"]=="Découverte"].groupby(pd.Grouper(key="Date", freq="W-MON"))["Quantité"].sum().rename("clients_uniques")
    packs = df[df["Groupe"]=="Packs"].groupby(pd.Grouper(key="Date", freq="W-MON"))["Quantité"].sum().rename("packs").reindex(cu.index).fillna(0)
    conv = (packs / cu.replace(0, np.nan)).fillna(0)

    fig, ax1 = plt.subplots(figsize=(12,5))
    width = 3
    ax1.bar(cu.index - pd.Timedelta(days=1), cu.values, width=width, label="Clients uniques", color="#6aa6ff")
    ax1.bar(packs.index + pd.Timedelta(days=1), packs.values, width=width, label="Packs vendus", color=PRIMARY, alpha=0.9)
    ax1.set_ylabel("Volumes")

    ax2 = ax1.twinx()
    ax2.plot(conv.index, (conv*100.0).values, marker="o", linewidth=2, color="#ffffff", label="% conv")
    ax2.set_ylabel("% conv (packs / clients uniques)")

    shade_closed_period(ax1)
    mplcyberpunk.add_glow_effects(ax1); mplcyberpunk.add_glow_effects(ax2)
    ax1.set_title(title)
    handles, labels = ax1.get_legend_handles_labels()
    dedup = dict(zip(labels, handles))
    ax1.legend(handles, labels, loc="upper left")
    fig.tight_layout()
    return fig

def arpu_line(df, title):
    _, plt, _, mplcyberpunk = _mpl(); plt.style.use("cyberpunk")

    if "Client" in df.columns:
        weekly_clients = df.groupby(pd.Grouper(key="Date", freq="W-MON"))["Client"].nunique()
    else:
        weekly_clients = df.groupby(pd.Grouper(key="Date", freq="W-MON"))["Quantité"].sum().apply(lambda x: max(1, int(x*0.4)))
    weekly_rev = df.groupby(pd.Grouper(key="Date", freq="W-MON"))["Montant total"].sum()
    arpu = (weekly_rev / weekly_clients.replace(0, np.nan)).fillna(0)

    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(arpu.index, arpu.values, marker="o", linewidth=2, label="ARPU (€)")
    shade_closed_period(ax)
    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(title); ax.set_ylabel("€ / client"); ax.legend()
    fig.tight_layout()
    return fig

def share_area(df, title):
    _, plt, _, mplcyberpunk = _mpl(); plt.style.use("cyberpunk")
    weekly = df.groupby([pd.Grouper(key="Date", freq="W-MON"), "Groupe"])["Montant total"].sum().reset_index()
    pivot = weekly.pivot(index="Date", columns="Groupe", values="Montant total").fillna(0)
    totals = pivot.sum(axis=1).replace(0, np.nan)
    share = (pivot.T / totals).T.fillna(0)

    fig, ax = plt.subplots(figsize=(12,5))
    colors = {"Découverte":"#6aa6ff","Packs":PRIMARY,"Abonnement 4×50’":"#0b4bcc","Unitaire (autres)":"#99bbff"}
    ax.stackplot(share.index, [share[c] for c in share.columns], labels=share.columns, colors=[colors.get(c) for c in share.columns])
    shade_closed_period(ax)
    mplcyberpunk.add_glow_effects(ax)
    ax.set_ylim(0,1); ax.set_yticks([0,0.25,0.5,0.75,1.0]); ax.set_yticklabels(["0%","25%","50%","75%","100%"])
    ax.set_title(title); ax.legend(loc="upper left")
    fig.tight_layout()
    return fig

def pie_split(series, title):
    _, plt, _, _ = _mpl(); plt.style.use("cyberpunk")
    fig, ax = plt.subplots(figsize=(6,6))
    wedges, texts, autotexts = ax.pie(series.values, labels=series.index, autopct="%1.1f%%")
    for t in autotexts: t.set_color("white")
    ax.set_title(title); fig.tight_layout()
    return fig

# ----- Attendance charts -----
def heatmap_attendance(att_df, metric="Nombre total de sessions"):
    _, plt, LinearSegmentedColormap, _ = _mpl(); plt.style.use("cyberpunk")
    fig, ax = plt.subplots(figsize=(12,6))
    if "JourFR" not in att_df.columns:
        ax.text(0.5,0.5,"Aucune colonne 'Date du service' → impossible de construire Jour × Heure.",
                ha="center", va="center"); return fig
    if "HeureHM" not in att_df.columns:
        ax.text(0.5,0.5,"Aucune colonne heure (Heure du service / Time).", ha="center", va="center"); return fig
    if metric not in att_df.columns:
        ax.text(0.5,0.5,f"Colonne '{metric}' manquante.", ha="center", va="center"); return fig

    P = att_df.pivot_table(index="JourFR", columns="HeureHM", values=metric, aggfunc="sum").fillna(0)
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
    _, plt, _, mplcyberpunk = _mpl(); plt.style.use("cyberpunk")
    fig, ax = plt.subplots(figsize=(10,5))
    if "HeureHM" not in att_df.columns or metric not in att_df.columns:
        ax.text(0.5,0.5,"Colonnes manquantes (HeureHM/metric).", ha="center", va="center"); return fig
    s = att_df.groupby("HeureHM")[metric].sum().sort_values(ascending=False).head(topn)[::-1]
    bars = ax.barh(s.index, s.values, color=PRIMARY)
    for b, v in zip(bars, s.values):
        ax.text(v+0.2, b.get_y()+b.get_height()/2, f"{int(v)}", va="center", color="white")
    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(f"Top {topn} créneaux — {metric}")
    ax.set_xlabel(metric); fig.tight_layout()
    return fig

def weekly_unique_clients(att_df, title="Clients uniques par semaine"):
    _, plt, _, mplcyberpunk = _mpl(); plt.style.use("cyberpunk")
    fig, ax = plt.subplots(figsize=(12,5))
    if "Date" not in att_df.columns or "Clients uniques" not in att_df.columns:
        ax.text(0.5,0.5,"Colonnes 'Date' ou 'Clients uniques' absentes.", ha="center", va="center"); return fig
    s = att_df.groupby(pd.Grouper(key="Date", freq="W-MON"))["Clients uniques"].sum()
    ax.plot(s.index, s.values, marker="o", linewidth=2, label="Clients uniques / semaine")
    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(title); ax.legend(); fig.tight_layout()
    return fig

def occupancy_gauge(att_df, capacity=0):
    _, plt, _, mplcyberpunk = _mpl(); plt.style.use("cyberpunk")
    fig, ax = plt.subplots(figsize=(5,5))

    if capacity <= 0 or "Nombre total de sessions" not in att_df.columns:
        ax.text(0.5,0.5,"Capacité non fournie ou colonne sessions manquante.", ha="center", va="center")
        return fig

    # Si Date dispo → vraie moyenne journalière
    if "Date" in att_df.columns and pd.api.types.is_datetime64_any_dtype(att_df["Date"]):
        daily = att_df.groupby(pd.Grouper(key="Date", freq="D"))["Nombre total de sessions"].sum()
        days = max(1, daily.shape[0])
        avg_sessions = float(daily.mean())
    else:
        # fallback : moyenne approximative sur l’ensemble du fichier
        total = float(att_df["Nombre total de sessions"].sum())
        # impossible d'inférer le nombre de jours → on affiche un ratio "par jour (approx.)"
        days = 1
        avg_sessions = total  # on suppose que le fichier correspond à ~1 journée si on n'a pas de dates

    occ = (avg_sessions / capacity) if capacity else 0.0
    ax.barh(["Occupation"], [occ*100], color=PRIMARY)
    ax.set_xlim(0,100); ax.set_xlabel("%"); ax.set_title("Occupation moyenne (≈)")

    for p in ax.patches:
        ax.text(min(99, p.get_width()+1), p.get_y()+p.get_height()/2, f"{occ*100:.0f}%", va="center", color="white")

    mplcyberpunk.add_glow_effects(ax); fig.tight_layout()
    return fig

def weekly_unique_clients_bar(att_df, title="Clients uniques par semaine (bar)"):
    _, plt, _, mplcyberpunk = _mpl(); plt.style.use("cyberpunk")
    fig, ax = plt.subplots(figsize=(12,5))

    if "Date" not in att_df.columns or "Clients uniques" not in att_df.columns:
        ax.text(0.5,0.5,"Colonnes 'Date' ou 'Clients uniques' absentes.", ha="center", va="center")
        return fig

    if not pd.api.types.is_datetime64_any_dtype(att_df["Date"]):
        # tente un parse si ce n'est pas un datetime
        try:
            att_df = att_df.copy()
            att_df["Date"] = pd.to_datetime(att_df["Date"], errors="coerce")
        except Exception:
            ax.text(0.5,0.5,"Colonne 'Date' non convertible.", ha="center", va="center")
            return fig

    s = att_df.groupby(pd.Grouper(key="Date", freq="W-MON"))["Clients uniques"].sum()
    bars = ax.bar(s.index, s.values, width=5, color=PRIMARY, label="Clients uniques")
    for b, v in zip(bars, s.values):
        ax.text(b.get_x()+b.get_width()/2, v+0.5, f"{int(v)}", ha="center", va="bottom", fontsize=8, color="white")

    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(title); ax.legend(); fig.tight_layout()
    return fig

# ----- Growth page helpers -----
def funnel_conversion(df):
    _, plt, _, mplcyberpunk = _mpl(); plt.style.use("cyberpunk")
    fig, ax = plt.subplots(figsize=(6,5))
    if "Client" in df.columns:
        g = df.groupby("Client")["Groupe"].apply(set)
        step1 = sum(1 for s in g if "Découverte" in s)
        step2 = sum(1 for s in g if ("Découverte" in s and "Packs" in s))
        step3 = sum(1 for s in g if ("Découverte" in s and "Abonnement 4×50’" in s))
        bars = [step1, step2, step3]
        labels = ["Découverte", "→ Pack", "→ Abonnement"]
        colors = ["#6aa6ff", PRIMARY, "#0b4bcc"]
        ax.barh(range(3)[::-1], bars[::-1], color=colors[::-1])
        for i, v in enumerate(bars[::-1]):
            ax.text(v+1, i, f"{v}", va="center", color="white")
        ax.set_yticks(range(3)); ax.set_yticklabels(labels[::-1]); ax.set_title("Funnel clients")
        mplcyberpunk.add_glow_effects(ax); fig.tight_layout()
        notes = "Funnel réel (basé sur la colonne Client)."
        return fig, notes
    else:
        # proxy funnel using quantities
        step1 = int(df[df["Groupe"]=="Découverte"]["Quantité"].sum())
        step2 = int(df[df["Groupe"]=="Packs"]["Quantité"].sum())
        step3 = int(df[df["Groupe"]=="Abonnement 4×50’"]["Quantité"].sum())
        bars = [step1, step2, step3]
        labels = ["Découverte (qty)", "→ Pack (qty)", "→ Abonnement (qty)"]
        colors = ["#6aa6ff", PRIMARY, "#0b4bcc"]
        ax.barh(range(3)[::-1], bars[::-1], color=colors[::-1])
        for i, v in enumerate(bars[::-1]):
            ax.text(v+1, i, f"{v}", va="center", color="white")
        ax.set_yticks(range(3)); ax.set_yticklabels(labels[::-1]); ax.set_title("Funnel (approx.)")
        mplcyberpunk.add_glow_effects(ax); fig.tight_layout()
        return fig, "Approximation (pas de colonne Client)."

def churn_block(df):
    # Simple definition: clients qui ont fait Découverte mais jamais Pack/Abonnement
    if "Client" in df.columns:
        g = df.groupby("Client")["Groupe"].apply(set)
        tried = sum(1 for s in g if "Découverte" in s)
        churned = sum(1 for s in g if ("Découverte" in s and not ("Packs" in s or "Abonnement 4×50’" in s)))
        churn = churned / tried if tried else 0.0
        return f"<div style='font-size:16px'>Churn Découverte ≈ <b>{churn:.0%}</b> — clients Découverte n'ayant pas poursuivi.</div>"
    else:
        return "<div style='font-size:16px'>Impossible de calculer un churn client sans colonne <b>Client</b>.</div>"

def cohort_note():
    return ("Pour une vraie analyse de cohortes (W0/W4/W8), il faut un ID client stable et la date de 1ère visite. "
            "Ensuite on suit la part revenant à +7/+30/+60 jours. Prêt à l’implémenter si tes exports le permettent.")

def warn_if_missing_cols(df):
    import streamlit as st
    msgs = []
    if "Client" not in df.columns:
        msgs.append("✅ Ajoute la colonne **Client** dans `sales.xlsx` pour des KPIs de rétention précis (conversion, churn, ARPU réels).")
    if msgs:
        st.warning("<br>".join(msgs), icon="⚠️")
