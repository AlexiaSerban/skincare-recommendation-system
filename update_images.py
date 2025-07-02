import os
import pymysql

# Conectare la baza de date MySQL
db = pymysql.connect(
    host="localhost",
    user="root",  
    password="",  
    database="recomandare_produse",
    charset="utf8mb4"
)
cursor = db.cursor()

image_folder = "/Users/alexiaserban/Documents/sistemDeRecomandare/produse_imagini"

for filename in os.listdir(image_folder):
    if filename.endswith(".jpg") or filename.endswith(".png"):  
        product_name = filename.replace(".jpg", "").replace(".png", "")  

        sql = "UPDATE produse SET imagine = %s WHERE product_name LIKE %s LIMIT 1"
        image_path = f"produse_imagini/{filename}"  
        cursor.execute(sql, (image_path, f"%{product_name}%")) 

db.commit()
cursor.close()
db.close()

print("Actualizare finalizată! Imaginile au fost asociate produselor în baza de date.")
