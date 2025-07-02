import pandas as pd
import mysql.connector

df = pd.read_csv("products_skin_type_final.csv")
#incarc tipul de ten in baza de date

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
    SET skin_type = %s
    WHERE id = %s
    """
    cursor.execute(query, (row['skin_type'], int(row['id'])))

conn.commit()
cursor.close()
conn.close()

print("Actualizare completă!")
