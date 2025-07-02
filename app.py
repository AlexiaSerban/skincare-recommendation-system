from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from datetime import date
import mysql.connector
import bcrypt
import os
import openai
from dotenv import load_dotenv
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image as keras_image
import numpy as np
from recomandare_ai import recomandare_ai_bp
from content_filtering import recomanda_produse

#cheia API din fisierul .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

#initializare aplicatia Flask
app = Flask(__name__)
app.secret_key = "secret_key"  

app.config["SESSION_TYPE"] = "filesystem"

# blueprint-ul pentru rutele AI
app.register_blueprint(recomandare_ai_bp)

#setarea pentru folderul de upload
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Conexiunea la baza de date
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="recomandare_produse"
)

# Pagina principala
@app.route('/')
def home():
    username = session.get("username")  # Verif daca utilizatorul e logat
    return render_template('index.html', username=username)

# Pagina produse
def get_all_products():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT product_name, product_url, product_type, clean_ingreds, descriere, imagine, id FROM produse")
    products = cursor.fetchall()
    cursor.close()
    return products
#paginare produse
def get_products_paginated(page, per_page=30):
    offset = (page - 1) * per_page
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM produse")
    total_products = cursor.fetchone()["total"]
    total_pages = (total_products // per_page) + (1 if total_products % per_page > 0 else 0)
    cursor.execute("SELECT product_name, product_url, product_type, clean_ingreds, descriere, imagine, id FROM produse LIMIT %s OFFSET %s", (per_page, offset))
    products = cursor.fetchall()
    cursor.close()
    
    return products, total_pages

#FILTRARE
def get_top_ingredients():
    return [
        "Water", "Niacinamide", "Retinol", "Lanolin", "Butane",
        "Propylene glycol", "Cetyl alcohol", "Squalene", "Lactic acid",
        "Ceramide", "Peptide", "Glycerin", "Pantenol", "Glycolic acid", 
        "Sodium hyaluronate", "Dimethicone", "Castor oil", "Sodium lactate", 
        "Alcohol", "Kaolin", "Butylene glycol", "Alanine"
    ]
@app.route('/produse', methods=['GET', 'POST'])
def produse():
    page = int(request.args.get("page", 1))
    product_type = request.args.get("type", "").strip()
    selected_ingredients = request.args.getlist("ingredients")
    skin_type = request.args.get("skin_type", "").strip()

    query = "SELECT * FROM produse WHERE 1=1"
    params = []

    if product_type:
        query += " AND LOWER(product_type) = LOWER(%s)"
        params.append(product_type)

    if skin_type:
        query += " AND LOWER(skin_type) = LOWER(%s)"
        params.append(skin_type)

    if selected_ingredients:
        ingredient_conditions = " OR ".join(["LOWER(clean_ingreds) LIKE LOWER(%s)" for _ in selected_ingredients])
        query += f" AND ({ingredient_conditions})"
        params.extend([f"%{ing}%" for ing in selected_ingredients])

    cursor = db.cursor(dictionary=True)

    if product_type or selected_ingredients or skin_type:
        cursor.execute(query, params)
        products = cursor.fetchall()
        total_pages = 1
    else:
        count_query = "SELECT COUNT(*) as total FROM produse"
        cursor.execute(count_query)
        total_products = cursor.fetchone()["total"]
        per_page = 30
        total_pages = (total_products // per_page) + (1 if total_products % per_page > 0 else 0)

        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        cursor.execute(query, params)
        products = cursor.fetchall()

    cursor.close()

    ingredients_list = get_top_ingredients()

    favorite_ids = []
    if "user_id" in session:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT product_id FROM favorite WHERE user_id = %s", (session["user_id"],))
        favorite_ids = [row["product_id"] for row in cursor.fetchall()]
        cursor.close()

    return render_template(
        'produse.html',
        products=products,
        page=page,
        total_pages=total_pages,
        product_type=product_type,
        selected_ingredients=selected_ingredients,
        ingredients_list=ingredients_list,
        favorite_ids=favorite_ids
    )

#PAGINA PRODUS INDIVIDUAL
def product_page(product_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produse WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()

    if not product:
        return "Produsul nu a fost găsit", 404

    return render_template('product.html', product=product)


#CAUTARE
@app.route('/cautare', methods=['GET'])
def cautare():
    search_query = request.args.get("query", "").strip()
    product_type = request.args.get("type", "").strip()
    selected_ingredients = request.args.getlist("ingredients")

    query = "SELECT * FROM produse WHERE 1=1"
    params = []

    # Cautare `product_name` și `clean_ingreds`
    if search_query:
        query += " AND (product_name LIKE %s OR clean_ingreds LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    # Aplica filtrul dupa tipul de produs 
    if product_type:
        query += " AND product_type = %s"
        params.append(product_type)

    # Aplica filtrul dupa ingrediente (daca sunt selectate)
    if selected_ingredients:
        ingredient_conditions = " OR ".join(["FIND_IN_SET(%s, clean_ingreds)" for _ in selected_ingredients])
        query += f" AND ({ingredient_conditions})"
        params.extend(selected_ingredients)

    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    products = cursor.fetchall()
    cursor.close()

    return jsonify(products)

#FAVORITE 
@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    if "user_id" not in session:
        return jsonify({"error": "Autentificare necesară"}), 401

    data = request.get_json()
    product_id = data.get("product_id")
    action = data.get("action")
    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    if action == "add":
        try:
            cursor.execute("INSERT IGNORE INTO favorite (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
            db.commit()
        except Exception as e:
            print("Eroare la adăugare favorite:", e)
            return jsonify({"error": "Eroare la adăugare"}), 500

    elif action == "remove":
        try:
            cursor.execute("DELETE FROM favorite WHERE user_id = %s AND product_id = %s", (user_id, product_id))
            db.commit()
        except Exception as e:
            print("Eroare la ștergere favorite:", e)
            return jsonify({"error": "Eroare la ștergere"}), 500

    cursor.close()
    return jsonify({"success": True})

# Inregistrare utilizator
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Criptam parola
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                           (username, email, hashed_password.decode('utf-8')))
            db.commit()
            flash("Înregistrare reușită! Te poți autentifica acum.")
            return redirect(url_for("login"))
        except mysql.connector.Error as err:
            flash(f"Eroare: {err}")
            return redirect(url_for("register"))

    return render_template("register.html")

#RECENZII
# Fct pentru a obtine detaliile unui produs si recenziile acestuia
def get_product_with_reviews(product_id):
    cursor = db.cursor(dictionary=True)

    # Obtine detaliile produsului
    cursor.execute("SELECT * FROM produse WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        return None, None, None

    # Obtine recenziile pentru produs
    cursor.execute("SELECT username, rating, review_text, created_at FROM reviews WHERE product_id = %s ORDER BY created_at DESC", (product_id,))
    reviews = cursor.fetchall()

    # Obtine media rating-ului 
    cursor.execute("SELECT IFNULL(AVG(rating), 0) as avg_rating FROM reviews WHERE product_id = %s", (product_id,))
    avg_rating = cursor.fetchone()["avg_rating"]
    avg_rating = round(avg_rating, 1) if avg_rating else 0  # Daca nu există recenzii, rating = 0

    cursor.close()
    return product, reviews, avg_rating


@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_page(product_id):
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        if "username" not in session:
            flash("Trebuie să fii autentificat pentru a lăsa o recenzie!")
            return redirect(url_for("login"))

        username = session["username"]
        rating = int(request.form["rating"])
        review_text = request.form["review_text"]

        # Verificam daca userul a lasat deja o recenzie pentru acest produs
        cursor.execute("SELECT * FROM reviews WHERE product_id = %s AND username = %s", (product_id, username))
        existing_review = cursor.fetchone()

        if existing_review:
            flash("Ai lăsat deja o recenzie pentru acest produs!")
        else:
            # Adaug recenzia in bd
            cursor.execute(
                "INSERT INTO reviews (product_id, username, rating, review_text) VALUES (%s, %s, %s, %s)",
                (product_id, username, rating, review_text)
            )
            db.commit()
            flash("Recenzia ta a fost adăugată cu succes!")

        cursor.close()
        return redirect(url_for("product_page", product_id=product_id))

    product, reviews, avg_rating = get_product_with_reviews(product_id)

    if not product:
        return "Produsul nu a fost găsit", 404
    
    favorite_ids = []
    if "user_id" in session:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT product_id FROM favorite WHERE user_id = %s", (session["user_id"],))
        favorite_ids = [row["product_id"] for row in cursor.fetchall()]
        cursor.close()

    return render_template(
        'product.html',
        product=product,
        reviews=reviews,
        avg_rating=avg_rating,
        favorite_ids=favorite_ids  
    )

#FAVORITE
@app.route('/favorite')
def favorite():
    if "user_id" not in session:
        flash("Trebuie să fii autentificat pentru a accesa favoritele.")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cursor = db.cursor(dictionary=True)

    # Select toate produsele favorite ale utilizatorului
    cursor.execute("""
        SELECT p.id, p.product_name, p.product_type, p.imagine
        FROM produse p
        JOIN favorite f ON p.id = f.product_id
        WHERE f.user_id = %s
    """, (user_id,))
    
    favorite_products = cursor.fetchall()
    cursor.close()

    return render_template("favorite.html", favorite_products=favorite_products)


#recomandari pe baza tipului de ten

#pt carusel
@app.route('/recomandari/<skin_type>')
def produse_carousel(skin_type):
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT * FROM (
            SELECT * FROM produse
            WHERE skin_type = %s
            ORDER BY RAND()
        ) AS random_produse
        GROUP BY product_type
    """
    cursor.execute(query, (skin_type,))
    produse = cursor.fetchall()
    cursor.close()

    return jsonify(produse)


@app.route('/recomandari_ten/<skin_type>')
def recomandari_ten(skin_type):
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM produse WHERE skin_type = %s"
    cursor.execute(query, (skin_type,))
    produse = cursor.fetchall()
    cursor.close()

    favorite_ids = []
    if "user_id" in session:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT product_id FROM favorite WHERE user_id = %s", (session["user_id"],))
        favorite_ids = [row["product_id"] for row in cursor.fetchall()]
        cursor.close()

    return render_template(
        "recomandari_ten.html",
        produse=produse,
        skin_type=skin_type,
        favorite_ids=favorite_ids
    )

    #return render_template("recomandari_ten.html", produse=produse, skin_type=skin_type)




# Autentificare utilizator
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Bine ai venit, {user['username']}!")
            return redirect(url_for("home"))
        else:
            flash("Email sau parolă incorectă!")

    return render_template("login.html")

@app.context_processor
def inject_user():
    return {
        "username": session.get("username")
    }

# Delogare utilizator
@app.route("/logout")
def logout():
    session.clear()
    flash("Te-ai delogat cu succes!")
    return redirect(url_for("home"))


#rutina
@app.route('/rutina_mea')
def rutina_mea():
    if "user_id" not in session:
        flash("Trebuie să fii autentificat pentru a accesa rutina.")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    db_reconnect = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="recomandare_produse"
    )
    cursor = db_reconnect.cursor(dictionary=True)

    # tipul de ten al utilizatorului
    cursor.execute("SELECT tip_ten FROM profil_utilizator WHERE user_id = %s", (user_id,))
    rezultat_ten = cursor.fetchone()

    if not rezultat_ten:
        flash("Nu ai completat profilul cu tipul de ten.")
        return redirect(url_for("profile"))

    tip_ten = rezultat_ten["tip_ten"]

   
    pasi = [
        {"nume": "Pasul 1: Curățare", "tip_cautare": "cleanser"},
        {"nume": "Pasul 2: Exfoliere", "tip_cautare": "exfoliator"},
        {"nume": "Pasul 3: Mască", "tip_cautare": "mask"},
        {"nume": "Pasul 4: Tonifiere", "tip_cautare": "toner"},
        {"nume": "Pasul 5: Ser", "tip_cautare": "serum"},
        {"nume": "Pasul 6: Cremă hidratantă", "tip_cautare": "moisturiser"},
    ]

    steps = []

    for pas in pasi:
        cursor.execute("""
            SELECT p.* FROM produse p
            JOIN rutina r ON p.id = r.product_id
            WHERE r.user_id = %s AND p.product_type = %s AND p.skin_type = %s
        """, (user_id, pas["tip_cautare"], tip_ten))
        produs = cursor.fetchone()

        steps.append({
            "nume": pas["nume"],
            "tip_cautare": pas["tip_cautare"],
            "produs": produs
        })

    # Rutina generata
    cursor.execute("""
        SELECT p.*, ra.step_name
        FROM produse p
        JOIN rutina_ai ra ON p.id = ra.product_id
        WHERE ra.user_id = %s
        ORDER BY ra.id
    """, (user_id,))
    rutina_ai = cursor.fetchall()

    cursor.close()
    db_reconnect.close()

    return render_template("rutina_mea.html", rutina_mea=steps, rutina_ai=rutina_ai)

   
#adaugare in rutina
@app.route('/adauga_in_rutina', methods=['POST'])
def adauga_in_rutina():
    if "user_id" not in session:
        flash("Trebuie să fii autentificat pentru a adăuga în rutină.")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    product_id = request.form.get("product_id")
    product_type = request.form.get("product_type")

    cursor = db.cursor(dictionary=True)

    # 1. Aflăm tipul de ten al utilizatorului
    cursor.execute("SELECT tip_ten FROM profil_utilizator WHERE user_id = %s", (user_id,))
    rezultat_ten = cursor.fetchone()

    if not rezultat_ten:
        flash("Nu ai completat tipul de ten în profil.")
        return redirect(url_for("profile"))

    tip_ten_user = rezultat_ten["tip_ten"]

    # 2. Aflăm pentru ce tip de ten e produsul
    cursor.execute("SELECT skin_type FROM produse WHERE id = %s", (product_id,))
    produs = cursor.fetchone()

    if not produs:
        flash("Produsul nu a fost găsit.")
        return redirect(url_for("rutina_mea"))

    tip_ten_produs = produs["skin_type"]

    # 3. Dacă produsul NU e pentru tipul lui de ten ⇒ mesaj + redirect
    if tip_ten_user != tip_ten_produs:
        flash(f"Atenție! Acest produs este pentru tenul {tip_ten_produs}, nu pentru tenul tău {tip_ten_user}.")
        return redirect(url_for("rutina_mea"))

    # 4. Dacă e ok, continuăm ca înainte
    cursor.execute("""
        DELETE FROM rutina
        WHERE user_id = %s AND product_id IN (
            SELECT id FROM produse WHERE product_type = %s
        )
    """, (user_id, product_type))

    cursor.execute("INSERT INTO rutina (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
    db.commit()
    cursor.close()

    flash("Produsul a fost adăugat în rutina ta!")
    return redirect(url_for("rutina_mea"))

#stergere rutina
@app.route('/sterge_din_rutina', methods=['POST'])
def sterge_din_rutina():
    if "user_id" not in session:
        flash("Trebuie să fii autentificat.")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    product_id = request.form.get("product_id")

    cursor = db.cursor(dictionary=True)
    cursor.execute("DELETE FROM rutina WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    db.commit()
    cursor.close()

    flash("Produsul a fost eliminat din rutină.")
    return redirect(url_for("rutina_mea"))


# Profil utilizator
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        flash("Trebuie să te autentifici mai întâi!")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    username = session["username"]
    cursor = db.cursor(dictionary=True)

    # Recomandări CBF
    produse_recomandate = []
    try:
        df = recomanda_produse(user_id)
        produse_recomandate = df[['id', 'product_name', 'similarity_score', 'imagine']].to_dict(orient="records")
    except Exception as e:
        print(f"Eroare la generarea recomandarilor: {e}")

    # Recomandări collaborative
    produse_collab = []
    try:
        from recomandari_collaborative import get_recommendations_for_user
        ids = get_recommendations_for_user(username)[:10]
        print("ID-uri recomandate:", ids)
        if ids:
            format_ids = ','.join(['%s'] * len(ids))
            cursor.execute(f"SELECT id, product_name, imagine FROM produse WHERE id IN ({format_ids})", tuple(ids))
            produse_collab = cursor.fetchall()
    except Exception as e:
        print(f"Eroare recomandări collaborative: {e}")

    # Procesare formular profil
    if request.method == "POST":
        nume = request.form["nume"]
        varsta = request.form["varsta"]
        gen = request.form["gen"]
        tip_ten = request.form["tip_ten"]
        alergii = request.form["alergii"]
        textura = request.form["textura"]

        imagine = None
        data_analiza = None

        if "imagine" in request.files:
            img_file = request.files["imagine"]
            if img_file and img_file.filename != "":
                image_name = f"{username}_{img_file.filename}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
                img_file.save(image_path)
                imagine = image_name
                data_analiza = date.today()

        cursor.execute("SELECT * FROM profil_utilizator WHERE user_id = %s", (user_id,))
        profil = cursor.fetchone()

        if profil:
            # UPDATE
            sql = """
                UPDATE profil_utilizator SET
                    nume=%s, varsta=%s, gen=%s, tip_ten=%s,
                    alergii=%s, textura=%s
            """
            values = [nume, varsta, gen, tip_ten, alergii, textura]
            if imagine:
                sql += ", imagine=%s, data_analiza=%s"
                values.extend([imagine, data_analiza])
            sql += " WHERE user_id=%s"
            values.append(user_id)
            cursor.execute(sql, tuple(values))
        else:
            # INSERT
            cursor.execute("""
                INSERT INTO profil_utilizator (
                    user_id, nume, varsta, gen, tip_ten,
                    alergii, textura, imagine, data_analiza
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, nume, varsta, gen, tip_ten, alergii, textura, imagine, data_analiza))

        db.commit()
        flash("Profil actualizat cu succes!")
        return redirect(url_for("profile"))

    # Preluare date profil + favorite
    cursor.execute("SELECT * FROM profil_utilizator WHERE user_id = %s", (user_id,))
    profil = cursor.fetchone()

    favorite_ids = []
    cursor.execute("SELECT product_id FROM favorite WHERE user_id = %s", (user_id,))
    favorite_ids = [row["product_id"] for row in cursor.fetchall()]
    cursor.close()

    return render_template(
        "profile.html",
        username=username,
        profil=profil,
        produse=produse_recomandate,
        produse_collab=produse_collab,
        favorite_ids=favorite_ids
    )

# chatbot
@app.route("/chatbot", methods=["POST"])
def chatbot_response():
    data = request.json
    user_input = data.get("message", "")

    # Inițializăm istoricul conversației dacă nu există
    if "chat_history" not in session:
        session["chat_history"] = []

    # Adăugăm mesajul utilizatorului la istoric
    session["chat_history"].append({"role": "user", "content": user_input})

    try:
        # Trimitem tot istoricul către OpenAI
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ești un consultant de beauty profesionist. Răspunde prietenos și clar la întrebările despre piele, păr, cosmetice și îngrijire personală."}
            ] + session["chat_history"],
            temperature=0.7,
            max_tokens=500
        )
        response_text = completion.choices[0].message["content"]

        # Salvăm răspunsul chatbot-ului în istoric
        session["chat_history"].append({"role": "assistant", "content": response_text})

    except Exception as e:
        print(f"Eroare OpenAI: {e}")
        response_text = "Îmi pare rău, momentan nu pot răspunde. Încearcă din nou mai târziu."

    return jsonify({"response": response_text})

#model ai
MODEL_PATH = '/Users/alexiaserban/Documents/sistemDeRecomandare/model/mobilenet_skin_finetuned.keras'  
CLASS_NAMES = ['acne', 'dry', 'oil']
FRIENDLY_NAMES = {
    'acne': 'ACNEIC',
    'dry': 'USCAT',
    'oil': 'GRAS'
}

#pagina cu formularul analiza ten
@app.route('/analiza_tenului')
def analiza_tenului():
    return render_template('analiza_tenului.html')
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return "Nicio imagine încărcată", 400

    image = request.files['image']
    if image.filename == '':
        return "Nu a fost selectat niciun fișier", 400

    if image:
        #salveaza imaginea in static/uploads
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_path)

        #incarca modelul
        model = load_model(MODEL_PATH)

        # pregatesc imaginea pt predictie
        img = keras_image.load_img(image_path, target_size=(224, 224))
        img_array = keras_image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0  

        # Fac pred
        prediction = model.predict(img_array)
        predicted_class_raw = CLASS_NAMES[np.argmax(prediction)]
        predicted_class = FRIENDLY_NAMES[predicted_class_raw]

        return render_template(
            'analiza_tenului.html',
            uploaded_image=image.filename,
            predicted_class=predicted_class
        )

    return "Ceva n-a mers bine", 500
