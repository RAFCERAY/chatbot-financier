"""
=============================================================
FIN.BOT SG — Interface Streamlit
=============================================================
Assistant Financier Gen AI — Datathon Société Générale
=============================================================
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import requests
import json

# ─── Configuration page ───────────────────────────────────
st.set_page_config(
    page_title="Fin.Bot SG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Style CSS ────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1C2951, #0D1B2A);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #E30613;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .chat-message {
        padding: 10px 15px;
        border-radius: 8px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

# ─── Chargement données ───────────────────────────────────
@st.cache_data
def charger_donnees():
    df = pd.read_csv(os.path.join(DATA_DIR, "alteryx.csv"), low_memory=False)
    annees = ['2013', '2016', '2019', '2022']
    cols_meta = ['Instrument', 'Risk category', 'Reporting country',
                 'Currency leg 1', 'Currency leg 2', 'Maturity']
    df = df[df['Instrument'] != 'Total (all instruments)'].copy()
    df_long = df.melt(id_vars=cols_meta, value_vars=annees,
                      var_name='annee', value_name='volume')
    df_long['annee'] = df_long['annee'].astype(int)
    df_long = df_long.dropna(subset=['volume'])
    return df_long

# ─── Réponse sans API ─────────────────────────────────────
def repondre_sans_api(question, df):
    q = question.lower()

    if "fx swap" in q or "swap" in q:
        fx = df[df['Instrument']=='FX swaps'].groupby('annee')['volume'].sum()
        croissance = ((fx[2022]-fx[2013])/fx[2013]*100).round(1)
        return f"""📊 **FX Swaps — Evolution 2013-2022**

| Année | Volume (milliards $) |
|-------|---------------------|
| 2013  | {fx[2013]/1e6:,.0f} |
| 2016  | {fx[2016]/1e6:,.0f} |
| 2019  | {fx[2019]/1e6:,.0f} |
| 2022  | {fx[2022]/1e6:,.0f} |

📈 **Croissance : +{croissance}% entre 2013 et 2022**

Les FX swaps représentent l'instrument dominant du marché OTC, 
reflétant l'internationalisation croissante des échanges financiers."""

    elif "pays" in q or "country" in q or "royaume" in q or "uk" in q:
        top = df[
            (df['annee']==2022) &
            (~df['Reporting country'].str.contains('total|all', case=False, na=False))
        ].groupby('Reporting country')['volume'].sum().nlargest(5)
        result = "📊 **Top 5 pays — Volume OTC 2022**\n\n"
        for pays, vol in top.items():
            result += f"- **{pays}** : {vol/1e6:,.0f} milliards $\n"
        result += "\n🇬🇧 Le Royaume-Uni reste la 1ère place financière mondiale."
        return result

    elif "instrument" in q or "2022" in q:
        top = df[df['annee']==2022].groupby('Instrument')['volume'].sum().nlargest(5)
        result = "📊 **Top 5 instruments — Volume OTC 2022**\n\n"
        for instr, vol in top.items():
            result += f"- **{instr}** : {vol/1e6:,.0f} milliards $\n"
        return result

    elif "devise" in q or "currency" in q or "paire" in q:
        df['paire'] = df['Currency leg 1'] + '/' + df['Currency leg 2']
        top = df[
            (df['annee']==2022) &
            (~df['Currency leg 1'].str.contains('total|all', case=False, na=False))
        ].groupby('paire')['volume'].sum().nlargest(5)
        result = "📊 **Top 5 paires de devises — 2022**\n\n"
        for paire, vol in top.items():
            result += f"- **{paire}** : {vol/1e6:,.0f} milliards $\n"
        return result

    elif "croissance" in q or "evolution" in q or "tendance" in q:
        vol = df.groupby('annee')['volume'].sum()
        result = "📊 **Evolution du marché OTC 2013-2022**\n\n"
        for annee, v in vol.items():
            result += f"- **{annee}** : {v/1e9:,.1f} milliers de milliards $\n"
        croissance = ((vol[2022]-vol[2013])/vol[2013]*100).round(1)
        result += f"\n📈 **Croissance totale : +{croissance}%**"
        return result

    else:
        return """🤖 Je peux répondre à des questions sur :

- **FX swaps** — evolution et volumes
- **Instruments financiers** — classement 2022
- **Pays** — top marchés mondiaux
- **Paires de devises** — volumes échangés
- **Croissance** — tendances 2013-2022

Essayez : *"Quel est le volume des FX swaps ?"*"""

