import requests
from bs4 import BeautifulSoup
import datetime

# --- CONFIGURATION ---
# On cible la rubrique Cybersécurité
URL_CIBLE = "https://www.lemondeinformatique.fr/actualites/rubrique-cybersecurite-24.html"
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

def parser_articles(html):
    """Analyse le HTML et extrait les articles."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Sélecteur pour LeMondeInformatique (div col-md-12 contient souvent les news)
    articles_bruts = soup.find_all('div', class_='col-md-12')
    
    resultats = []

    print(f"🔍 Analyse HTML en cours...")
    
    for article in articles_bruts:
        try:
            # 1. On cherche le Titre (souvent dans un <h3>)
            titre_balise = article.find('h3')
            if not titre_balise:
                continue # Si pas de titre, ce n'est pas un article
                
            titre = titre_balise.get_text().strip()
            
            # 2. On cherche le Lien
            lien_balise = article.find('a')
            if lien_balise:
                lien = lien_balise['href']
                # Si le lien est relatif (ex: /article/...), on ajoute le domaine
                if not lien.startswith('http'):
                    lien = "https://www.lemondeinformatique.fr" + lien
            else:
                lien = "N/A"

            # 3. On ajoute à notre liste de résultats
            resultats.append({
                "titre": titre,
                "lien": lien,
                "date": datetime.date.today()
            })
            
        except Exception as e:
            # On ignore les erreurs mineures pour ne pas arrêter le script
            continue

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