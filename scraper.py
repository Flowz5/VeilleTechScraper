"""
PROJET : Web Scrapper de Veille Technologique Automatisée
Auteur : Léo Dupont - BTS SIO 1
Description : 
Ce script permet de récupérer des articles depuis plusieurs flux RSS (Cyber et Dev).
Les articles sont filtrés (manuel ou auto) puis stockés dans une base de données MySQL.
Idéal pour alimenter un tableau de bord de veille.
"""

import os
import requests
from bs4 import BeautifulSoup
import datetime
import mysql.connector
import sys
from dotenv import load_dotenv

# --- 1. CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ---
# On utilise load_dotenv pour ne pas écrire les identifiants en dur dans le code
# C'est une bonne pratique de sécurité vue en cours de Cybersécurité
load_dotenv()

# --- 2. CONFIGURATION DES SOURCES ---
# J'ai choisi des sources mixtes pour couvrir les deux options du BTS (SLAM et SISR)
SOURCES = {
    "[CYBER] ANSSI (CERT-FR)": "https://www.cert.ssi.gouv.fr/feed/",
    "[CYBER] Le Monde Informatique": "https://www.lemondeinformatique.fr/flux-rss/rubrique/cybersecurite/rss.xml",
    "[CYBER] Zataz": "https://www.zataz.com/feed/",
    "[DEV] Developpez.com": "https://www.developpez.com/index/rss",
    "[DEV] Human Coders": "https://news.humancoders.com/items/feed"
}

# On définit un User-Agent pour simuler un navigateur et éviter d'être bloqué par les sites
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Configuration de la connexion MySQL via les variables du fichier .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'), 
    'database': os.getenv('DB_NAME')
}

# --- 3. FONCTION DE RÉCUPÉRATION (REQUÊTE HTTP) ---
def recuperer_xml(url):
    """
    Utilise la bibliothèque 'requests' pour télécharger le contenu du flux RSS.
    On gère les exceptions avec un bloc try/except pour éviter que le script plante.
    """
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        # On vérifie si la requête a réussi (code 200)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"   ❌ Erreur de connexion : {e}")
        return None

# --- 4. FONCTION DE PARSING (EXTRACTION DES DONNÉES) ---
def parser_articles(xml, nom_source):
    """
    Analyse le XML avec BeautifulSoup. 
    On limite à 10 articles par source pour ne pas surcharger la base de données.
    """
    soup = BeautifulSoup(xml, 'xml') 
    
    # On utilise le slicing Python [:10] pour limiter la liste
    items = soup.find_all('item')[:10]
    
    resultats = []
    
    for item in items:
        # On récupère la date du jour au format SQL (YYYY-MM-DD)
        date_jour = datetime.date.today().strftime('%Y-%m-%d')
        # On limite la taille des chaînes pour correspondre aux colonnes VARCHAR de la BDD
        titre = item.title.text[:255] if item.title else "Sans titre"
        lien = item.link.text[:255] if item.link else ""

        if lien:
            # On stocke les infos dans un dictionnaire avant de les ajouter à la liste
            resultats.append({
                "source": nom_source,
                "titre": titre,
                "lien": lien,
                "date": date_jour
            })
    return resultats

# --- 5. FONCTION DE STOCKAGE (BASE DE DONNÉES) ---
def sauvegarder_mysql(articles):
    """
    Se connecte à MySQL et insère les articles.
    On utilise 'INSERT IGNORE' pour ne pas avoir de doublons si on lance le script plusieurs fois.
    """
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        ajouts = 0
        
        for art in articles:
            # Requête préparée pour éviter les injections SQL
            query = """
                INSERT IGNORE INTO articles (date, source, titre, lien) 
                VALUES (%s, %s, %s, %s)
            """
            valeurs = (art['date'], art['source'], art['titre'], art['lien'])
            
            cursor.execute(query, valeurs)
            # On incrémente le compteur si une ligne a bien été ajoutée
            if cursor.rowcount > 0:
                ajouts += 1
                
        # On valide la transaction
        conn.commit()
        return ajouts
        
    except mysql.connector.Error as err:
        print(f"   ❌ Erreur MySQL : {err}")
        return 0
    finally:
        # On ferme proprement le curseur et la connexion (vu en SQL)
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- 6. PROGRAMME PRINCIPAL ---
def main():
    print(f"🤖 Lancement de la Veille...")
    print(f"📅 Date : {datetime.datetime.now()}")
    print("-" * 50)
    
    tous_les_articles = []

    # ETAPE A : RÉCUPÉRATION
    # On boucle sur le dictionnaire des sources défini au début
    for nom_site, url_rss in SOURCES.items():
        print(f"🌍 {nom_site}...", end=" ")
        xml = recuperer_xml(url_rss)
        
        if xml:
            articles_site = parser_articles(xml, nom_site)
            tous_les_articles.extend(articles_site)
            print(f"✅ OK ({len(articles_site)} articles)")
        else:
            print("⚠️ Erreur")

    print("-" * 50)
    print(f"📊 TOTAL RÉCUPÉRÉ : {len(tous_les_articles)} articles.")

    # ETAPE B : FILTRAGE (Intervention humaine ou Automatique)
    articles_a_sauvegarder = []

    # sys.stdin.isatty() permet de savoir si on lance le script à la main (True)
    # ou via une tâche planifiée type Cron (False).
    if sys.stdin.isatty():
        print("\n👀 MODE MANUEL DÉTECTÉ - Vérification des articles :")
        
        # Affichage pour l'utilisateur
        for i, art in enumerate(tous_les_articles):
            print(f"[{i+1}] [{art['source']}] {art['titre']}")
        
        print("\n" + "-"*30)
        choix = input("❌ Entrez les numéros à IGNORER (ex: 1, 3) ou Entrée pour tout garder : ")
        
        indices_a_ignorer = []
        if choix.strip():
            try:
                # Compréhension de liste pour convertir la saisie en entiers
                indices_a_ignorer = [int(x.strip()) for x in choix.split(',')]
            except ValueError:
                print("⚠️ Erreur de saisie. Tout sera conservé.")

        # On filtre la liste globale
        for i, art in enumerate(tous_les_articles):
            if (i + 1) not in indices_a_ignorer:
                articles_a_sauvegarder.append(art)
            else:
                print(f"🗑️ Ignoré : {art['titre']}")
                
    else:
        # En mode automatique (Cron), on ne peut pas poser de question
        print("\n🤖 MODE AUTOMATIQUE DÉTECTÉ : Sauvegarde intégrale sans interaction.")
        articles_a_sauvegarder = tous_les_articles

    # ETAPE C : SAUVEGARDE FINALE
    if articles_a_sauvegarder:
        print(f"\n💾 Enregistrement de {len(articles_a_sauvegarder)} articles en base...")
        nb_ajouts = sauvegarder_mysql(articles_a_sauvegarder)
        print(f"✅ TERMINÉ : {nb_ajouts} nouveaux articles ajoutés dans MySQL.")
    else:
        print("❌ Aucun article à sauvegarder.")

# Point d'entrée standard du script
if __name__ == "__main__":
    main()