# ─── Appel API OpenAI ─────────────────────────────────────
def interroger_openai(question, df, api_key):
    fx = df[df['Instrument']=='FX swaps'].groupby('annee')['volume'].sum()
    top_pays = df[(df['annee']==2022) &
                  (~df['Reporting country'].str.contains('total|all', case=False, na=False))
                 ].groupby('Reporting country')['volume'].sum().nlargest(5)

    contexte = f"""Tu es Fin.Bot SG, un assistant financier expert de Société Générale.
Tu analyses les données BIS sur les dérivés OTC 2013-2022.

DONNÉES CLÉS :
- FX swaps 2022 : {fx[2022]/1e6:,.0f} milliards $
- Croissance FX swaps : +{((fx[2022]-fx[2013])/fx[2013]*100).round(1)}%
- Top pays : {', '.join(top_pays.index[:3].tolist())}

Réponds en français, de façon professionnelle avec des chiffres précis."""

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": contexte},
            {"role": "user", "content": question}
        ],
        "max_tokens": 400
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return repondre_sans_api(question, df)

# ─── INTERFACE ────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <h1 style="color:white; margin:0;">🤖 Fin.Bot SG</h1>
    <p style="color:#CADCFC; margin:5px 0 0 0;">Assistant Financier Gen AI — Données BIS OTC 2013-2022</p>
