"""
=============================================================
EXPLORATION — Dataset BIS Datathon Société Générale
=============================================================
"""
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

print("="*55)
print("EXPLORATION DU DATASET ALTERYX")
print("="*55)

# Chargement échantillon
df = pd.read_csv(os.path.join(DATA_DIR, "alteryx.csv"),
                 nrows=1000, low_memory=False)

print(f"\n📊 Dimensions : {df.shape}")
print(f"\n📋 Colonnes ({len(df.columns)}) :")
for i, col in enumerate(df.columns):
    print(f"   {i:3d}. {col}")

print(f"\n📊 Types de données :")
print(df.dtypes)

print(f"\n📊 Aperçu des 3 premières lignes :")
print(df.head(3).to_string())

print(f"\n📊 Valeurs manquantes :")
missing = df.isnull().sum()
print(missing[missing > 0])

print(f"\n📊 Statistiques :")
print(df.describe())