import os
import requests
from bs4 import BeautifulSoup
import datetime
import mysql.connector
import sys
import logging
from dotenv import load_dotenv

# --- IMPORTS RICH ---
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from rich.theme import Theme

# Configuration du thème Rich
custom_theme = Theme({"success": "green", "warning": "yellow", "error": "bold red", "info": "cyan"})
console = Console(theme=custom_theme)

# Charger les variables
load_dotenv()

# --- CONFIGURATION LOGGING ---
logging.basicConfig(
    filename='journal.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- CONFIGURATION SOURCES ---
SOURCES = {
    # --- CYBERSÉCURITÉ ---
    "[CYBER] ANSSI (CERT-FR)": "https://www.cert.ssi.gouv.fr/feed/",
    "[CYBER] Le Monde Informatique": "https://www.lemondeinformatique.fr/flux-rss/rubrique/cybersecurite/rss.xml",
    "[CYBER] Zataz": "https://www.zataz.com/feed/",
    "[CYBER] ZDNet Sécu": "https://www.zdnet.fr/feeds/rss/actualites/security/",
    "[CYBER] WeLiveSecurity (ESET)": "https://www.welivesecurity.com/fr/feed/",
    
    # --- DÉVELOPPEMENT ---
    "[DEV] Developpez.com": "https://www.developpez.com/index/rss",
    "[DEV] Journal du Hacker": "https://www.journalduhacker.net/rss",
    "[DEV] GitHub Blog": "https://github.blog/feed/",
    
    # --- INFRA & LINUX ---
    "[INFRA] IT Connect": "https://www.it-connect.fr/feed/",
    "[INFRA] LinuxFR.org": "https://linuxfr.org/news.atom",
    "[INFRA] ZDNet Cloud": "https://www.zdnet.fr/feeds/rss/actualites/cloud-computing/",
    
    # --- TECH & IA ---
    "[IA] Actu IA": "https://www.actuia.com/feed/",
    "[TECH] Next": "https://next.ink/feed/", 
    "[TECH] Korben": "https://korben.info/feed"
}

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'), 
    'database': os.getenv('DB_NAME')
}

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
    soup = BeautifulSoup(xml, 'xml') 
    items = soup.find_all('item')[:50]
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
        
        for art in articles:
            query = "INSERT IGNORE INTO articles (date, source, titre, lien) VALUES (%s, %s, %s, %s)"
            valeurs = (art['date'], art['source'], art['titre'], art['lien'])
            cursor.execute(query, valeurs)
            if cursor.rowcount > 0:
                ajouts += 1
                
        conn.commit()
        logging.info(f"Succès SQL : {ajouts} articles ajoutés.")
        return ajouts
    except mysql.connector.Error as err:
        console.print(f"[error]❌ Erreur MySQL : {err}[/error]")
        logging.error(f"Erreur MySQL : {err}")
        return 0
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def main():
    logging.info("--- DÉMARRAGE DU SCRAPER ---")
    console.print(Panel.fit("🤖 [bold cyan]Scraper de Veille Technologique[/bold cyan]", border_style="blue"))
    
    tous_les_articles = []

    # --- ÉTAPE 1 : RÉCUPÉRATION ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("[green]Récupération des flux...", total=len(SOURCES))
        
        for nom_site, url_rss in SOURCES.items():
            xml = recuperer_xml(url_rss)
            if xml:
                articles_site = parser_articles(xml, nom_site)
                tous_les_articles.extend(articles_site)
            else:
                console.print(f"[warning]⚠️ Échec sur {nom_site}[/warning]")
                logging.warning(f"Échec flux : {nom_site}")
            
            progress.advance(task)

    console.print(f"\n[bold]📊 Total récupéré : {len(tous_les_articles)} articles.[/bold]")

    # --- ÉTAPE 2 : FILTRAGE ---
    articles_a_sauvegarder = []

    if sys.stdin.isatty():
        # Mode Interactif
        logging.info("Mode : Manuel (Interactif)")
        console.print("\n[bold yellow]👀 MODE INTERACTIF - TRI MANUEL[/bold yellow]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Source", style="cyan", width=25)
        table.add_column("Titre", style="white")

        for i, art in enumerate(tous_les_articles):
            table.add_row(str(i+1), art['source'], art['titre'])
        
        console.print(table)
        
        choix = console.input("[bold yellow]❌ Numéros à IGNORER (ex: 1,3) ou Entrée : [/bold yellow]")
        
        indices_a_ignorer = []
        if choix.strip():
            try:
                indices_a_ignorer = [int(x.strip()) for x in choix.split(',')]
            except ValueError:
                console.print("[error]Saisie invalide, tout est conservé.[/error]")

        for i, art in enumerate(tous_les_articles):
            if (i + 1) not in indices_a_ignorer:
                articles_a_sauvegarder.append(art)
    else:
        # Mode Automatique
        logging.info("Mode : Automatique (Cron/Arrière-plan)")
        console.print("[dim]🤖 Mode automatique : Sauvegarde complète.[/dim]")
        articles_a_sauvegarder = tous_les_articles

    # --- ÉTAPE 3 : SAUVEGARDE ---
    if articles_a_sauvegarder:
        with console.status("[bold green]Sauvegarde en base de données...[/bold green]"):
            nb_ajouts = sauvegarder_mysql(articles_a_sauvegarder)
        
        console.print(Panel(f"✅ TERMINÉ\n[bold green]{nb_ajouts} nouveaux articles ajoutés[/bold green]", border_style="green"))
    else:
        console.print("[warning]Aucun article à sauvegarder.[/warning]")
        logging.info("Aucun article sauvegardé.")

    logging.info("--- FIN DU SCRAPER ---\n")

if __name__ == "__main__":
    main()