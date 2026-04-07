import requests

N8N_URL = "http://localhost:5680/webhook-test/alert"

fake_article = {
    "titre": "🚨 [TEST] ALERTE RANSOMWARE DÉTECTÉE SUR LE RÉSEAU",
    "source": "Simulation Python",
    "lien": "https://www.google.com",
    "score": 10
}

try:
    print(f"📡 Envoi vers {N8N_URL}...")
    response = requests.post(N8N_URL, json=fake_article)
    
    if response.status_code == 200:
        print("✅ Message envoyé ! Vérifie ton Discord tout de suite !")
    else:
        print(f"❌ Erreur n8n : {response.status_code} - {response.text}")

except Exception as e:
    print(f"❌ Crash connexion : {e}")