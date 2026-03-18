"""
=============================================================
RAPPORT AUTOMATIQUE — Datathon Société Générale
=============================================================
Objectif : Générer automatiquement un rapport financier
           avec analyse, KPIs et graphiques
=============================================================
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
FIG_DIR  = os.path.join(BASE_DIR, "..", "outputs", "figures")
RPT_DIR  = os.path.join(BASE_DIR, "..", "outputs", "rapports")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RPT_DIR, exist_ok=True)

# ── Chargement ─────────────────────────────────────────────
print("="*55)
print("GENERATION RAPPORT AUTOMATIQUE")
print("="*55)

df = pd.read_csv(os.path.join(DATA_DIR, "alteryx.csv"), low_memory=False)
annees = ['2013', '2016', '2019', '2022']
cols_meta = ['Instrument', 'Risk category', 'Reporting country',
             'Currency leg 1', 'Currency leg 2', 'Maturity']
df = df[df['Instrument'] != 'Total (all instruments)'].copy()
df_long = df.melt(id_vars=cols_meta, value_vars=annees,
                  var_name='annee', value_name='volume')
df_long['annee'] = df_long['annee'].astype(int)
df_long = df_long.dropna(subset=['volume'])
print(f"OK {df_long.shape[0]:,} observations chargées")

# ── Calcul des KPIs ────────────────────────────────────────
print("\nCalcul des KPIs...")

# KPI 1 — Volume total par année
vol_annee = df_long.groupby('annee')['volume'].sum()

# KPI 2 — Top instrument 2022
top_instr_2022 = df_long[df_long['annee']==2022].groupby(
    'Instrument')['volume'].sum().nlargest(3)

# KPI 3 — Croissance FX swaps
fx = df_long[df_long['Instrument']=='FX swaps'].groupby('annee')['volume'].sum()
croissance_fx = ((fx[2022] - fx[2013]) / fx[2013] * 100).round(1)

# KPI 4 — Top pays 2022
top_pays_2022 = df_long[
    (df_long['annee']==2022) &
    (~df_long['Reporting country'].str.contains('total|all', case=False, na=False))
].groupby('Reporting country')['volume'].sum().nlargest(3)

# KPI 5 — Part FX swaps dans le total 2022
total_2022 = df_long[df_long['annee']==2022]['volume'].sum()
part_fx = (fx[2022] / total_2022 * 100).round(1)

print(f"   Volume total 2022    : {total_2022/1e9:,.2f} milliers de milliards $")
print(f"   Croissance FX swaps  : +{croissance_fx}% (2013-2022)")
print(f"   Part FX swaps 2022   : {part_fx}% du marché total")

# ── Génération du rapport texte ────────────────────────────
date_rapport = datetime.now().strftime("%d/%m/%Y")
rapport = f"""
==============================================================
RAPPORT AUTOMATIQUE — MARCHE DES DERIVES OTC
Société Générale Global Solution Centre
Date : {date_rapport}
Source : BIS — Bank for International Settlements
==============================================================

1. RESUME EXECUTIF
------------------
Ce rapport analyse l'evolution des marches de derives OTC
de 2013 a 2022, couvrant {df_long.shape[0]:,} observations
issues de la base BIS.

2. KPIS CLES
------------
Volume total 2022        : {total_2022/1e9:,.1f} milliers de milliards $
Croissance FX swaps      : +{croissance_fx}% entre 2013 et 2022
Part FX swaps marche     : {part_fx}% du volume total 2022

3. EVOLUTION DES VOLUMES PAR ANNEE
-----------------------------------
"""
for annee, vol in vol_annee.items():
    variation = ""
    if annee > 2013:
        var = ((vol - vol_annee[annee-3]) / vol_annee[annee-3] * 100)
        variation = f"  ({var:+.1f}% vs période précédente)"
    rapport += f"   {annee} : {vol/1e9:,.1f} milliers de milliards ${variation}\n"

rapport += f"""
4. TOP 3 INSTRUMENTS (2022)
----------------------------
"""
for instr, vol in top_instr_2022.items():
    part = vol / total_2022 * 100
    rapport += f"   {instr:30s} : {vol/1e6:>10,.0f} milliards $ ({part:.1f}%)\n"

rapport += f"""
5. TOP 3 PAYS (2022)
---------------------
"""
for pays, vol in top_pays_2022.items():
    rapport += f"   {pays:30s} : {vol/1e6:>10,.0f} milliards $\n"

rapport += f"""
6. ANALYSE FX SWAPS
--------------------
Les FX swaps sont l'instrument dominant du marche OTC.
Leur croissance de +{croissance_fx}% entre 2013 et 2022
reflète l'internationalisation croissante des echanges
et le besoin de couverture de risque de change.

"""
for annee, vol in fx.items():
    rapport += f"   {annee} : {vol/1e6:,.0f} milliards $\n"

rapport += f"""
7. CONCLUSIONS ET RECOMMANDATIONS
-----------------------------------
- Les FX swaps representent {part_fx}% du marche — instrument strategique
- Le Royaume-Uni reste la 1ere place financiere mondiale pour les derives
- Croissance soutenue post-Covid : reprise des volumes en 2022
- Recommandation : renforcer le monitoring des FX swaps EUR/USD

==============================================================
Rapport genere automatiquement par le Chatbot Financier Gen AI
Datathon MBA ESG / ESG Executive / Societe Generale — 2024
==============================================================
"""

# Sauvegarde rapport texte
output_txt = os.path.join(RPT_DIR, "rapport_derives_OTC.txt")
with open(output_txt, 'w', encoding='utf-8') as f:
    f.write(rapport)
print(f"\nRapport texte sauvegardé : {output_txt}")
print(rapport)