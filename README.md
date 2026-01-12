
# 🛡️ Cyber-Watch : Veille Technologique & Cyber-Intelligence

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Scraping](https://img.shields.io/badge/BeautifulSoup-Scraping-green?style=for-the-badge)

**Cyber-Watch** est une plateforme de veille technologique automatisée orientée Cybersécurité et DevOps. 
Plus qu'un simple agrégateur RSS, elle intègre un **moteur d'analyse sémantique** capable de scorer les articles selon leur criticité (Ransomware, 0-Day, Failles) pour prioriser la lecture des experts.

---

## 🚀 Pourquoi ce projet ?

Dans le flux continu d'informations technologiques, le défi n'est plus de trouver l'information, mais de **filtrer le bruit**. 
Cyber-Watch répond à ce besoin via :
1.  **Centralisation** : Sources Françaises (ANSSI, Zataz) et Internationales (The Hacker News, BleepingComputer).
2.  **Qualification** : Algorithme de pondération par mots-clés.
3.  **Visualisation** : Dashboard BI pour piloter la veille.

---

## ⚙️ Fonctionnalités Clés

### 1. Collecte Intelligente (`scraper.py`)
* **Multi-Sources & Hybride** : Scrape ~20 flux RSS majeurs (Cyber, Dev, Cloud).
* **Contournement de Protections** : Gestion des *User-Agents* et certificats SSL pour les sites gouvernementaux/protégés.
* **Nettoyage** : Déduplication automatique via SQL pour éviter les doublons.

### 2. Moteur de Pertinence (Scoring)
L'application analyse chaque titre d'article et attribue un score de **0 à 10** selon des poids définis :
* 🔴 **Critique (+3 pts)** : *Ransomware, 0-day, Breach, CVE, Faille...*
* 🟠 **Important (+2 pts)** : *ANSSI, GDPR, Python, Docker, Cyber...*
* 🔵 **Contexte (+1 pt)** : *Windows, Update, Web, Tech...*

### 3. Dashboard Business Intelligence (`dashboard.py`)
* **Fil d'actualité Priorisé** : Les articles critiques remontent automatiquement en haut de liste avec une barre de progression visuelle.
* **Analyse de Tendances** : Nuage de mots-clés (WordCloud) généré dynamiquement (Stopwords FR/EN filtrés).
* **KPIs Temps Réel** : Volume d'articles, sources les plus actives, nombre d'alertes "Hot" 🔥.
* **Filtres Avancés** : Recherche textuelle instantanée, filtrage par source et date.

---

## 📁 Structure du Projet

```bash
VeilleTechScraper/
├── scraper.py       # Backend : Collecte, Parsing XML, Insertion BDD
├── dashboard.py     # Frontend : Interface Streamlit, Algo de Scoring, Dataviz
├── recherche.py     # CLI : Interface terminal rapide (Rich)
├── requirements.txt # Dépendances
├── .env             # Variables d'environnement (Non versionné)
└── README.md        # Documentation

```

---

## 🛠️ Installation & Démarrage

### 1. Prérequis

* Python 3.10+
* Serveur MySQL (Local ou Distant)

### 2. Installation

```bash
git clone [https://github.com/Flowz5/VeilleTechScraper.git](https://github.com/Flowz5/VeilleTechScraper.git)
cd VeilleTechScraper

# Environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate # Windows

# Dépendances
pip install -r requirements.txt

```

### 3. Configuration (.env)

Créez un fichier `.env` à la racine :

```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_NAME=veille_tech

```

### 4. Lancer l'application

**Étape 1 : Récupérer les articles**

```bash
python scraper.py

```

**Étape 2 : Lancer le Dashboard**

```bash
streamlit run dashboard.py

```

*Le navigateur s'ouvrira automatiquement sur http://localhost:8501*

---

## 🐧 Intégration Linux (Hyprland / Bash)

Pour les utilisateurs avancés, ajoutez ces alias dans votre `.bashrc` ou `.zshrc` pour lancer votre veille en une commande :

```bash
alias cyberwatch="cd ~/Chemin/Vers/VeilleTechScraper && source venv/bin/activate && streamlit run dashboard.py"
alias cyberscrape="cd ~/Chemin/Vers/VeilleTechScraper && source venv/bin/activate && python scraper.py"

```
