import streamlit as st
import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Cyber-Watch Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Chargement des variables d'environnement
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'), 
    'database': os.getenv('DB_NAME')
}

# --- FONCTION DE CHARGEMENT OPTIMISÉE (CACHE) ---
@st.cache_data(ttl=600)  # Mise en cache des données pour 10 minutes
def load_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # On récupère les 500 derniers articles pour l'analyse
        query = "SELECT date, source, titre, lien FROM articles ORDER BY date DESC LIMIT 5000"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return None

# --- HEADER & TITRE ---
st.title("🛡️ Cyber-Watch : Tableau de Bord")
st.markdown("""
<style>
    .big-font { font-size:18px !important; color: #6c757d; }
</style>
<p class="big-font">Outil de pilotage de veille technologique et cybersécurité.</p>
""", unsafe_allow_html=True)

st.divider()

# --- CHARGEMENT DES DONNÉES ---
df = load_data()

if df is None:
    st.error("❌ Erreur de connexion à la base de données. Vérifiez le fichier .env")
    st.stop()

if df.empty:
    st.warning("⚠️ La base de données est vide. Lancez 'scraper.py' d'abord.")
    st.stop()

# --- BARRE LATÉRALE (FILTRES) ---
st.sidebar.header("🔍 Filtres de Recherche")

# 1. Filtre par Source
all_sources = sorted(df['source'].unique())
selected_sources = st.sidebar.multiselect("Sélectionner les sources", all_sources)

# 2. Filtre par Mot-clé
search_query = st.sidebar.text_input("Rechercher dans les titres", placeholder="Ex: Ransomware, Python...")

# Application des filtres
filtered_df = df.copy()

if selected_sources:
    filtered_df = filtered_df[filtered_df['source'].isin(selected_sources)]

if search_query:
    filtered_df = filtered_df[filtered_df['titre'].str.contains(search_query, case=False)]

# --- INDICATEURS CLÉS (KPI) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Articles (Filtre)", value=len(filtered_df))

with col2:
    # Source la plus active dans la sélection
    top_source = filtered_df['source'].mode()[0] if not filtered_df.empty else "N/A"
    st.metric(label="Source Top Actvité", value=top_source)

with col3:
    last_date = filtered_df['date'].max() if not filtered_df.empty else "N/A"
    st.metric(label="Dernière M.A.J", value=str(last_date))

with col4:
    # Pourcentage par rapport au total global
    ratio = (len(filtered_df) / len(df)) * 100
    st.metric(label="Pertinence", value=f"{ratio:.1f}%")

st.markdown("---")

# --- GRAPHIQUES & VISUALISATION ---
col_charts, col_data = st.columns([1, 2])

with col_charts:
    st.subheader("📊 Volume par Source")
    if not filtered_df.empty:
        source_counts = filtered_df['source'].value_counts().head(10) # Top 10 seulement pour lisibilité
        st.bar_chart(source_counts, color="#00aa00") # Vert Matrix
    else:
        st.info("Aucune donnée pour ce filtre.")

with col_data:
    st.subheader("📰 Fil d'Actualité")
    
    # Configuration avancée du tableau
    st.dataframe(
        filtered_df,
        column_config={
            "lien": st.column_config.LinkColumn("Lien", display_text="Lire l'article"),
            "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
            "titre": "Titre de l'article",
            "source": "Source"
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )

# --- PIED DE PAGE ---
st.sidebar.markdown("---")
st.sidebar.caption("Développé par Léo Dupont • BTS SIO 2026")
if st.sidebar.button("🔄 Rafraîchir les données"):
    load_data.clear() # Vide le cache
    st.rerun()