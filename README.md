# Sistem de Recomandare pentru Produse de Îngrijire Personală
Această aplicație web oferă recomandări personalizate de produse cosmetice, folosind inteligență artificială, filtrare bazată pe conținut și filtrare colaborativă. Utilizatorii pot încărca o imagine pentru analiza tipului de ten, pot vizualiza produse recomandate, salva favorite și crea rutine de îngrijire personalizate.

## Funcționalități
- Autentificare și creare cont
- Profil utilizator cu preferințe (ten, alergii, textură, parfum)
- Analiza AI a tipului de ten pe bază de imagine (cu MobileNetV2) și recomandări pe baza tipului de ten obținut
- Recomandări AI:
  - Content-based (în funcție de profil)
  - Collaborative filtering (în funcție de evaluările altor utilizatori)
- Sistem de recenzii și ratinguri
- Pagini de produse cu filtrare (tip de ten, ingrediente, tip produs) și căutare
- Favorite 
- Rutine personalizate (manuale sau generate automat)
- Chatbot informativ
- Recomandări pe baza completării unui quiz

##  Tehnologii folosite
- Backend: Python, Flask
- Baza de date: MySQL
- Frontend: HTML, CSS, JavaScript
- Model AI: TensorFlow, Keras

##  Instalare

### 1. Se clonează proiectul

### 2. Se creează și activează un mediu virtual (opțional)
python -m venv venv
# Se activează mediul:
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

### 3. Se instalează dependențele
pip install -r requirements.txt

### 4. Se configurează .env 
- Pentru ca chatbot-ul și quiz-ul de skincare să funcționeze, aplicația folosește modelul GPT de la OpenAI. Este nevoie de o cheie API validă.
- Se creează un cont pe:  https://platform.openai.com/signup
- Pentru a se genera cheia:
  - Se accesează: https://platform.openai.com/api-keys
  - Se apasă pe butonul „Create new secret key”
  - Se copiază cheia generată (de forma: sk-...)
- În folderul principal al proiectului (acolo unde e app.py), se creează un fișier numit .env și se adaugă:
OPENAI_API_KEY=sk-... (cheia aici)

### 5. Setare bază de date
- Se instalează, apoi se deschide XAMPP și se pornește serviciul MySQL si Apache.
- Se accesează http://localhost/phpmyadmin și se creează o bază de date numită: recomandare_produse
- Pe tabul „Import” se selectează fișierul recomandare_produse.sql din proiect, apoi se apasă „Execută”.
- Setare conexiune MySql:
- Se verifică în app.py ca linia de conexiune să fie:
```python
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="recomandare_produse"
)
```


### 6. Pornire aplicație
- python3 app.py
- apoi deschide în browser:
http://127.0.0.1:5001/

