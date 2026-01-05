import requests
from bs4 import BeautifulSoup
import datetime

# --- CONFIGURATION ---
# On cible la rubrique Cybersécurité
URL_CIBLE = "https://www.lemondeinformatique.fr/flux-rss/rubrique/cybersecurite/rss.xml"# On se fait passer pour un vrai navigateur (indispensable pour ne pas être bloqué)
# On se fait passer pour un vrai navigateur (indispensable pour ne pas être bloqué)
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def recuperer_html(url):
    """Télécharge le code source d'une page."""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Lève une erreur si le site renvoie 404 ou 500
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau : {e}")
        return None

def parser_articles(xml):
    """Analyse le flux RSS et extrait les articles."""
    # On utilise 'xml' au lieu de 'html.parser' pour lire du RSS
    soup = BeautifulSoup(xml, 'xml') 
    
    items = soup.find_all('item')
    resultats = []
    
    for item in items:
        titre = item.title.text
        lien = item.link.text
        # La date est souvent dans <pubDate>
        
        resultats.append({
            "titre": titre,
            "lien": lien,
            "date": datetime.date.today()
        })
        
    return resultats

def main():
    print(f"🤖 Lancement du Scraper sur : {URL_CIBLE}")
    print("-" * 40)
    
    html = recuperer_html(URL_CIBLE)
    
    if html:
        articles = parser_articles(html)
        
        # Affichage des résultats
        print(f"\n✅ {len(articles)} articles trouvés (Affichage des 5 premiers) :\n")
        
        for art in articles[:5]:
            print(f"📅 {art['date']} | 📰 {art['titre']}")
            print(f"🔗 {art['lien']}")
            print("-" * 30)
    else:
        print("❌ Échec de la récupération de la page.")

if __name__ == "__main__":
    main()