import streamlit as st
import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from datetime import datetime, timedelta

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Cyber-Watch Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Chargement des variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'), 
    'database': os.getenv('DB_NAME')
}

# --- FONCTION CHARGEMENT (CACHE) ---
@st.cache_data(ttl=600)
def load_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = "SELECT date, source, titre, lien FROM articles ORDER BY date DESC LIMIT 2000"
        df = pd.read_sql(query, conn)
        conn.close()
        # Conversion forcée en datetime pour les filtres
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        return None

# --- HEADER ---
st.title("🛡️ Cyber-Watch : Tableau de Bord")
st.markdown("""
<style>
    .big-font { font-size:18px !important; color: #6c757d; }
</style>
<p class="big-font">Outil de pilotage de veille technologique et cybersécurité.</p>
""", unsafe_allow_html=True)

st.divider()

# --- CHARGEMENT ---
df = load_data()

if df is None:
    st.error("❌ Erreur de connexion BDD.")
    st.stop()
if df.empty:
    st.warning("⚠️ Base de données vide.")
    st.stop()

# ==========================================
#      SIDEBAR (ÉPURÉE)
# ==========================================

st.sidebar.header("🔍 Configuration")

# 1. FILTRE TEMPOREL
st.sidebar.subheader("Période")
days_back = st.sidebar.slider("Historique (Jours)", min_value=1, max_value=365, value=90)
min_date = datetime.now() - timedelta(days=days_back)

st.sidebar.markdown("---")

# 2. FILTRES DE RECHERCHE
st.sidebar.subheader("Filtres")
search_query = st.sidebar.text_input("Mots-clés (Titre)", placeholder="Ex: Ransomware...")
all_sources = sorted(df['source'].unique())
selected_sources = st.sidebar.multiselect("Sources", all_sources)

# APPLICATION DES FILTRES
filtered_df = df.copy()

# Filtre Date
filtered_df = filtered_df[filtered_df['date'] >= min_date]

# Filtre Source
if selected_sources:
    filtered_df = filtered_df[filtered_df['source'].isin(selected_sources)]

# Filtre Texte
if search_query:
    filtered_df = filtered_df[filtered_df['titre'].str.contains(search_query, case=False)]

st.sidebar.markdown("---")

# 3. EXPORT DATA
st.sidebar.subheader("Export")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="📥 Télécharger (.csv)",
    data=csv,
    file_name='cyber_watch_export.csv',
    mime='text/csv',
)

# ==========================================
#           FIN SIDEBAR
# ==========================================


# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total Articles", len(filtered_df))
with col2: st.metric("Source Top Activité", filtered_df['source'].mode()[0] if not filtered_df.empty else "N/A")
with col3: st.metric("Dernière M.A.J", str(filtered_df['date'].max().date()) if not filtered_df.empty else "N/A")
with col4: st.metric("Pertinence", f"{(len(filtered_df)/len(df)*100):.1f}%")

st.markdown("---")

# --- VISUALISATION ---
col_cloud, col_chart = st.columns([1, 1])

with col_cloud:
    st.subheader("☁️ Tendances (Mots-clés)")
    if not filtered_df.empty:
        text = " ".join(title for title in filtered_df.titre)
        
        stopwords = {
            "le", "la", "les", "des", "du", "en", "un", "une", "pour", "sur", "avec", "par", 
            "dans", "et", "ou", "a", "est", "son", "sa", "ses", "qui", "que", "aux", "ne", 
            "se", "ce", "cette", "être", "avoir", "de", "c", "d", "il", "elle", "ils", "elles",
            "nous", "vous", "leur", "y", "en", "vers", "sans", "sous", "près", "chez", "tout",
            "tous", "toute", "toutes", "plus", "moins", "très", "bien", "fait", "faire", "comme",
            "aussi", "mais", "donc", "or", "ni", "car", "si", "quand", "où", "dont", "celui",
            "celle", "cela", "ça", "ceux", "nouveau", "nouvelle", "depuis", "votre", "notre",
            "entre", "après", "avant", "contre", "déjà", "encore", "faut", "peut", "veut",
            "dire", "dit", "voir", "pendant", "fois", "leurs", "quoi", "quel", "quelle",
            "comment", "pourquoi", "jamais", "toujours", "lors", "vers", "via", "ces", "cet",
            "ici", "là", "non", "oui", "alors", "ainsi", "telle", "tel", "tels", "telles",
            "sont", "ont", "va", "van", "aux", "leurs", "leur", "mes", "tes", "ses", "nos", "vos"
        }
        
        wordcloud = WordCloud(
            width=800, height=350,
            background_color='#0e1117', 
            stopwords=stopwords,
            min_word_length=3,
            max_words=60,
            colormap="ocean",
            random_state=42
        ).generate(text)
        
        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        fig.patch.set_facecolor('#0e1117')
        st.pyplot(fig, use_container_width=True)
    else:
        st.info("Pas assez de données.")

with col_chart:
    st.subheader("📊 Volume par Source")
    if not filtered_df.empty:
        st.bar_chart(filtered_df['source'].value_counts().head(10), color="#00aa00")
    else:
        st.info("Aucune donnée.")

# --- TABLEAU ---
st.subheader("📰 Fil d'Actualité")
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