
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import mplcyberpunk  # style & glow

PRIMARY = "#0f6fff"

# ---------- Data loaders ----------
def load_sales(file):
    """Load 'Sales by Service' Excel and normalize columns + grouping."""
    xls = pd.read_excel(file, sheet_name=None)
    # Heuristic to find the right sheet
    sheet = None
    for k in xls.keys():
        lk = k.lower()
        if "service" in lk or "vente" in lk:
            sheet = k
            break
    if sheet is None:
        sheet = list(xls.keys())[0]
    df = xls[sheet].copy()

    # Normalize columns
    if "Date d'achat" in df.columns:
        df["Date"] = pd.to_datetime(df["Date d'achat"], errors="coerce")
    elif "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="cocoerce")
    else:
        df["Date"] = pd.NaT

    # Standardize naming
    if "Nom" not in df.columns:
        # try to infer the service name column
        for c in df.columns:
            if "Nom" in c or "Service" in c or "Name" in c:
                df.rename(columns={c:"Nom"}, inplace=True)
                break
    if "Quantité" not in df.columns:
        # try to infer quantity
        for c in df.columns:
            if "Quant" in c or "Qty" in c:
                df.rename(columns={c:"Quantité"}, inplace=True)
                break
    if "Montant total" not in df.columns:
        for c in df.columns:
            if "Montant" in c or "Total" in c or "Amount" in c:
                df.rename(columns={c:"Montant total"}, inplace=True)
                break

    df["Nom"] = df["Nom"].astype(str)

    def group_service(n):
        x = str(n).lower()
        if "découverte" in x:
            return "Découverte"
        if "pack" in x or "recharge" in x:
            return "Packs"
        if "4 x 50" in x:
            return "Abonnement 4×50’"
        return "Unitaire"

    df["Groupe"] = df["Nom"].apply(group_service)
    return df


def load_attendance(file):
    """Load 'Attendance Analysis' Excel and normalize time columns."""
    xls = pd.read_excel(file, sheet_name=None)
    # Heuristic to find attendance sheet
    sheet = None
    for k in xls.keys():
        lk = k.lower()
        if "présence" in lk or "presence" in lk or "attendance" in lk:
            sheet = k
            break
    if sheet is None:
        sheet = list(xls.keys())[0]
    df = xls[sheet].copy()

    # Find time columns
    time_col = None
    for c in df.columns:
        if "Heure" in c or "Time" in c:
            time_col = c
            break
    if time_col is not None:
        df["HeureDT"] = pd.to_datetime(df[time_col], errors="coerce")
        df["heure_label"] = df["HeureDT"].dt.strftime("%H:%M")
    else:
        df["heure_label"] = ""

    # Standardize metrics if present
    if "Nombre total de sessions" not in df.columns:
        for c in df.columns:
            if "sessions" in c.lower() and "total" in c.lower():
                df.rename(columns={c:"Nombre total de sessions"}, inplace=True)
                break
    if "Clients uniques" not in df.columns:
        for c in df.columns:
            if "client" in c.lower() and "unique" in c.lower():
                df.rename(columns={c:"Clients uniques"}, inplace=True)
                break

    return df


# ---------- Plot helpers ----------

def apply_cyberpunk():
    """Apply mplcyberpunk style to current figure."""
    plt.style.use("cyberpunk")


def gradient_color(primary_hex=PRIMARY, alpha=1.0):
    """Return a vertical gradient colormap based on primary color."""
    # Simple gradient from brighter to primary
    return LinearSegmentedColormap.from_list(
        "flexlab_grad", [(0.0, (0.8, 0.88, 1.0, alpha)), (1.0, _hex_to_rgba(primary_hex, alpha))], N=256
    )


def _hex_to_rgba(h, alpha=1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16)/255.0 for i in (0,2,4)) + (alpha,)


def stacked_bar_with_cumulative(daily_pivot, rev_df, title):
    """Stacked bar quantities with cumulative revenue line."""
    apply_cyberpunk()
    fig, ax1 = plt.subplots(figsize=(12,5))

    # Stacked bars
    bottom = np.zeros(len(daily_pivot.index))
    labels = list(daily_pivot.columns)
    palette = {
        "Découverte": "#6aa6ff",
        "Packs": "#0f6fff",
        "Abonnement 4×50’": "#0b4bcc",
        "Unitaire": "#99bbff",
    }
    for lab in labels:
        vals = daily_pivot[lab].values
        bars = ax1.bar(daily_pivot.index, vals, bottom=bottom, label=lab, color=palette.get(lab, "#6aa6ff"))
        bottom += vals
        # annotate stacked segments (only if height not too small)
        for b, v in zip(bars, vals):
            if v >= 1:
                ax1.text(b.get_x()+b.get_width()/2, b.get_y()+b.get_height()/2, f"{int(v)}",
                         ha="center", va="center", fontsize=7, color="white")
    ax1.set_ylabel("Quantité vendue / jour")

    # Cumulative revenue line
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
    """Simple cyberpunk line plot for weekly revenue by group."""
    apply_cyberpunk()
    fig, ax = plt.subplots(figsize=(12,5))
    for col in df_indexed.columns:
        ax.plot(df_indexed.index, df_indexed[col], marker="o", linewidth=2, label=col)
    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend()
    fig.tight_layout()
    return fig


def pie_split(series, title):
    """Pie chart for revenue split."""
    apply_cyberpunk()
    fig, ax = plt.subplots(figsize=(6,6))
    labels = list(series.index)
    wedges, texts, autotexts = ax.pie(series.values, labels=labels, autopct="%1.1f%%")
    for t in autotexts:
        t.set_color("white")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def bar_by_hour(att_df, col_name, title, ylabel):
    """Bar chart for attendance by hour label."""
    apply_cyberpunk()
    fig, ax = plt.subplots(figsize=(12,5))
    if "heure_label" not in att_df.columns or col_name not in att_df.columns:
        ax.text(0.5, 0.5, "Colonnes manquantes dans le fichier de présence.", ha="center", va="center")
        return fig
    hours = att_df["heure_label"]
    vals = att_df[col_name].fillna(0).values
    bars = ax.bar(hours, vals, color="#0f6fff")
    for b, v in zip(bars, vals):
        if v > 0:
            ax.text(b.get_x()+b.get_width()/2, v+0.1, f"{int(v)}", ha="center", va="bottom", fontsize=8, color="white")
    mplcyberpunk.add_glow_effects(ax)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45)
    fig.tight_layout()
    return fig
