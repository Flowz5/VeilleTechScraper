import os
import mysql.connector
from dotenv import load_dotenv
import webbrowser

# --- IMPORTS RICH ---
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt

load_dotenv()
console = Console()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'), 
    'database': os.getenv('DB_NAME')
}

def connecter_bdd():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        console.print(f"[bold red]❌ Erreur de connexion : {err}[/bold red]")
        return None

def recherche_globale(mot_cle):
    conn = connecter_bdd()
    if not conn: return
    
    cursor = conn.cursor()
    query = """
        SELECT date, source, titre, lien 
        FROM articles 
        WHERE source LIKE %s OR titre LIKE %s 
        ORDER BY date DESC 
        LIMIT 30
    """
    search_term = f"%{mot_cle}%"
    cursor.execute(query, (search_term, search_term))
    resultats = cursor.fetchall()
    conn.close()
    
    if not resultats:
        console.print(f"[yellow]⚠️ Aucun résultat pour : '{mot_cle}'[/yellow]")
        return

    # --- AFFICHAGE TABLEAU RICH ---
    table = Table(title=f"🔎 Résultats pour : {mot_cle}", box=box.ROUNDED, border_style="blue")

    table.add_column("#", style="dim", justify="right")
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Source", style="magenta")
    table.add_column("Titre", style="bold white")

    # On remplit le tableau
    for i, (date, source, titre, lien) in enumerate(resultats):
        table.add_row(str(i+1), str(date), source, titre)

    console.print(table)
    
    # --- OUVERTURE NAVIGATEUR ---
    ouvrir_lien(resultats)

def ouvrir_lien(resultats):
    """Propose d'ouvrir un article dans le navigateur"""
    print()
    choix = Prompt.ask("[bold green]🚀 Ouvrir un article ?[/bold green] (Numéro ou Entrée pour passer)")
    
    if choix.isdigit():
        index = int(choix) - 1
        if 0 <= index < len(resultats):
            lien = resultats[index][3]
            console.print(f"🌍 Ouverture de : [underline blue]{lien}[/underline blue]...")
            webbrowser.open(lien)
        else:
            console.print("[red]Numéro invalide.[/red]")

def main():
    console.print(Panel.fit("[bold white]🔍 MOTEUR DE RECHERCHE DE VEILLE[/bold white]", style="on blue"))
    
    while True:
        mot = Prompt.ask("\n[bold cyan]👉 Recherche[/bold cyan] (ou 'q' pour quitter)")
        
        if mot.lower() == 'q':
            console.print("[dim]👋 À bientôt ![/dim]")
            break
            
        if len(mot) < 2:
            console.print("[red]⚠️ Mot-clé trop court ![/red]")
            continue
            
        recherche_globale(mot)

if __name__ == "__main__":
    main()