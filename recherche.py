import os
import mysql.connector
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

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
        print(f"❌ Erreur de connexion : {err}")
        return None

def recherche_globale(mot_cle):
    conn = connecter_bdd()
    if not conn: return
    
    cursor = conn.cursor()
    
    # La magie est ici : on cherche dans la source OU dans le titre
    # %mot% permet de trouver le mot n'importe où dans la phrase
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
        print(f"\n⚠️ Aucun article ne contient le mot : '{mot_cle}'")
    else:
        print(f"\n🔍 {len(resultats)} RÉSULTATS POUR : '{mot_cle}'")
        print("=" * 80)
        for date, source, titre, lien in resultats:
            # On met en couleur (optionnel) le thème pour la lisibilité
            print(f"📅 {date} | {source}")
            print(f"📌 {titre}")
            print(f"🔗 {lien}")
            print("-" * 80)

def main():
    print("      ========================================")
    print("      🔍 MOTEUR DE RECHERCHE DE VEILLE SIO")
    print("      ========================================")
    
    while True:
        print("\nEntrez un thème (DEV, CYBER...) ou un mot-clé (Windows, Python, Script...)")
        choix = input("👉 Recherche (ou 'Q' pour quitter) : ").strip()

        if choix.upper() == 'Q':
            print("👋 Fermeture du moteur de recherche.")
            break
        
        if len(choix) < 2:
            print("⚠️ Veuillez entrer au moins 2 caractères.")
            continue
            
        recherche_globale(choix)

if __name__ == "__main__":
    main()