import requests
from bs4 import BeautifulSoup
import datetime
import mysql.connector # <--- Le nouveau pilote

# --- CONFIGURATION ---
URL_CIBLE = "https://www.lemondeinformatique.fr/flux-rss/rubrique/cybersecurite/rss.xml"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# ⚠️ À MODIFIER SELON TA CONFIGURATION LOCALE DBeaver/MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',        # Souvent 'root' ou ton nom d'utilisateur
    'password': 'admin', # <--- METS TON MOT DE PASSE ICI
    'database': 'veille_tech'
}

def recuperer_html(url):
    """Télécharge le XML."""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau : {e}")
        return None

def parser_articles(xml):
    """Extrait les articles du XML."""
    soup = BeautifulSoup(xml, 'xml') 
    items = soup.find_all('item')
    resultats = []
    
    for item in items:
        # Conversion de la date pour MySQL (YYYY-MM-DD)
        date_jour = datetime.date.today().strftime('%Y-%m-%d')
        
        resultats.append({
            "titre": item.title.text[:255], # On coupe si > 255 car VARCHAR(255)
            "lien": item.link.text[:255],
            "date": date_jour
        })
    return resultats

def sauvegarder_mysql(articles):
    """Insère les articles dans MySQL."""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        ajouts = 0
        
        for art in articles:
            # Syntaxe MySQL : INSERT IGNORE permet de ne pas planter si le lien existe déjà
            # Et on utilise %s pour les variables (pas ?)
            query = "INSERT IGNORE INTO articles (date, titre, lien) VALUES (%s, %s, %s)"
            valeurs = (art['date'], art['titre'], art['lien'])
            
            cursor.execute(query, valeurs)
            
            # rowcount vaut 1 si inséré, 0 si ignoré (doublon)
            if cursor.rowcount > 0:
                ajouts += 1
                
        conn.commit()
        print(f"💾 Base de données mise à jour : {ajouts} nouveaux articles ajoutés.")
        
    except mysql.connector.Error as err:
        print(f"❌ Erreur MySQL : {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def main():
    print(f"🤖 Récupération du flux RSS...")
    xml = recuperer_html(URL_CIBLE)
    
    if xml:
        tous_les_articles = parser_articles(xml)
        
        # 1. AFFICHAGE ET FILTRAGE
        print("\n--- 📰 ARTICLES DU FLUX ---")
        for i, art in enumerate(tous_les_articles):
            print(f"[{i+1}] {art['titre']}")
        
        print("\n" + "-"*30)
        choix = input("❌ Numéros à IGNORER (ex: 1, 3) : ")
        
        indices_a_ignorer = []
        if choix.strip():
            try:
                indices_a_ignorer = [int(x.strip()) for x in choix.split(',')]
            except ValueError: pass

        articles_a_sauvegarder = []
        for i, art in enumerate(tous_les_articles):
            if (i + 1) not in indices_a_ignorer:
                articles_a_sauvegarder.append(art)

        # 2. SAUVEGARDE MYSQL
        if articles_a_sauvegarder:
            sauvegarder_mysql(articles_a_sauvegarder)
        else:
            print("Aucun article retenu.")
            
    else:
        print("❌ Problème de flux.")

if __name__ == "__main__":
    main()