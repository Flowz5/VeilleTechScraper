import requests
from bs4 import BeautifulSoup
import datetime
import mysql.connector
import sys

# --- CONFIGURATION ---
SOURCES = {
    "Le Monde Informatique": "https://www.lemondeinformatique.fr/flux-rss/rubrique/cybersecurite/rss.xml",
    "ANSSI (CERT-FR)": "https://www.cert.ssi.gouv.fr/feed/",
    "Zataz": "https://www.zataz.com/feed/",
    "ZDNet France": "https://www.zdnet.fr/feeds/rss/actualites/security/",
    "Cyberguerre (Numerama)": "https://www.numerama.com/cyberguerre/feed/"
}

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# ⚠️ METS TON MOT DE PASSE MYSQL ICI
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin', 
    'database': 'veille_tech'
}

def recuperer_xml(url):
    """Télécharge le contenu XML d'un flux."""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"   ❌ Erreur de connexion : {e}")
        return None

def parser_articles(xml, nom_source):
    """Extrait les articles (LIMITE À 10 PAR SOURCE)."""
    soup = BeautifulSoup(xml, 'xml') 
    
    # ✅ LIMITATION : On ne prend que les 10 premiers items
    items = soup.find_all('item')[:10]
    
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
    """Insère les articles dans MySQL."""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        ajouts = 0
        
        for art in articles:
            query = """
                INSERT IGNORE INTO articles (date, source, titre, lien) 
                VALUES (%s, %s, %s, %s)
            """
            valeurs = (art['date'], art['source'], art['titre'], art['lien'])
            
            cursor.execute(query, valeurs)
            if cursor.rowcount > 0:
                ajouts += 1
                
        conn.commit()
        return ajouts
        
    except mysql.connector.Error as err:
        print(f"   ❌ Erreur MySQL : {err}")
        return 0
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def main():
    print(f"🤖 Lancement de la Veille...")
    print(f"📅 Date : {datetime.datetime.now()}")
    print("-" * 50)
    
    tous_les_articles = []

    # 1. RÉCUPÉRATION
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

    # 2. FILTRAGE INTELLIGENT (C'est ici que la magie opère)
    articles_a_sauvegarder = []

    # sys.stdin.isatty() renvoie True si c'est un humain (terminal interactif)
    # et False si c'est Cron ou un script automatique.
    if sys.stdin.isatty():
        print("\n👀 MODE MANUEL DÉTECTÉ - Vérification des articles :")
        
        # On affiche la liste à l'humain
        for i, art in enumerate(tous_les_articles):
            print(f"[{i+1}] [{art['source']}] {art['titre']}")
        
        print("\n" + "-"*30)
        choix = input("❌ Entrez les numéros à IGNORER (ex: 1, 3) ou Entrée pour tout garder : ")
        
        indices_a_ignorer = []
        if choix.strip():
            try:
                indices_a_ignorer = [int(x.strip()) for x in choix.split(',')]
            except ValueError:
                print("⚠️ Erreur de saisie. Tout sera conservé.")

        # On filtre
        for i, art in enumerate(tous_les_articles):
            if (i + 1) not in indices_a_ignorer:
                articles_a_sauvegarder.append(art)
            else:
                print(f"🗑️ Ignoré : {art['titre']}")
                
    else:
        # Mode automatique (Cron) : On ne demande rien, on garde tout
        print("\n🤖 MODE AUTOMATIQUE DÉTECTÉ : Sauvegarde intégrale sans interaction.")
        articles_a_sauvegarder = tous_les_articles

    # 3. SAUVEGARDE
    if articles_a_sauvegarder:
        print(f"\n💾 Enregistrement de {len(articles_a_sauvegarder)} articles en base...")
        nb_ajouts = sauvegarder_mysql(articles_a_sauvegarder)
        print(f"✅ TERMINÉ : {nb_ajouts} nouveaux articles ajoutés dans MySQL.")
    else:
        print("❌ Aucun article à sauvegarder.")

if __name__ == "__main__":
    main()