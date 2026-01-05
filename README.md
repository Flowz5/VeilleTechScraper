
# 🛡️ Cyber-Watch : Automatisation de Veille Cybersécurité

Ce projet est un outil de veille technologique automatisé développé en Python. Il permet d'agréger, filtrer et archiver des flux RSS provenant de sources majeures de la cybersécurité dans une base de données MySQL.

## 📁 Structure du Projet

L'organisation du projet suit les standards de développement professionnel :

* `scraper.py` : Script principal contenant la logique de récupération et de traitement.
* `database.sql` : Script de création de la base de données et de la table des articles.
* `requirements.txt` : Liste des dépendances Python nécessaires.
* `.env` : Configuration locale des accès à la base de données (non versionné).
* `.env.exemple` : Modèle de configuration pour faciliter le déploiement.
* `journal.log` : Fichier de log permettant le suivi des exécutions (notamment via Cron).
* `venv/` : Environnement virtuel isolé pour les dépendances.

## 🚀 Fonctionnalités

* **Multi-sources** : Centralisation des flux (ANSSI, Zataz, Le Monde Informatique, etc.).
* **Mode Hybride** :
* **Interactif** : Permet de choisir manuellement les articles à conserver.
* **Automatique** : Idéal pour une exécution planifiée sans intervention humaine.


* **Sécurité** : Séparation stricte du code et des identifiants via les variables d'environnement.
* **Intégrité** : Gestion automatique des doublons en base de données.

## 🛠️ Installation et Configuration

### 1. Préparation de l'environnement

```bash
# Activation de l'environnement virtuel (Windows)
.\venv\Scripts\activate

# Installation des dépendances
pip install -r requirements.txt

```

### 2. Base de données

Importez le fichier `database.sql` dans votre serveur MySQL pour créer la structure nécessaire.

### 3. Configuration des accès

Copiez le fichier `.env.exemple` vers un nouveau fichier `.env` et complétez vos informations :

```env
DB_HOST=localhost
DB_USER=votre_user
DB_PASS=votre_password
DB_NAME=veille_tech

```

## 🖥️ Utilisation

Pour lancer une session de veille :

```bash
python scraper.py

```

## 📊 Valorisation BTS SIO

Ce projet permet de valider plusieurs compétences du référentiel :

* **Option SLAM** : Développement d'application, manipulation de bibliothèques tierces, gestion de persistance SQL.
* **Option SISR** : Automatisation de la veille (obligatoire pour l'E5), scripting système, gestion de la sécurité des données.

---

*Projet réalisé dans un cadre pédagogique - 2025*

---
