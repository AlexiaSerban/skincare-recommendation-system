import pandas as pd
import mysql.connector

df = pd.read_csv("products_textura.csv")
#incarc textura in baza de date

conn = mysql.connector.connect(
    host="localhost",
    user="root",        
    password="",        
    database="recomandare_produse",
)
cursor = conn.cursor()

for _, row in df.iterrows():
    query = """
    UPDATE produse
    SET textura = %s
    WHERE product_name = %s
    """
    cursor.execute(query, (row['textura'], row['product_name']))

conn.commit()
cursor.close()
conn.close()

print("Actualizare TEXTURA completă!")
