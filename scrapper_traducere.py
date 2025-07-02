import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from googletrans import Translator
import time

# datasetul complet
csv_file = "skincare_products_clean.csv"  
# Citim datele din CSV intr-un DataFrame
df = pd.read_csv(csv_file, delimiter=",", encoding="utf-8")
# Initializam translatorul Google
translator = Translator()
# Functie care extrage descrierea produsului de pe pagina web
def get_description(product_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(product_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
         # Cautam div-ul care contine descrierea produsului
        description_tag = soup.find("div", {"id": "product-description-0"})
        if description_tag:
            description_text = description_tag.get_text(strip=True)
            return description_text
        
        return "Descriere indisponibilă"
    
    except Exception as e:
        return f"Eroare la extragerea descrierii: {e}"
# Functie care traduce descrierea din engleza in romana
def translate_description(text):
    try:
        translated_text = translator.translate(text, src='en', dest='ro').text
        return translated_text
    except Exception as e:
        return "Eroare la traducere"
# Parcurgem fiecare produs din DataFrame
for i in range(len(df)):
    product_url = df.iloc[i]["product_url"]
    print(f"Procesam: {product_url}")
     # Extragere + traducere descriere
    description = get_description(product_url)
    translated_description = translate_description(description)
    # Adaugam traducerea in coloana "descriere"
    df.at[i, "descriere"] = translated_description
    
    time.sleep(2)  

df.to_csv("produse_cu_descriere.csv", index=False, encoding="utf-8")

print("Proces complet! Fisierul 'produse_cu_descriere.csv' este gata.")