#quiz
@app.route("/beauty_quiz", methods=["GET", "POST"])
def beauty_quiz():
    rezultat = None

    if request.method == "POST":
        piele_dupa_curatare = request.form.get("piele_dupa_curatare")
        acnee = request.form.get("acnee")
        preocupare = request.form.get("preocupare")
        spf = request.form.get("spf")
        parfum = request.form.get("parfum")

        # prompt pentru OpenAI
        prompt = (
            f"Pe baza răspunsurilor de mai jos, oferă o recomandare de rutină de îngrijire personalizată pentru piele:\n"
            f"- Piele după curățare: {piele_dupa_curatare}\n"
            f"- Tendință de acnee: {acnee}\n"
            f"- Preocupare principală: {preocupare}\n"
            f"- Utilizare SPF: {spf}\n"
            f"- Preferință parfum: {parfum}\n\n"
            f"Scrie recomandarea într-un stil prietenos și profesionist."
        )

        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ești un consultant expert de beauty care oferă sfaturi personalizate de skincare."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            rezultat = completion.choices[0].message["content"]

        except Exception as e:
            print(f"Eroare OpenAI: {e}")
            rezultat = "Îmi pare rău, nu am putut genera o recomandare momentan."

    return render_template("beauty_quiz.html", rezultat=rezultat)

if __name__ == "__main__":
    app.run(debug=True, port=5001) 
