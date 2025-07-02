import pandas as pd
import numpy as np
import pymysql
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD

# Functie care intoarce lista de produse recomandate pentru un utilizato
def get_recommendations_for_user(username, k=2, n_components=2):
    username = username.strip() 

    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recomandare_produse"
    )

    # Extragem ratingurile
    query = "SELECT username, product_id, rating FROM reviews;"
    df = pd.read_sql(query, conn)
    # Daca utilizatorul nu are recenzii, oprim
    if username not in df['username'].unique():
        print(f"[INFO] Utilizatorul '{username}' nu are recenzii.")
        conn.close()
        return []

    # Construim matricea user-item
    ratings_matrix = df.pivot(index='username', columns='product_id', values='rating')
    # Daca utilizatorul a evaluat toate produsele, nu avem ce recomanda
    if ratings_matrix.loc[username].isna().sum() == 0:
        print(f"[INFO] Utilizatorul '{username}' a evaluat deja toate produsele.")
        conn.close()
        return []

    # ===== Memory-Based: Similaritate =====
    # Completam valorile lipsa cu 0 pentru cosine_similarity
    matrix_for_similarity = ratings_matrix.fillna(0)
    # Similaritate intre utilizatori (user-based)
    user_similarity_df = pd.DataFrame(
        cosine_similarity(matrix_for_similarity),
        index=matrix_for_similarity.index,
        columns=matrix_for_similarity.index
    )
    # Similaritate intre produse (item-based)
    item_similarity_df = pd.DataFrame(
        cosine_similarity(matrix_for_similarity.T),
        index=matrix_for_similarity.columns,
        columns=matrix_for_similarity.columns
    )
# Predictie user-based: folosim utilizatorii asemanatori care au evaluat acel produs
    def predict_user_based(user, item):
        other_users = ratings_matrix[ratings_matrix[item].notna()].index
        if other_users.empty:
            return np.nan
        sims = user_similarity_df.loc[user, other_users].sort_values(ascending=False).head(k)
        ratings = ratings_matrix.loc[sims.index, item]
        return np.dot(sims.values, ratings.values) / sims.sum() if sims.sum() != 0 else np.nan
  # Predictie item-based: folosim produse asemanatoare evaluate de user
    def predict_item_based(user, item):
        rated_items = ratings_matrix.loc[user].dropna().index
        if rated_items.empty:
            return np.nan
        sims = item_similarity_df.loc[item, rated_items].sort_values(ascending=False).head(k)
        ratings = ratings_matrix.loc[user, sims.index]
        return np.dot(sims.values, ratings.values) / sims.sum() if sims.sum() != 0 else np.nan

    # ===== Model-Based: SVD =====
    # Completam valorile lipsa cu media pe rand (utilizator)
    filled_matrix = ratings_matrix.apply(lambda row: row.fillna(row.mean()), axis=1)
    # Aplicam SVD
    svd = TruncatedSVD(n_components=n_components)
    svd_matrix = svd.fit_transform(filled_matrix)
    approx_matrix = np.dot(svd_matrix, svd.components_)
    svd_predicted = pd.DataFrame(approx_matrix, index=ratings_matrix.index, columns=ratings_matrix.columns)

    # ===== Predictie Hibrida =====
    predicted_ratings = {}
    for item in ratings_matrix.columns:
        if pd.isna(ratings_matrix.loc[username, item]):
            user_pred = predict_user_based(username, item)
            item_pred = predict_item_based(username, item)
            svd_pred = svd_predicted.loc[username, item]
# Folosim doar valorile valide (care nu sunt NaN)
            values = [v for v in [user_pred, item_pred, svd_pred] if pd.notna(v)]
            if values:
                final = np.mean(values)
                predicted_ratings[item] = final

    conn.close()

    if not predicted_ratings:
        print(f"[INFO] Nu s-au putut genera predictii pentru utilizatorul '{username}'.")
 # Sortam produsele dupa scorul estimat (descrescator)
    recommended = sorted(predicted_ratings.items(), key=lambda x: x[1], reverse=True)
    return [prod_id for prod_id, _ in recommended]
