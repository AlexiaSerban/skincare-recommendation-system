import os
import requests
import pandas as pd
from bs4 import BeautifulSoup

csv_file = "produse-nume-link.csv"
df = pd.read_csv(csv_file, delimiter=";")  
# Folderul unde vor fi salvate imaginile
image_folder = "produse_imagini"
os.makedirs(image_folder, exist_ok=True)
# Functie care descarca imaginea de pe pagina produsului
def download_image(product_name, product_url, folder=image_folder):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(product_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        img_tag = soup.find("img")  

        if img_tag and "src" in img_tag.attrs:
            img_url = img_tag["src"]
            img_filename = os.path.join(folder, f"{product_name[:50]}.jpg")

            img_data = requests.get(img_url).content
            with open(img_filename, "wb") as img_file:
                img_file.write(img_data)

            print(f"Descărcat: {img_filename}")
        else:
            print(f"Imagine indisponibilă pentru {product_name}")
    except Exception as e:
        print(f"Eroare la {product_name}: {e}")
# Parcurgem toate produsele din DataFrame
for i in range(len(df)): 
    product_name = df.iloc[i]["product_name"]
    product_url = df.iloc[i]["product_url"]
    download_image(product_name, product_url)

print("Proces finalizat!")
