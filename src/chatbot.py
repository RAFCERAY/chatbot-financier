"""
=============================================================
CHATBOT FINANCIER — Société Générale Datathon
=============================================================
Assistant Gen AI pour analyser les données BIS
=============================================================
"""
import pandas as pd
import os
import requests
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

def charger_donnees():
    df = pd.read_csv(os.path.join(DATA_DIR, "alteryx.csv"), low_memory=False)
    annees = ['2013', '2016', '2019', '2022']
    cols_meta = ['Instrument', 'Risk category', 'Reporting country',
                 'Currency leg 1', 'Currency leg 2', 'Maturity',
                 'Execution method', 'Basis']
    df = df[df['Instrument'] != 'Total (all instruments)'].copy()
    df_long = df.melt(
        id_vars=cols_meta,
        value_vars=annees,
        var_name='annee',
        value_name='volume_milliards'
    )
    df_long['annee'] = df_long['annee'].astype(int)
    df_long = df_long.dropna(subset=['volume_milliards'])
    return df_long

def construire_contexte(df):
    stats = df.groupby(['Instrument', 'annee'])['volume_milliards'].sum().round(2)
    top_pays = df.groupby('Reporting country')['volume_milliards'].sum().nlargest(5)
    top_devises = df.groupby('Currency leg 1')['volume_milliards'].sum().nlargest(5)

    contexte = f"""
Tu es un assistant financier expert specialise dans les marches de derives financiers.
Tu analyses les donnees BIS (Bank for International Settlements) sur les derives OTC.

DONNEES DISPONIBLES (2013-2022) :
- {df.shape[0]:,} observations
- Instruments : {', '.join(df['Instrument'].unique()[:8])}
- Pays : {', '.join(df['Reporting country'].unique()[:5])}

VOLUMES PAR INSTRUMENT ET ANNEE (milliards $) :
{stats.to_string()}

TOP 5 PAYS :
{top_pays.to_string()}

TOP 5 DEVISES :
{top_devises.to_string()}

Reponds en francais, de facon precise et professionnelle.
Cite toujours les chiffres specifiques quand tu reponds.
"""
    return contexte

def interroger_chatbot(contexte, question, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": contexte},
            {"role": "user", "content": question}
        ],
        "max_tokens": 500
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Erreur API : {response.status_code}"

def main():
    print("="*55)
    print("CHATBOT FINANCIER — Societe Generale Datathon")
    print("="*55)

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("Mode demonstration — sans cle API")
        api_key = None

    print("Chargement des donnees...")
    df = charger_donnees()
    print(f"OK {df.shape[0]:,} observations chargees")

    contexte = construire_contexte(df)

    questions_demo = [
        "Quel instrument a le plus grand volume en 2022 ?",
        "Comment a evolue le volume des FX swaps entre 2013 et 2022 ?",
        "Quels sont les 3 pays qui reportent le plus de volume ?",
    ]

    print("\n" + "="*55)
    print("QUESTIONS DE DEMONSTRATION")
    print("="*55)

    for q in questions_demo:
        print(f"\nQuestion : {q}")
        if api_key:
            reponse = interroger_chatbot(contexte, q, api_key)
            print(f"Reponse  : {reponse}")
        else:
            if "evolue" in q.lower() or "FX" in q:
                fx = df[df['Instrument'] == 'FX swaps'].groupby('annee')['volume_milliards'].sum()
                print(f"Reponse  : Evolution FX swaps :")
                for annee, vol in fx.items():
                    print(f"   {annee} : {vol:,.2f} milliards $")
            elif "2022" in q:
                top = df[df['annee'] == 2022].groupby('Instrument')['volume_milliards'].sum().nlargest(1)
                print(
                    f"Reponse  : L'instrument dominant en 2022 est {top.index[0]} avec {top.values[0]:,.2f} milliards $")
            elif "pays" in q.lower():
                top_pays = df.groupby('Reporting country')['volume_milliards'].sum().nlargest(3)
                print(f"Reponse  : Top 3 pays :")
                for pays, vol in top_pays.items():
                    print(f"   {pays} : {vol:,.2f} milliards $")

    print("\n" + "="*55)
    print("Chatbot pret ! Ajoutez votre cle API dans .env")
    print("pour activer les reponses Gen AI completes.")
    print("="*55)

if __name__ == "__main__":
    main()