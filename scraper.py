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

# --- [NOUVEAU] CONFIGURATION SCORING & N8N ---
# URL de ton Webhook n8n (Production)
# ⚠️ Remplace 'webhook-test' par 'webhook' quand tu actives le switch "Active" dans n8n
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/alert"

# Poids des mots-clés pour le déclenchement d'alerte
KEYWORDS_WEIGHTS = {
    # 🔴 CRITIQUE (3 pts)
    "ransomware": 3, "0-day": 3, "faille": 3, "critique": 3, "urgence": 3,
    "cve": 3, "breach": 3, "piratage": 3, "hacked": 3, "exploit": 3, "rce": 3,
    
    # 🟠 IMPORTANT (2 pts)
    "cyber": 2, "anssi": 2, "security": 2, "malware": 2, "rootkit": 2,
    "phishing": 2, "ddos": 2, "alert": 2, "vulnerabilité": 2,
    
    # 🔵 CONTEXTE (1 pt)
    "python": 1, "linux": 1, "docker": 1, "windows": 1, "google": 1
}

# --- CONFIGURATION SOURCES ---
SOURCES = {
    # --- CYBERSÉCURITÉ (FR) ---
    "[CYBER] ANSSI (CERT-FR)": "https://www.cert.ssi.gouv.fr/feed/",
    "[CYBER] Le Monde Informatique": "https://www.lemondeinformatique.fr/flux-rss/rubrique/cybersecurite/rss.xml",
    "[CYBER] Zataz": "https://www.zataz.com/feed/",
    "[CYBER] ZDNet Sécu": "https://www.zdnet.fr/feeds/rss/actualites/security/",
    "[CYBER] WeLiveSecurity (ESET)": "https://www.welivesecurity.com/fr/feed/",
    
    # --- CYBERSÉCURITÉ (US - Indispensable pour la réactivité) ---
    "[CYBER 🇺🇸] The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "[CYBER 🇺🇸] BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "[CYBER 🇺🇸] Google Security Blog": "https://security.googleblog.com/feeds/posts/default",
    
    # --- DÉVELOPPEMENT & PYTHON ---
    "[DEV] Developpez.com": "https://www.developpez.com/index/rss",
    "[DEV] Journal du Hacker": "https://www.journalduhacker.net/rss",
    "[DEV] GitHub Blog": "https://github.blog/feed/",
    "[DEV 🇺🇸] Real Python": "https://realpython.com/atom.xml",
    "[DEV 🇺🇸] Dev.to": "https://dev.to/feed",
    
    # --- INFRA, LINUX & CLOUD ---
    "[INFRA] IT Connect": "https://www.it-connect.fr/feed/",
    "[INFRA] LinuxFR.org": "https://linuxfr.org/news.atom",
    "[INFRA] ZDNet Cloud": "https://www.zdnet.fr/feeds/rss/actualites/cloud-computing/",
    "[INFRA] Toolinux": "http://feeds.feedburner.com/toolinux",
    "[INFRA 🇺🇸] AWS What's New": "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
    
    # --- TECH, IA & DATA ---
    "[IA] Actu IA": "https://www.actuia.com/feed/",
    "[TECH] Next": "https://next.ink/feed/", 
    "[TECH] Korben": "https://korben.info/feed",
    "[IA 🇺🇸] OpenAI Blog": "https://openai.com/blog/rss.xml",
    "[DATA 🇺🇸] KDnuggets": "https://www.kdnuggets.com/feed",
    "[SCIENCE] Numerama": "https://www.numerama.com/feed/"
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'), 
    'database': os.getenv('DB_NAME')
}

# --- [NOUVEAU] FONCTIONS INTELLIGENTES ---
def calculer_score(titre):
    """Calcule la pertinence d'un article"""
    score = 0
    titre_min = titre.lower()
    for mot, poids in KEYWORDS_WEIGHTS.items():
        if mot in titre_min:
            score += poids
    return score

def notifier_n8n(article, score):
    """Envoie l'article à n8n pour alerte Discord"""
    payload = {
        "titre": article['titre'],
        "source": article['source'],
        "lien": article['lien'],
        "score": score
    }
    try:
        # Timeout court (2s) pour ne pas bloquer le scraper si n8n est éteint
        requests.post(N8N_WEBHOOK_URL, json=payload, timeout=2)
    except Exception as e:
        # On log l'erreur discrètement sans faire planter le script
        logging.warning(f"Impossible de joindre n8n : {e}")

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
            # Insertion en base
            query = "INSERT IGNORE INTO articles (date, source, titre, lien) VALUES (%s, %s, %s, %s)"
            valeurs = (art['date'], art['source'], art['titre'], art['lien'])
            cursor.execute(query, valeurs)
            
            # Si rowcount > 0, c'est que l'article est NOUVEAU (pas un doublon)
            if cursor.rowcount > 0:
                ajouts += 1
                
                # --- [NOUVEAU] VÉRIFICATION ALERTES ---
                # On calcule le score seulement si l'article est nouveau
                score = calculer_score(art['titre'])
                
                # SEUIL D'ALERTE : 4 points
                # (Ex: "Ransomware" (3) + "Linux" (1) = 4 -> ALERTE)
                if score >= 0:
                    notifier_n8n(art, score)
                    alertes_envoyees += 1
                    console.print(f"[bold red]🔥 ALERTE ENVOYÉE : {art['titre']} (Score: {score})[/bold red]")

        conn.commit()
        logging.info(f"Succès SQL : {ajouts} ajouts, {alertes_envoyees} alertes envoyées.")
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
    console.print(Panel.fit("🤖 [bold cyan]Scraper de Veille Technologique v2[/bold cyan]", border_style="blue"))
    
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

    # --- ÉTAPE 3 : SAUVEGARDE & NOTIFICATIONS ---
    if articles_a_sauvegarder:
        with console.status("[bold green]Sauvegarde et Analyse IA...[/bold green]"):
            nb_ajouts = sauvegarder_mysql(articles_a_sauvegarder)
        
        console.print(Panel(f"✅ TERMINÉ\n[bold green]{nb_ajouts} nouveaux articles ajoutés[/bold green]", border_style="green"))
    else:
        console.print("[warning]Aucun article à sauvegarder.[/warning]")
        logging.info("Aucun article sauvegardé.")

    logging.info("--- FIN DU SCRAPER ---\n")

if __name__ == "__main__":
    main()