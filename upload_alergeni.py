import pandas as pd
import mysql.connector
#incarcam alergenii in baza de date
df = pd.read_csv("Produse_cu_alergeni_detectati.csv")

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
    SET alergeni = %s
    WHERE product_name = %s
    """
    cursor.execute(query, (row['detected_allergens'], row['product_name']))

conn.commit()
cursor.close()
conn.close()

print("Actualizare completă!")
