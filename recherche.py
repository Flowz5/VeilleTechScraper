import os
import mysql.connector
from dotenv import load_dotenv
import webbrowser
from collections import Counter
import re

# --- IMPORTS RICH ---
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt
from rich.layout import Layout
from rich.align import Align

load_dotenv()
console = Console()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'), 
    'database': os.getenv('DB_NAME')
}

# Liste de mots vides à ignorer pour l'analyse sémantique
STOP_WORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "ou", "a", "au", "aux", 
    "en", "par", "pour", "sur", "dans", "avec", "sans", "ce", "ces", "cet", "cette", "qui", 
    "que", "quoi", "dont", "est", "sont", "il", "elle", "ils", "elles", "je", "tu", "nous", 
    "vous", "mais", "pas", "plus", "moins", "très", "bien", "fait", "être", "avoir", "faire",
    "tout", "tous", "toute", "toutes", "votre", "notre", "leurs", "leur", "comme", "aussi",
    "cyber", "securite", "security" # On peut exclure les thèmes génériques
}

def connecter_bdd():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        console.print(f"[bold red]❌ Erreur de connexion : {err}[/bold red]")
        return None

# --- FONCTION 1 : RECHERCHE INTELLIGENTE (SCORING) ---
def recherche_pertinence(mot_cle):
    conn = connecter_bdd()
    if not conn: return
    
    cursor = conn.cursor()
    # SQL AVANCÉ : Calcul d'un score de pertinence dynamique
    # Titre match = 10 points | Source match = 5 points
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
    cursor.execute(query, (term, term, term, term))
    resultats = cursor.fetchall()
    conn.close()
    
    if not resultats:
        console.print(f"[yellow]⚠️ Aucun résultat pertinent pour : '{mot_cle}'[/yellow]")
        return

    # Affichage
    table = Table(title=f"🔎 Résultats pour : '{mot_cle}' (Tri par pertinence)", box=box.ROUNDED, border_style="blue", show_lines=True, padding=(0, 1))
    table.add_column("#", style="dim", justify="right")
    table.add_column("Score", style="yellow", justify="center") # On affiche le score !
    table.add_column("Date", style="cyan")
    table.add_column("Source", style="magenta")
    table.add_column("Titre", style="bold white")

    for i, (date, source, titre, lien, score) in enumerate(resultats):
        # On ajoute une étoile si le score est élevé (>10)
        score_display = f"⭐ {score}" if score >= 10 else str(score)
        table.add_row(str(i+1), score_display, str(date), source, titre)

    console.print(table)
    ouvrir_lien(resultats)

# --- FONCTION 2 : ANALYSE DES TENDANCES (DATA MINING) ---
def analyser_tendances():
    conn = connecter_bdd()
    if not conn: return
    cursor = conn.cursor()

    console.print(Panel("📊 [bold]ANALYSE HEBDOMADAIRE (7 Jours)[/bold]", style="green"))

    # 1. Volume par Source (SQL)
    query_vol = """
        SELECT source, COUNT(*) as vol 
        FROM articles 
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY source ORDER BY vol DESC LIMIT 5
    """
    cursor.execute(query_vol)
    top_sources = cursor.fetchall()

    # 2. Extraction des Mots-Clés (Python)
    # On récupère tous les titres de la semaine
    query_titres = "SELECT titre FROM articles WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    cursor.execute(query_titres)
    raw_titles = cursor.fetchall()
    
    mots_compteur = Counter()
    for row in raw_titles:
        titre = row[0].lower()
        # Regex pour ne garder que les mots (enlève ponctuation)
        mots = re.findall(r'\b\w+\b', titre)
        filtered_words = [m for m in mots if m not in STOP_WORDS and len(m) > 3]
        mots_compteur.update(filtered_words)
    
    top_mots = mots_compteur.most_common(5)

    # --- AFFICHAGE DASHBOARD ---
    # Tableau 1 : Top Sources
    table_src = Table(title="📢 Sources les plus actives", box=box.SIMPLE)
    table_src.add_column("Source", style="cyan"); table_src.add_column("Vol.", style="magenta")
    for src, vol in top_sources:
        table_src.add_row(src, str(vol))

    # Tableau 2 : Buzz Words
    table_buzz = Table(title="🔥 Sujets brûlants (Mots-clés)", box=box.SIMPLE)
    table_buzz.add_column("Mot-clé", style="green"); table_buzz.add_column("Freq.", style="yellow")
    for mot, freq in top_mots:
        table_buzz.add_row(mot.capitalize(), str(freq))

    console.print(table_src)
    console.print(table_buzz)
    conn.close()
    
    input("\nAppuyez sur Entrée pour revenir au menu...")

# --- UTILITAIRE : OUVRIR LIEN ---
def ouvrir_lien(resultats):
    print()
    choix = Prompt.ask("[bold green]🚀 Ouvrir un article ?[/bold green] (Numéro ou Entrée pour passer)")
    if choix.isdigit():
        index = int(choix) - 1
        if 0 <= index < len(resultats):
            webbrowser.open(resultats[index][3]) # Le lien est à l'index 3

# --- MENU PRINCIPAL ---
def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear') # Nettoie le terminal
        console.print(Panel.fit("[bold white]🧠 CYBER-WATCH INTELLIGENCE[/bold white]", style="on blue"))
        
        console.print("\n[bold]Menu Principal :[/bold]")
        console.print("1. [cyan]🔍 Recherche Intelligente (Score de Pertinence)[/cyan]")
        console.print("2. [green]📊 Analyse des Tendances & Buzz Words[/green]")
        console.print("3. [red]🚪 Quitter[/red]")
        
        choix = Prompt.ask("\n[bold]Votre choix[/bold]", choices=["1", "2", "3"], default="1")
        
        if choix == "3":
            console.print("[dim]Arrêt du système...[/dim]")
            break
        elif choix == "2":
            analyser_tendances()
        elif choix == "1":
            mot = Prompt.ask("[bold cyan]👉 Entrez un mot-clé[/bold cyan]")
            if len(mot) >= 2:
                recherche_pertinence(mot)
                input("\nAppuyez sur Entrée pour continuer...") # Pause pour lire
            else:
                console.print("[red]Mot trop court.[/red]")

if __name__ == "__main__":
    main()