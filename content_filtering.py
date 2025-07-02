import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.metrics.pairwise import cosine_similarity

# conectare la baza de date MySQL
engine = create_engine("mysql+pymysql://root:@localhost/recomandare_produse")

# Functie pentru a obtine profilul unui utilizator dupa ID
def get_user_profile(user_id):
    query = f"SELECT * FROM profil_utilizator WHERE user_id = {user_id}"
    user_df = pd.read_sql(query, engine)
    return user_df.iloc[0]
# Functie pentru a extrage toate produsele din baza de date
def get_products():
    query = "SELECT * FROM produse"
    products_df = pd.read_sql(query, engine)
    return products_df

def get_user_favorites(user_id):
    query = f"""
    SELECT p.* FROM produse p
    JOIN favorite f ON f.product_id = p.id
    WHERE f.user_id = {user_id}
    """
    favorites_df = pd.read_sql(query, engine)
    return favorites_df

def vectorize_user(user_profile):
    """
    Vectorizeaza caracteristicile utilizatorului
    """
    return {
        'tip_ten': user_profile['tip_ten'].strip().lower(),
        'textura': [user_profile['textura'].strip().lower()] if user_profile['textura'] else [],
        'alergii': [a.strip().lower() for a in user_profile['alergii'].split(',')] if user_profile['alergii'] else []
    }

def vectorize_products(products_df):
    """
    Vectorizează caracteristicile fiecarui produs.
    """
    products_features = []
    for _, row in products_df.iterrows():
        features = {
            'tip_ten': row['skin_type'].strip().lower() if pd.notna(row['skin_type']) else '',
            'textura': [row['textura'].strip().lower()] if pd.notna(row['textura']) else [],
            'alergii': [a.strip().lower() for a in row['alergeni'].split(',')] if pd.notna(row['alergeni']) else []
        }
        products_features.append(features)
    return products_features
# Functia principala de recomandare
def recomanda_produse(user_id, top_n=10):
    #Extragem datele
    user_profile = get_user_profile(user_id)
    products_df = get_products()

    # Vectorizam
    user_features = vectorize_user(user_profile)
    products_features = vectorize_products(products_df)

    # lista completa de caracteristici
    all_skin_types = list(set([f['tip_ten'] for f in products_features] + [user_features['tip_ten']]))
    all_textures = set()
    for f in products_features:
        all_textures.update(f['textura'])
    all_textures.update(user_features['textura'])
    all_textures = list(all_textures)
    all_allergies = set()
    for f in products_features:
        all_allergies.update(f['alergii'])
    all_allergies.update(user_features['alergii'])
    all_allergies = list(all_allergies)

    # codare binara
    def binarize_feature(values, all_values):
        return [1 if val in values else 0 for val in all_values]

    #Vector utilizator
    user_vector = (
        binarize_feature([user_features['tip_ten']], all_skin_types) +
        binarize_feature(user_features['textura'], all_textures) +
        binarize_feature(user_features['alergii'], all_allergies)
    )

    #Vectori produse
    product_vectors = []
    for f in products_features:
        vector = (
            binarize_feature([f['tip_ten']], all_skin_types) +
            binarize_feature(f['textura'], all_textures) +
            binarize_feature(f['alergii'], all_allergies)
        )
        product_vectors.append(vector)

    # Similaritate
    similarity_scores = cosine_similarity([user_vector], product_vectors)[0]

    # Adaug scorurile în dataFrame si sortez
    products_df = products_df.copy()
    products_df['similarity_score'] = similarity_scores
    products_df = products_df.sort_values(by='similarity_score', ascending=False)

    # Returnam doar top N produse 
    return products_df.head(top_n)

# Testare
if __name__ == "__main__":
    df = recomanda_produse(user_id=8, top_n=10)
    print(df[['product_name', 'similarity_score']])
