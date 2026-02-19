"""
=============================================================================
PROJET : CYBER-WATCH CLI (OUTIL D'ANALYSE TERMINAL)
DATE   : 19 Février 2026
DEV    : Léo
=============================================================================

LOG :
--------
[19/02 14:00] Initialisation du projet d'interface CLI.
[19/02 14:15] Connexion à la BDD MySQL via mysql-connector.
[19/02 14:40] Fonction 1 : Création du moteur de recherche avec scoring SQL. Match titre = 10 pts, match source = 5 pts.
[19/02 15:10] Fonction 2 : Implémentation de l'analyseur de tendances (buzz words sur les 7 derniers jours).
[19/02 15:30] Création de la stoplist pour virer le bruit sémantique (les, des, de, etc.).
[19/02 16:15] UX : Ajout de la navigation menu (Clear screen) et ouverture navigateur auto.
=============================================================================
"""

import os
import mysql.connector
from dotenv import load_dotenv
import webbrowser
from collections import Counter
import re

# Suite Rich pour faire un terminal propre (finis les print() dégueulasses)
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt

load_dotenv()
console = Console()

# Variables d'environnement standardisées
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'), 
    'database': os.getenv('DB_NAME')
}

# Stoplist hardcore pour cleaner l'analyse fréquentielle (NLP du pauvre)
STOP_WORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "ou", "a", "au", "aux", 
    "en", "par", "pour", "sur", "dans", "avec", "sans", "ce", "ces", "cet", "cette", "qui", 
    "que", "quoi", "dont", "est", "sont", "il", "elle", "ils", "elles", "je", "tu", "nous", 
    "vous", "mais", "pas", "plus", "moins", "très", "bien", "fait", "être", "avoir", "faire",
    "tout", "tous", "toute", "toutes", "votre", "notre", "leurs", "leur", "comme", "aussi",
    "cyber", "securite", "security", "faille", "contre" 
}

def connecter_bdd():
    # Helper générique de connexion
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        console.print(f"[bold red]❌ Erreur de connexion : {err}[/bold red]")
        return None


def recherche_pertinence(mot_cle):
    """Moteur de recherche pondéré directement en SQL"""
    conn = connecter_bdd()
    if not conn: return
    
    cursor = conn.cursor()
    
    # La magie SQL : 
    # Si le mot est dans le TITRE -> +10 points (Hyper pertinent)
    # Si le mot est dans le nom de la SOURCE -> +5 points (Contexte global)
    query = """
        SELECT date, source, titre, lien,
        (CASE WHEN titre LIKE %s THEN 10 ELSE 0 END + 
        CASE WHEN source LIKE %s THEN 5 ELSE 0 END) AS score
        FROM articles 
        WHERE source LIKE %s OR titre LIKE %s 
        ORDER BY score DESC, date DESC 
        LIMIT 20
    """
    
    term = f"%{mot_cle}%"
    # Injection paramétrée x4 car on a 4 placeholders %s dans la query
    cursor.execute(query, (term, term, term, term))
    resultats = cursor.fetchall()
    conn.close()
    
    if not resultats:
        console.print(f"[yellow]⚠️ Aucun résultat pertinent pour : '{mot_cle}'[/yellow]")
        return

    # Création du tableau Rich
    table = Table(title=f"🔎 Résultats pour : '{mot_cle}' (Tri par pertinence)", box=box.ROUNDED, border_style="blue", show_lines=True, padding=(0, 1))
    table.add_column("#", style="dim", justify="right")
    table.add_column("Score", style="yellow", justify="center")
    table.add_column("Date", style="cyan")
    table.add_column("Source", style="magenta")
    table.add_column("Titre", style="bold white")

    # Remplissage du tableau
    for i, (date, source, titre, lien, score) in enumerate(resultats):
        # Feedback visuel : on lâche une étoile si le score est max
        score_display = f"⭐ {score}" if score >= 10 else str(score)
        table.add_row(str(i+1), score_display, str(date), source, titre)

    console.print(table)
    # On passe la liste pour pouvoir ouvrir l'article derrière
    ouvrir_lien(resultats)


