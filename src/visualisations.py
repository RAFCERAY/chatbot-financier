"""
=============================================================
VISUALISATIONS — Dataset BIS Datathon Société Générale
=============================================================
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
FIG_DIR  = os.path.join(BASE_DIR, "..", "outputs", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Chargement
print("Chargement des données...")
df = pd.read_csv(os.path.join(DATA_DIR, "alteryx.csv"), low_memory=False)
annees = ['2013', '2016', '2019', '2022']
cols_meta = ['Instrument', 'Risk category', 'Reporting country',
             'Currency leg 1', 'Currency leg 2', 'Maturity']
df = df[df['Instrument'] != 'Total (all instruments)'].copy()
df_long = df.melt(id_vars=cols_meta, value_vars=annees,
                  var_name='annee', value_name='volume')
df_long['annee'] = df_long['annee'].astype(int)
df_long = df_long.dropna(subset=['volume'])
print(f"OK {df_long.shape[0]:,} observations")

# ── Graphique 1 — Evolution par instrument ─────────────────
print("\nGraphique 1 — Evolution par instrument...")
top_instr = ['FX swaps', 'Outright forwards', 'Options',
             'Currency swaps', 'Overnight indexed swaps']
df_top = df_long[df_long['Instrument'].isin(top_instr)]
pivot = df_top.groupby(['annee', 'Instrument'])['volume'].sum().unstack()

fig, ax = plt.subplots(figsize=(12, 6))
colors = ['#1E3A5F', '#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
for i, instr in enumerate(top_instr):
    if instr in pivot.columns:
        ax.plot(pivot.index, pivot[instr]/1e6, marker='o',
                linewidth=2.5, label=instr, color=colors[i])
ax.set_title('Evolution des volumes par instrument (2013-2022)\nMilliards $',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Année')
ax.set_ylabel('Volume (milliers de milliards $)')
ax.legend(loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "evolution_instruments.png"), dpi=150)
print("   Sauvegardé !")

# ── Graphique 2 — Top 10 pays en 2022 ─────────────────────
print("\nGraphique 2 — Top 10 pays 2022...")
df_2022 = df_long[
    (df_long['annee'] == 2022) &
    (~df_long['Reporting country'].str.contains('total|all', case=False, na=False))
]
top_pays = df_2022.groupby('Reporting country')['volume'].sum().nlargest(10)

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(range(len(top_pays)), top_pays.values/1e6,
               color='#1E3A5F', alpha=0.85)
ax.set_yticks(range(len(top_pays)))
ax.set_yticklabels(top_pays.index, fontsize=11)
ax.set_title('Top 10 pays — Volume dérivés OTC (2022)\nMilliards $',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Volume (milliers de milliards $)')
for bar, val in zip(bars, top_pays.values):
    ax.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2,
            f'{val/1e6:.0f}K Mds', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "top_pays_2022.png"), dpi=150)
print("   Sauvegardé !")

# ── Graphique 3 — Breakdown par catégorie de risque ────────
print("\nGraphique 3 — Breakdown risque...")
df_risk = df_long[
    ~df_long['Risk category'].str.contains('total|all', case=False, na=False)
]
pivot_risk = df_risk.groupby(['annee', 'Risk category'])['volume'].sum().unstack()

fig, ax = plt.subplots(figsize=(10, 6))
pivot_risk_pct = pivot_risk.div(pivot_risk.sum(axis=1), axis=0) * 100
colors_risk = ['#1E3A5F', '#2E86AB', '#A23B72', '#F18F01']
pivot_risk_pct.plot(kind='bar', stacked=True, ax=ax,
                    color=colors_risk[:len(pivot_risk_pct.columns)],
                    alpha=0.85)
ax.set_title('Répartition par catégorie de risque (2013-2022)\n%',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Année')
ax.set_ylabel('Part (%)')
ax.legend(loc='upper right', fontsize=9)
ax.set_xticklabels(pivot_risk_pct.index, rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "breakdown_risque.png"), dpi=150)
print("   Sauvegardé !")

# ── Graphique 4 — Top paires de devises ────────────────────
print("\nGraphique 4 — Top paires de devises 2022...")
df_long['paire'] = df_long['Currency leg 1'] + '/' + df_long['Currency leg 2']
df_paires = df_long[
    (df_long['annee'] == 2022) &
    (~df_long['Currency leg 1'].str.contains('total|all', case=False, na=False)) &
    (~df_long['Currency leg 2'].str.contains('total|all', case=False, na=False))
]
top_paires = df_paires.groupby('paire')['volume'].sum().nlargest(10)

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(range(len(top_paires)), top_paires.values/1e6,
       color='#2E86AB', alpha=0.85)
ax.set_xticks(range(len(top_paires)))
ax.set_xticklabels(top_paires.index, rotation=45, ha='right', fontsize=10)
ax.set_title('Top 10 paires de devises — Volume OTC (2022)\nMilliards $',
             fontsize=14, fontweight='bold')
ax.set_ylabel('Volume (milliers de milliards $)')
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "top_paires_devises.png"), dpi=150)
print("   Sauvegardé !")

print("\n" + "="*55)
print(f"4 graphiques sauvegardés dans outputs/figures/")
print("="*55)