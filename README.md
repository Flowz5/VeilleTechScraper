
# 🛡️ Cyber-Watch : Veille Technologique Automatisée

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

**Cyber-Watch** est une solution complète de veille technologique. Elle automatise la collecte d'articles (Cyber, Dev, Infra), les stocke, et offre deux interfaces de consultation : un terminal interactif pour les experts et un **Dashboard Web** pour l'analyse visuelle.

## 📁 Structure du Projet

L'architecture respecte les standards de développement professionnel :

* `scraper.py` : **Collecteur (Backend)**. Récupère les flux RSS, gère le tri (manuel/auto) et l'insertion en BDD avec logs.
* `dashboard.py` : **Interface Web (Frontend)**. Tableau de bord Business Intelligence (BI) développé avec **Streamlit** pour visualiser les données.
* `recherche.py` : **Interface CLI**. Moteur de recherche rapide dans le terminal avec affichage enrichi (`Rich`).
* `requirements.txt` : Liste des dépendances (`streamlit`, `rich`, `mysql-connector`, `pandas`).
* `.env` : Configuration sécurisée des identifiants (non versionné).

## 🚀 Fonctionnalités Clés

### 1. Collecte Intelligente (`scraper.py`)
* **Multi-Sources** : Agrégation centralisée (ANSSI, Zataz, Developpez, GitHub Blog, IT Connect...).
* **Robustesse** : Gestion des erreurs réseaux, logs détaillés (`journal.log`), et anti-doublons SQL.
* **Mode Hybride** : Interactif (choix manuel) ou Automatique (Cron).

### 2. Business Intelligence & Data Viz (`dashboard.py`)
* **Visualisation** : Graphiques dynamiques des volumes par source.
* **KPIs** : Indicateurs clés (Nombre d'articles, Source la plus active, Pertinence).
* **Filtres Temps Réel** : Tri par source, recherche textuelle instantanée.
* **Interface Web** : Accessible via navigateur, responsive et moderne (Mode sombre supporté).

### 3. Consultation Rapide (`recherche.py`)
* **Moteur SQL** : Recherche par pertinence (Algorithme de scoring simple).
* **CLI Moderne** : Tableaux formatés et ouverture des liens au clavier.

## 🛠️ Installation

### 1. Préparation
```bash
git clone [https://github.com/Flowz5/VeilleTechScraper.git](https://github.com/Flowz5/VeilleTechScraper.git)
cd VeilleTechScraper

# Création et activation de l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate # Windows

# Installation des dépendances
pip install -r requirements.txt

```

### 2. Base de données

Assurez-vous d'avoir un serveur MySQL local. Créez la base et importez la structure (table `articles`).

### 3. Configuration

Créez un fichier `.env` à la racine :

```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_NAME=veille_tech

```

## 🖥️ Utilisation

### 📥 Lancer une collecte

```bash
python scraper.py

```

### 📊 Ouvrir le Dashboard Web

```bash
streamlit run dashboard.py

```

*Le tableau de bord s'ouvrira automatiquement dans votre navigateur (http://localhost:8501).*

### 🔍 Recherche Rapide (Terminal)

```bash
python recherche.py

```

## 🐧 Intégration Linux (Hyprland / Bash)

Ajoutez ces alias dans votre `.bashrc` pour un accès ultra-rapide :

```bash
alias veille="cd ~/Projets/VeilleTechScraper && source venv/bin/activate && python scraper.py"
alias dash="cd ~/Projets/VeilleTechScraper && source venv/bin/activate && streamlit run dashboard.py"

```
