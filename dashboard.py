import streamlit as st
import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from datetime import datetime, timedelta

# --- CONFIGURATION UTILISATEUR ---
# Liste des mots qui t'intéressent. Plus un article en contient, plus il sera bien noté.
# --- CONFIGURATION AVANCÉE (POIDS) ---
# Format : "mot_clé": score (1=Normal, 2=Important, 3=Critique)
MES_MOTS_CLES = {
    # 🔴 CRITIQUE (Menaces & Urgences)
    "ransomware": 3, "0-day": 3, "zero-day": 3, "faille": 3, "vulnerabilité": 3,
    "cve": 3, "breach": 3, "fuite": 3, "piratage": 3, "hacked": 3, "exploit": 3,
    "rce": 3, "critique": 3, "urgence": 3, "alert": 3,

    # 🟠 IMPORTANT (Cyber & Outils majeurs)
    "cyber": 2, "sécurité": 2, "security": 2, "anssi": 2, "malware": 2,
    "phishing": 2, "ddos": 2, "rootkit": 2, "spyware": 2, "botnet": 2,
    "gdpr": 2, "rgpd": 2, "cnil": 2, "cert": 2, "soc": 2, "siem": 2,
    "docker": 2, "kubernetes": 2, "linux": 2, "python": 2, "ai": 2, "ia": 2,
    "chatgpt": 2, "gpt": 2, "openai": 2,

    # 🔵 NORMAL (Tech & Langages)
    "windows": 1, "microsoft": 1, "apple": 1, "google": 1, "aws": 1, "azure": 1,
    "cloud": 1, "server": 1, "data": 1, "javascript": 1, "react": 1, "node": 1,
    "php": 1, "java": 1, "c#": 1, "c++": 1, "rust": 1, "go": 1, "sql": 1,
    "api": 1, "rest": 1, "web": 1, "dev": 1, "code": 1, "github": 1, "gitlab": 1
}

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

def calculer_score(titre):
    """Calcule le score en fonction des poids définis"""
    if not isinstance(titre, str): return 0
    score = 0
    titre_min = titre.lower()
    
    # On parcourt notre dictionnaire (mot, poids)
    for mot, poids in MES_MOTS_CLES.items():
        if mot in titre_min:
            score += poids
            
    return score

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

# --- APPLICATION DES FILTRES ---
filtered_df = df.copy()

# 1. Filtre Date
filtered_df = filtered_df[filtered_df['date'] >= min_date]

# 2. Filtre Source
if selected_sources:
    filtered_df = filtered_df[filtered_df['source'].isin(selected_sources)]

# 3. Filtre Recherche Texte (Barre de recherche)
if search_query:
    filtered_df = filtered_df[filtered_df['titre'].str.contains(search_query, case=False)]

# --- CALCUL DE LA PERTINENCE (NOUVEAU) ---
# On applique la notation sur chaque ligne
filtered_df['score'] = filtered_df['titre'].apply(calculer_score)

# On trie : Les meilleurs scores en haut, puis par date récente
filtered_df = filtered_df.sort_values(by=['score', 'date'], ascending=[False, False])

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
nb_articles_hot = len(filtered_df[filtered_df['score'] > 0]) # Nombre d'articles ayant au moins 1 mot-clé

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total Articles", len(filtered_df))
with col2: st.metric("Source Top Activité", filtered_df['source'].mode()[0] if not filtered_df.empty else "N/A")
with col3: st.metric("Dernière M.A.J", str(filtered_df['date'].max().date()) if not filtered_df.empty else "N/A")
# Ici, on affiche le nombre d'articles "Pertinents" (qui matchent tes mots-clés)
with col4: st.metric("Articles Pertinents 🔥", f"{nb_articles_hot}") 

st.markdown("---")

# --- VISUALISATION ---
col_cloud, col_chart = st.columns([1, 1])

with col_cloud:
    st.subheader("☁️ Tendances (Mots-clés)")
    if not filtered_df.empty:
        text = " ".join(title for title in filtered_df.titre)
        
        # TA LISTE DE STOPWORDS (Je te laisse la tienne, elle était très bien)
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
            "sont", "ont", "va", "van", "aux", "leurs", "leur", "mes", "tes", "ses", "nos", "vos",
            "été", "étée", "étées", "ayant", "suis", "es", "sommes", "êtes", "font", "vont",
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", 
            "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", 
            "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", "all", "would", 
            "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which", 
            "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know", 
            "take", "people", "into", "year", "your", "good", "some", "could", "them", "see", 
            "other", "than", "then", "now", "look", "only", "come", "its", "over", "think", 
            "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", 
            "way", "even", "new", "want", "because", "any", "these", "give", "day", "most", 
            "us", "is", "are", "was", "were", "has", "had", "been", "more", "very", "should",
            "news", "today", "using", "used", "does", "read", "click", "here",
            "http", "https", "www", "com", "fr", "org", "net", "html", "php", 
            "cookies", "policy", "privacy", "rights", "reserved", "copyright", 
            "loading", "content", "skip", "main", "menu"
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

# On n'affiche pas la colonne "score" brute (c'est moche), on utilise ColumnConfig pour faire des étoiles
st.dataframe(
    filtered_df,
    column_config={
        "lien": st.column_config.LinkColumn("Lien", display_text="Lire l'article"),
        "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
        "titre": "Titre de l'article",
        "source": "Source",
        "score": st.column_config.ProgressColumn(
            "Intérêt",
            help="Score calculé selon la criticité des mots-clés",
            format="%d",
            min_value=0,
            max_value=10, # <-- Passe de 3 à 10 pour supporter les gros scores
        ),
    },
    hide_index=True,
    use_container_width=True,
    height=600 # Un peu plus grand pour bien voir
)