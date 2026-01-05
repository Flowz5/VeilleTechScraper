import requests
from bs4 import BeautifulSoup
import datetime
import csv  # Nécessaire pour créer le fichier Excel

# --- CONFIGURATION ---
# On cible le flux RSS Cybersécurité (plus fiable que le HTML)
URL_CIBLE = "https://www.lemondeinformatique.fr/flux-rss/rubrique/cybersecurite/rss.xml"
# On se fait passer pour un vrai navigateur
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def recuperer_html(url):
    """Télécharge le code source (ici le XML du RSS)."""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau : {e}")
        return None

def parser_articles(xml):
    """Analyse le flux RSS et extrait les articles."""
    soup = BeautifulSoup(xml, 'xml') 
    
    items = soup.find_all('item')
    resultats = []
    
    for item in items:
        titre = item.title.text
        lien = item.link.text
        # Pour simplifier, on prend la date du jour de l'exécution
        date_jour = datetime.date.today()
        
        resultats.append({
            "titre": titre,
            "lien": lien,
            "date": date_jour
        })
        
    return resultats

def sauvegarder_csv(articles):
    """Sauvegarde les articles dans un fichier CSV (compatible Excel)."""
    nom_fichier = "veille_cybersecurite.csv"
    
    # Vérification : est-ce que le fichier existe déjà ?
    fichier_existe = False
    try:
        with open(nom_fichier, 'r', encoding='utf-8') as f:
            fichier_existe = True
    except FileNotFoundError:
        fichier_existe = False

    # Mode 'a' (append) pour ajouter à la suite sans effacer l'historique
    with open(nom_fichier, mode='a', newline='', encoding='utf-8') as f:
        # Le délimiteur ';' est important pour qu'Excel reconnaisse les colonnes en France
        writer = csv.writer(f, delimiter=';')
        
        # Si le fichier est tout neuf, on écrit la première ligne (les titres)
        if not fichier_existe:
            writer.writerow(["Date", "Titre", "Lien"])
            
        # On écrit chaque article
        compteur = 0
        for art in articles:
            writer.writerow([art['date'], art['titre'], art['lien']])
            compteur += 1
            
    print(f"💾 {compteur} articles sauvegardés dans le fichier '{nom_fichier}'")

def main():
    print(f"🤖 Lancement du Scraper sur : {URL_CIBLE}")
    print("-" * 40)
    
    # 1. Téléchargement
    contenu_xml = recuperer_html(URL_CIBLE)
    
    if contenu_xml:
        # 2. Analyse
        articles = parser_articles(contenu_xml)
        
        print(f"\n✅ {len(articles)} articles trouvés.\n")
        
        # 3. Sauvegarde dans le fichier
        sauvegarder_csv(articles)
        
        print("-" * 40)
        print("Terminé. Vous pouvez ouvrir 'veille_cybersecurite.csv' !")
        
    else:
        print("❌ Échec de la récupération.")

if __name__ == "__main__":
    main()