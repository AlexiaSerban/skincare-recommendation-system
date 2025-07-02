

from flask import Blueprint, request, render_template, redirect, url_for, flash, session
import mysql.connector
import random

recomandare_ai_bp = Blueprint('recomandare_ai', __name__)
#conexiune bd
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="recomandare_produse"
)

# Functie pentru a lua produse potrivite din baza de date
def get_recommended_products(skin_type, category):
    cursor = db.cursor(dictionary=True)
    query = """
    SELECT * FROM produse
    WHERE LOWER(skin_type) = LOWER(%s) AND LOWER(product_type) = LOWER(%s)
    """
    cursor.execute(query, (skin_type, category))

    produse = cursor.fetchall()
    cursor.close()

    if produse:
        return random.choice(produse)
    else:
        return None

#recomandari de rutina generata
@recomandare_ai_bp.route('/genereaza_rutina_ai', methods=['POST'])
def genereaza_rutina_ai():
    if "user_id" not in session:
        flash("Trebuie să fii autentificat.")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    # sterge vechea rutins daca exista
    cursor.execute("DELETE FROM rutina_ai WHERE user_id = %s", (user_id,))
    db.commit()

    cursor.execute("SELECT tip_ten FROM profil_utilizator WHERE user_id = %s", (user_id,))
    profil = cursor.fetchone()

    if not profil or not profil['tip_ten']:
        flash("Nu am găsit informații despre tipul tău de ten în profil.")
        cursor.close()
        return redirect(url_for("rutina_mea"))

    skin_type = profil['tip_ten'].lower()
#structurare pe pasi
    pasi = [
        {"nume": "Pasul 1: Curățare", "tip_cautare": "cleanser"},
        {"nume": "Pasul 2: Exfoliere", "tip_cautare": "exfoliator"},
        {"nume": "Pasul 3: Mască", "tip_cautare": "mask"},
        {"nume": "Pasul 4: Tonifiere", "tip_cautare": "toner"},
        {"nume": "Pasul 5: Ser", "tip_cautare": "serum"},
        {"nume": "Pasul 6: Cremă hidratantă", "tip_cautare": "moisturiser"},
    ]

    for pas in pasi:
        product = get_recommended_products(skin_type, pas["tip_cautare"])
        if product:
            cursor.execute(
                "INSERT INTO rutina_ai (user_id, product_id, step_name) VALUES (%s, %s, %s)",
                (user_id, product["id"], pas["nume"])
            )


    db.commit()
    cursor.close()

    return redirect(url_for('rutina_mea'))