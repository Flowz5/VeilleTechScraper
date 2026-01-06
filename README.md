Voici une version **complète et modernisée** de ton README. J'ai intégré les dernières nouveautés que nous avons développées ensemble (l'interface graphique avec `Rich`, le script de recherche `search.py`, et l'organisation par catégories).

C'est une version "prête à l'emploi" pour ton GitHub.

---

# 🛡️ Cyber-Watch : Veille Technologique Automatisée

**Cyber-Watch** est un outil complet de veille technologique développé en Python. Il permet d'automatiser la collecte d'articles depuis de multiples sources (Cyber, Dev, IA, Infra), de les archiver dans une base de données MySQL, et de les consulter via une interface terminal moderne et interactive.

## 📁 Structure du Projet

L'architecture respecte les standards de développement professionnel :

* `scraper.py` : **Collecteur**. Récupère les flux RSS, gère le tri (manuel/auto) et l'insertion en BDD.
* `search.py` : **Moteur de recherche**. Interface CLI pour requêter la base de données et ouvrir les articles dans le navigateur.
* `database.sql` : Script d'initialisation de la structure MySQL.
* `requirements.txt` : Liste des dépendances (incluant `rich`, `requests`, `mysql-connector`).
* `.env` : Configuration sécurisée des identifiants (non versionné).
* `venv/` : Environnement virtuel isolé.

## 🚀 Fonctionnalités Clés

### 1. Collecte Intelligente (`scraper.py`)

* **Multi-catégories** : Agrégation de sources variées :
* 🔐 **Cyber** : ANSSI, Zataz, Le Monde Informatique...
* 💻 **Dev** : Developpez.com, GitHub Blog...
* 🤖 **IA & Infra** : Actu IA, IT Connect...


* **Mode Hybride** :
* **Interactif** : Interface visuelle pour sélectionner manuellement les articles pertinents.
* **Automatique (Cron)** : Mode silencieux pour l'archivage planifié sur serveur.


* **Feedback Visuel** : Barres de progression et tableaux formatés grâce à la librairie **Rich**.

### 2. Consultation & Recherche (`search.py`)

* **Moteur SQL** : Recherche rapide par mots-clés dans les titres et les sources.
* **Navigation Fluide** : Ouverture directe des articles dans le navigateur web par simple sélection numérique.
* **Historique** : Accès à l'intégralité des articles archivés.

### 3. Sécurité & Robustesse

* **Gestion des doublons** : Utilisation de `INSERT IGNORE` pour garantir l'unicité des liens.
* **Environnement** : Séparation stricte du code et des secrets via `.env`.

## 🛠️ Installation

### 1. Préparation

Cloner le dépôt et configurer l'environnement virtuel :

```bash
git clone https://github.com/Flowz5/VeilleTechScraper.git
cd VeilleTechScraper

# Création et activation de l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# .\venv\Scripts\activate # Sur Windows

# Installation des dépendances
pip install -r requirements.txt

```

### 2. Base de données

Importez le fichier `database.sql` dans votre serveur MySQL/MariaDB.

### 3. Configuration

Dupliquez le fichier d'exemple et renseignez vos accès :

```bash
cp .env.exemple .env

```

*Modifiez ensuite `.env` avec vos identifiants BDD.*

## 🖥️ Utilisation

### Lancer une veille (Collecte)

Pour récupérer les derniers articles :

```bash
python scraper.py

```

### Rechercher un article

Pour interroger votre base de connaissances :

```bash
python search.py

```

## 🐧 Intégration Linux (Bonus)

Le projet est conçu pour s'intégrer parfaitement dans un workflow Linux (ex: **Hyprland**).
Exemple de *bindings* pour lancer la veille ou la recherche sans quitter le clavier :

```ini
# Hyprland Config
bind = SUPER, S, exec, kitty --hold bash -c "cd ~/Chemin/Projet && source venv/bin/activate && python scraper.py"
bind = SUPER SHIFT, S, exec, kitty --hold bash -c "cd ~/Chemin/Projet && source venv/bin/activate && python search.py"

```

## 📊 Valorisation BTS SIO

Ce projet couvre des compétences clés du diplôme :

* **Option SLAM** : Développement applicatif, utilisation de librairies tierces (`BeautifulSoup`, `Rich`), requêtage SQL complexe, gestion d'interfaces CLI.
* **Option SISR** : Automatisation de tâches (Scripting), gestion de flux de données, surveillance et centralisation de logs/informations (Veille).
