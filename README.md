
# 🛡️ Cyber-Watch : Veille Technologique & Cyber-Intelligence

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Container-blue?style=for-the-badge&logo=docker&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-Automation-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

**Cyber-Watch** est une plateforme de veille technologique automatisée et conteneurisée, orientée Cybersécurité et DevOps.

Au-delà de l'agrégation RSS, le projet intègre un pipeline **ETL** (Extract, Transform, Load) complet : collecte Python, stockage SQL, analyse sémantique (Scoring) et **orchestration d'alertes en temps réel via n8n et Discord**.

---

## 🚀 Architecture Technique

Le système repose sur 4 piliers interconnectés :

1.  **Collecte (Python)** : Scraper multi-threadé qui interroge ~20 sources (ANSSI, BleepingComputer, etc.).
2.  **Intelligence (Algo)** : Moteur de scoring qui détecte les mots-clés critiques (*Ransomware, CVE, 0-Day*).
3.  **Stockage (MySQL)** : Base de données relationnelle avec gestion d'unicité.
4.  **Notification (Docker + n8n)** : Envoi automatique d'alertes formatées sur Discord pour les menaces critiques (Score ≥ 4).

---

## ⚙️ Fonctionnalités Clés

### 1. Collecte & Filtrage (`scraper.py`)
* **Hybride** : Gestion des flux RSS et parsing HTML (BeautifulSoup).
* **Robustesse** : Contournement des protections (User-Agents, SSL) pour les sites gouvernementaux.
* **Déduplication** : Vérification en base avant insertion.

### 2. Moteur de Pertinence (Scoring)
Chaque article reçoit un score de **0 à 10** selon sa criticité :
* 🔴 **Critique (+3 pts)** : *Ransomware, 0-day, Breach, CVE, Faille...* -> **Déclenche une alerte Discord**.
* 🟠 **Important (+2 pts)** : *ANSSI, GDPR, Python, Docker...*
* 🔵 **Contexte (+1 pt)** : *Windows, Update, Web, Tech...*

### 3. Automatisation & Alerting (`n8n`)
Un conteneur Docker **n8n** écoute les webhooks envoyés par le script Python.
* Réception des données (Titre, Source, Lien, Score).
* Formatage du message (Rich text).
* Dispatch vers un channel Discord dédié à la veille.

### 4. Dashboard BI (`dashboard.py`)
Interface Streamlit pour la consultation à froid :
* Fil d'actualité priorisé par score.
* Nuage de mots-clés dynamique (WordCloud).
* Statistiques sur les sources les plus actives.

---

## 📁 Structure du Projet

```bash
VeilleTechScraper/
├── scraper.py           # Backend : Collecte, Scoring, Webhook vers n8n
├── dashboard.py         # Frontend : Interface Streamlit & Dataviz
├── n8n_automation.json  # Workflow d'automatisation (Import n8n)
├── requirements.txt     # Dépendances Python
├── .env                 # Secrets (DB, etc.)
└── README.md            # Documentation

```

---

## 🛠️ Installation & Démarrage

### 1. Prérequis

* Python 3.10+
* Docker & Docker Compose
* Serveur MySQL

### 2. Installation Python & BDD

```bash
git clone [https://github.com/Flowz5/VeilleTechScraper.git](https://github.com/Flowz5/VeilleTechScraper.git)
cd VeilleTechScraper

# Environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Dépendances
pip install -r requirements.txt

```

Créez un fichier `.env` à la racine :

```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_NAME=veille_tech
# (L'URL n8n est configurée dans le script scraper.py)

```

### 3. Mise en place de l'Automatisation (n8n)

Lancer le conteneur n8n (avec persistance des données) :

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n:Z \
  --restart always \
  docker.n8n.io/n8nio/n8n

```

**Configuration du Workflow :**

1. Accéder à `http://localhost:5678`.
2. Cliquer sur **"Add workflow"** > **"Import from..."** > **"File"**.
3. Sélectionner le fichier `n8n_automation.json` présent dans ce dépôt.
4. Double-cliquer sur le nœud **Discord**.
5. Dans "Credential", créez un nouveau "Discord Webhook account" et collez **votre propre URL de Webhook Discord**.
6. **Activez** le workflow (Bouton en haut à droite).

### 4. Utilisation

**Mode Manuel :**

```bash
python scraper.py        # Récupère les articles et alerte si critique
streamlit run dashboard.py # Lance l'interface visuelle

```

**Mode Automatique (Cron) :**
Ajouter au crontab pour une exécution tous les matins à 8h00 :

```bash
0 8 * * * /chemin/vers/venv/bin/python /chemin/vers/scraper.py >> /chemin/vers/cron.log 2>&1

```

---

## 🐧 Intégration Linux (Alias)

Pour les utilisateurs avancés (Hyprland / Bash / Zsh) :

```bash
alias cyberwatch="cd ~/Projets/VeilleTechScraper && source venv/bin/activate && streamlit run dashboard.py"
alias cyberscrape="cd ~/Projets/VeilleTechScraper && source venv/bin/activate && python scraper.py"

```