def analyser_tendances():
    """Extraction des KPIs et buzzwords de la semaine"""
    conn = connecter_bdd()
    if not conn: return
    cursor = conn.cursor()

    console.print(Panel("📊 [bold]ANALYSE HEBDOMADAIRE (7 Jours)[/bold]", style="green"))

    # 1. Volume par Source (100% SQL)
    query_vol = """
        SELECT source, COUNT(*) as vol 
        FROM articles 
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY source ORDER BY vol DESC LIMIT 5
    """
    cursor.execute(query_vol)
    top_sources = cursor.fetchall()

    # 2. Extraction des Mots-Clés (SQL + Python)
    # On ramène tous les titres en mémoire pour les processer
    query_titres = "SELECT titre FROM articles WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    cursor.execute(query_titres)
    raw_titles = cursor.fetchall()
    
    # Counter est parfait pour faire un dictionnaire de fréquences
    mots_compteur = Counter()
    
    for row in raw_titles:
        titre = row[0].lower()
        # Regex \b\w+\b chope les mots et ignore la ponctuation/espaces
        mots = re.findall(r'\b\w+\b', titre)
        
        # Filtre anti-bruit : on jette les stopwords et les mots < 4 lettres (le, un, du...)
        filtered_words = [m for m in mots if m not in STOP_WORDS and len(m) > 3]
        mots_compteur.update(filtered_words)
    
    # Top 5 des mots les plus utilisés
    top_mots = mots_compteur.most_common(5)

    # --- AFFICHAGE DASHBOARD ---
    
    # Tableau 1 : L'activité des sources
    table_src = Table(title="📢 Sources les plus actives", box=box.SIMPLE)
    table_src.add_column("Source", style="cyan")
    table_src.add_column("Vol.", style="magenta")
    for src, vol in top_sources:
        table_src.add_row(src, str(vol))

    # Tableau 2 : Les tendances sémantiques
    table_buzz = Table(title="🔥 Sujets brûlants (Mots-clés)", box=box.SIMPLE)
    table_buzz.add_column("Mot-clé", style="green")
    table_buzz.add_column("Freq.", style="yellow")
    for mot, freq in top_mots:
        table_buzz.add_row(mot.capitalize(), str(freq))

    console.print(table_src)
    console.print(table_buzz)
    conn.close()
    
    # Pause UX
    input("\nAppuyez sur Entrée pour revenir au menu...")


def ouvrir_lien(resultats):
    """Ouvre le lien de l'article dans le navigateur web par défaut"""
    print()
    # Prompt Rich super pratique qui bloque tant qu'on répond pas
    choix = Prompt.ask("[bold green]🚀 Ouvrir un article ?[/bold green] (Numéro ou Entrée pour passer)")
    
    if choix.isdigit():
        index = int(choix) - 1
        # Sécurité pour pas taper en dehors de la liste
        if 0 <= index < len(resultats):
            webbrowser.open(resultats[index][3]) # L'index 3 correspond au champ 'lien' du SELECT


def main():
    """Boucle principale de l'application CLI"""
    while True:
        # Clear l'écran pour garder l'UI clean entre chaque action
        os.system('cls' if os.name == 'nt' else 'clear') 
        
        console.print(Panel.fit("[bold white]🧠 CYBER-WATCH INTELLIGENCE[/bold white]", style="on blue"))
        
        console.print("\n[bold]Menu Principal :[/bold]")
        console.print("1. [cyan]🔍 Recherche Intelligente (Score de Pertinence)[/cyan]")
        console.print("2. [green]📊 Analyse des Tendances & Buzz Words[/green]")
        console.print("3. [red]🚪 Quitter[/red]")
        
        # Le default="1" permet de valider avec Entrée si on veut juste chercher
        choix = Prompt.ask("\n[bold]Votre choix[/bold]", choices=["1", "2", "3"], default="1")
        
        if choix == "3":
            console.print("[dim]Arrêt du système...[/dim]")
            break
            
        elif choix == "2":
            # Clear avant d'afficher les stats, c'est plus propre
            os.system('cls' if os.name == 'nt' else 'clear')
            analyser_tendances()
            
        elif choix == "1":
            mot = Prompt.ask("[bold cyan]👉 Entrez un mot-clé[/bold cyan]")
            # Petite verif pour eviter de chercher juste la lettre "a" et faire planter le truc
            if len(mot) >= 2:
                recherche_pertinence(mot)
                input("\nAppuyez sur Entrée pour continuer...") 
            else:
                console.print("[red]Erreur : Le mot-clé doit faire au moins 2 caractères.[/red]")
                input("\nAppuyez sur Entrée...")

if __name__ == "__main__":
    main()