
# FlexLab Dashboard (Streamlit)

Tableau de bord investisseur **prêt à déployer** (Streamlit) :
- Page **Ventes** : barres quotidiennes empilées par service (Découverte / Packs / Abonnement 4×50’ / Unitaire) + **CA cumulatif**, tendance hebdo, pie chart.
- Page **Présences** : sessions & clients uniques par créneau horaire (optimisation planning).
- Style **mplcyberpunk** + thème FlexLab (`#0f6fff`).

## Lancer en local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déployer (Streamlit Cloud)
1) Crée un repo GitHub (ex: `flexlab-dashboard`)
2) Pousse ce dossier (voir commandes ci-dessous)
3) Sur https://share.streamlit.io, connecte ton repo et sélectionne `app.py`

## Uploads
- Page Ventes : Excel **Sales by Service Report** (Mindbody)
- Page Présences : Excel **Attendance Analysis Report** (Mindbody)

> L'app détecte automatiquement les bonnes feuilles et colonnes (heuristique robuste).

## Git — commandes rapides
```bash
git init
git add .
git commit -m "feat: flexlab streamlit dashboard v1"
git branch -M main
git remote add origin https://github.com/<ton-user>/flexlab-dashboard.git
git push -u origin main
```

## Améliorations possibles
- KPI conversion **Découverte → Pack/Abonnement** (si ID client dispo)
- **MRR** des abonnements + cohorte mensuelle
- **Heatmap** Heures × Jours (si dates présentes dans Attendance)
- Export PDF/PNG auto des graphs pour pitch deck
```

# flexlab-dashboard