</div>
""", unsafe_allow_html=True)

# Chargement données
df = charger_donnees()

# ─── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Soci%C3%A9t%C3%A9_G%C3%A9n%C3%A9rale.svg/200px-Soci%C3%A9t%C3%A9_G%C3%A9n%C3%A9rale.svg.png", width=150)
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input("Clé API OpenAI (optionnel)", type="password",
                             help="Sans clé API, le chatbot fonctionne en mode démonstration")
    st.markdown("---")
    st.markdown("### 📊 Filtres")
    annee_select = st.selectbox("Année d'analyse", [2022, 2019, 2016, 2013])
    instrument_select = st.multiselect(
        "Instruments",
        options=df['Instrument'].unique().tolist(),
        default=['FX swaps', 'Outright forwards', 'Options']
    )
    st.markdown("---")
    st.markdown("### 💡 Questions rapides")
    if st.button("📈 Evolution FX swaps"):
        st.session_state.question_rapide = "Comment a évolué le volume des FX swaps ?"
    if st.button("🌍 Top pays 2022"):
        st.session_state.question_rapide = "Quels sont les pays avec le plus grand volume ?"
    if st.button("🏆 Top instruments"):
        st.session_state.question_rapide = "Quel instrument a le plus grand volume en 2022 ?"
    if st.button("💱 Top paires devises"):
        st.session_state.question_rapide = "Quelles sont les paires de devises dominantes ?"

# ─── KPIs ─────────────────────────────────────────────────
fx = df[df['Instrument']=='FX swaps'].groupby('annee')['volume'].sum()
total_2022 = df[df['annee']==2022]['volume'].sum()
croissance = ((fx[2022]-fx[2013])/fx[2013]*100).round(1)
n_pays = df[df['annee']==2022]['Reporting country'].nunique()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Volume FX swaps 2022", f"{fx[2022]/1e6:,.0f} Mds $", f"+{croissance}% vs 2013")
with col2:
    st.metric("Volume total OTC 2022", f"{total_2022/1e9:,.1f} K Mds $")
with col3:
    st.metric("Part FX swaps", f"{fx[2022]/total_2022*100:.1f}%", "du marché total")
with col4:
    st.metric("Pays reportants", f"{n_pays}", "places financières")

st.markdown("---")

# ─── Tabs ─────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["💬 Chatbot", "📊 Visualisations", "📋 Rapport Auto"])

# ── Tab 1 — Chatbot ───────────────────────────────────────
with tab1:
    st.markdown("### 💬 Posez votre question financière")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Bonjour ! Je suis Fin.Bot SG 🤖\n\nJe peux analyser les données BIS sur les dérivés OTC 2013-2022.\nPosez-moi une question sur les volumes, instruments, pays ou devises !"}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Posez votre question...")

    if "question_rapide" in st.session_state:
        question = st.session_state.question_rapide
        del st.session_state.question_rapide

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyse en cours..."):
                if api_key:
                    reponse = interroger_openai(question, df, api_key)
                else:
                    reponse = repondre_sans_api(question, df)
            st.markdown(reponse)
            st.session_state.messages.append({"role": "assistant", "content": reponse})

# ── Tab 2 — Visualisations ────────────────────────────────
with tab2:
    st.markdown("### 📊 Tableaux de bord interactifs")

    col1, col2 = st.columns(2)

    with col1:
        # Evolution par instrument
        df_instr = df[df['Instrument'].isin(instrument_select)]
        pivot = df_instr.groupby(['annee', 'Instrument'])['volume'].sum().reset_index()
        fig = px.line(pivot, x='annee', y='volume', color='Instrument',
                      title='Evolution des volumes par instrument',
                      labels={'volume': 'Volume (milliards $)', 'annee': 'Année'},
                      markers=True)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top pays sélectionné
        df_pays = df[
            (df['annee']==annee_select) &
            (~df['Reporting country'].str.contains('total|all', case=False, na=False))
        ].groupby('Reporting country')['volume'].sum().nlargest(10).reset_index()
        fig2 = px.bar(df_pays, x='volume', y='Reporting country',
                      orientation='h',
                      title=f'Top 10 pays — {annee_select}',
                      labels={'volume': 'Volume (milliards $)'},
                      color='volume', color_continuous_scale='Blues')
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    # Breakdown risque
    df_risk = df[
        ~df['Risk category'].str.contains('total|all', case=False, na=False)
    ].groupby(['annee', 'Risk category'])['volume'].sum().reset_index()
    fig3 = px.bar(df_risk, x='annee', y='volume', color='Risk category',
                  title='Répartition par catégorie de risque (2013-2022)',
                  labels={'volume': 'Volume (milliards $)', 'annee': 'Année'},
                  barmode='stack')
    fig3.update_layout(height=350)
    st.plotly_chart(fig3, use_container_width=True)

# ── Tab 3 — Rapport Auto ──────────────────────────────────
with tab3:
    st.markdown("### 📋 Rapport automatique")

    if st.button("🔄 Générer le rapport", type="primary"):
        with st.spinner("Génération en cours..."):
            vol_annee = df.groupby('annee')['volume'].sum()
            top_instr = df[df['annee']==2022].groupby('Instrument')['volume'].sum().nlargest(3)
            top_pays = df[
                (df['annee']==2022) &
                (~df['Reporting country'].str.contains('total|all', case=False, na=False))
            ].groupby('Reporting country')['volume'].sum().nlargest(3)

            rapport = f"""
# Rapport — Marché des Dérivés OTC
**Date :** Mars 2026 | **Source :** BIS

## KPIs clés
- Volume total 2022 : **{total_2022/1e9:,.1f} milliers de milliards $**
- Croissance FX swaps : **+{croissance}%** (2013-2022)
- Part FX swaps : **{fx[2022]/total_2022*100:.1f}%** du marché

## Top 3 instruments 2022
"""
            for instr, vol in top_instr.items():
                rapport += f"- **{instr}** : {vol/1e6:,.0f} Mds $\n"

            rapport += "\n## Top 3 pays 2022\n"
            for pays, vol in top_pays.items():
                rapport += f"- **{pays}** : {vol/1e6:,.0f} Mds $\n"

            rapport += f"""
## Conclusions
- FX swaps : instrument stratégique avec **+{croissance}%** de croissance
- UK : 1ère place financière mondiale
- Croissance soutenue post-Covid en 2022
"""
            st.markdown(rapport)
            st.download_button(
                "⬇️ Télécharger le rapport",
                rapport,
                file_name="rapport_derives_OTC.md",
                mime="text/markdown"
            )