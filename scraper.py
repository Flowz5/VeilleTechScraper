"""
=============================================================================
PROJET : SCRAPER DE VEILLE TECH & SISR
DATE   : 19 Février 2026
DEV    : Léo
=============================================================================

LOG :
--------
[18/02 22:00] Init v2. Ajout de Rich pour avoir un terminal plus lisible.
[19/02 09:30] Ajout des sources US (BleepingComputer, HackerNews) pour l'actu 0-day.
[19/02 11:15] Intégration du système de scoring. Seuil d'alerte à 2 points.
[19/02 14:30] Connexion au webhook n8n pour push les alertes critiques sur Discord.
[19/02 18:03] Fix du timeout sur les requêtes n8n. Si le serveur est down, le script continue.
=============================================================================
"""

import os
import requests
from bs4 import BeautifulSoup
import datetime
import mysql.connector
import sys
import logging
from dotenv import load_dotenv

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from rich.theme import Theme

# Theme Rich pour le feedback visuel
custom_theme = Theme({"success": "green", "warning": "yellow", "error": "bold red", "info": "cyan"})
console = Console(theme=custom_theme)

load_dotenv()

# Log system pour debug post-cron
logging.basicConfig(
    filename='journal.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Webhook local n8n
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/alert"

# Dictionnaire de poids pour le tri automatique
KEYWORDS_WEIGHTS = {
    "ransomware": 3, "0-day": 3, "faille": 3, "critique": 3, "urgence": 3,
    "cve": 3, "breach": 3, "piratage": 3, "hacked": 3, "exploit": 3, "rce": 3,
    "cyber": 2, "anssi": 2, "security": 2, "malware": 2, "rootkit": 2,
    "phishing": 2, "ddos": 2, "alert": 2, "vulnerabilité": 2,
    "python": 1, "linux": 1, "docker": 1, "windows": 1, "google": 1
}

# Mapping des flux RSS par thématique
SOURCES = {
    "[CYBER] ANSSI (CERT-FR)": "https://www.cert.ssi.gouv.fr/feed/",
    "[CYBER] Le Monde Informatique": "https://www.lemondeinformatique.fr/flux-rss/rubrique/cybersecurite/rss.xml",
    "[CYBER] Zataz": "https://www.zataz.com/feed/",
    "[CYBER 🇺🇸] BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "[SISR] IT-Connect (Cours & Tutos)": "https://www.it-connect.fr/feed/",
    "[LINUX] LinuxFR.org": "https://linuxfr.org/news.atom",
    "[TECH] Korben": "https://korben.info/feed",
    "[IA 🇺🇸] OpenAI Blog": "https://openai.com/blog/rss.xml"
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'), 
    'database': os.getenv('DB_NAME')
}

def calculer_score(titre):
    # Calcul de la pertinence basé sur le titre
    score = 0
    titre_min = titre.lower()
    for mot, poids in KEYWORDS_WEIGHTS.items():
        if mot in titre_min:
            score += poids
    return score

def notifier_n8n(article, score):
    # Push Discord via n8n
    payload = {
        "titre": article['titre'],
        "source": article['source'],
        "lien": article['lien'],
        "score": score
    }
    try:
        # Timeout court pour pas freeze le scraper si n8n est off
        requests.post(N8N_WEBHOOK_URL, json=payload, timeout=2)
    except Exception as e:
        logging.warning(f"Webhook n8n injoignable : {e}")

def recuperer_xml(url):
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Erreur connexion {url} : {e}")
        return None

def parser_articles(xml, nom_source):
    # Parsing XML standard
    soup = BeautifulSoup(xml, 'xml') 
    items = soup.find_all('item')[:100]
    resultats = []
    
    for item in items:
        date_jour = datetime.date.today().strftime('%Y-%m-%d')
        titre = item.title.text[:255] if item.title else "Sans titre"
        lien = item.link.text[:255] if item.link else ""

        if lien:
            resultats.append({
                "source": nom_source,
                "titre": titre,
                "lien": lien,
                "date": date_jour
            })
    return resultats

def sauvegarder_mysql(articles):
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        ajouts = 0
        alertes_envoyees = 0
        
        for art in articles:
            # INSERT IGNORE pour eviter les doublons
            query = "INSERT IGNORE INTO articles (date, source, titre, lien) VALUES (%s, %s, %s, %s)"
            valeurs = (art['date'], art['source'], art['titre'], art['lien'])
            cursor.execute(query, valeurs)
            
            # Traitement des alertes uniquement si l'article est nouveau
            if cursor.rowcount > 0:
                ajouts += 1
                score = calculer_score(art['titre'])
                
                # Seuil de déclenchement d'alerte
                if score >= 2:
                    notifier_n8n(art, score)
                    alertes_envoyees += 1
                    console.print(f"[bold red]ALERTE : {art['titre']} (Score: {score})[/bold red]")

        conn.commit()
        logging.info(f"Stats SQL : {ajouts} nouveaux, {alertes_envoyees} alertes.")
        return ajouts
    except mysql.connector.Error as err:
        console.print(f"[error]Erreur MySQL : {err}[/error]")
        return 0
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def main():
    console.print(Panel.fit("🤖 Scraper de Veille v2", border_style="blue"))
    tous_les_articles = []

    # Etape 1 : Crawling des flux
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Récupération RSS...", total=len(SOURCES))
        for nom_site, url_rss in SOURCES.items():
            xml = recuperer_xml(url_rss)
            if xml:
                articles_site = parser_articles(xml, nom_site)
                tous_les_articles.extend(articles_site)
            progress.advance(task)

    # Etape 2 : Tri manuel ou auto
    articles_a_sauvegarder = []
    if sys.stdin.isatty():
        # Mode Manuel
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", width=4)
        table.add_column("Source", width=25)
        table.add_column("Titre")

        for i, art in enumerate(tous_les_articles):
            table.add_row(str(i+1), art['source'], art['titre'])
        console.print(table)
        
        choix = console.input("[bold yellow]IDs à ignorer (ex: 1,3) ou Entrée : [/bold yellow]")
        indices_a_ignorer = [int(x.strip()) for x in choix.split(',')] if choix.strip() else []

        for i, art in enumerate(tous_les_articles):
            if (i + 1) not in indices_a_ignorer:
                articles_a_sauvegarder.append(art)
    else:
        # Mode Cron (tout sauvegarder)
        articles_a_sauvegarder = tous_les_articles

    # Etape 3 : Commit
    if articles_a_sauvegarder:
        with console.status("Sauvegarde..."):
            nb_ajouts = sauvegarder_mysql(articles_a_sauvegarder)
        console.print(f"✅ Terminé : {nb_ajouts} nouveaux articles.")
    
if __name__ == "__main__":
    main()