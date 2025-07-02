import pytest
import mysql.connector
import bcrypt

@pytest.fixture
def create_user():
    def _create_user(email='exist@example.com', password='parola_corecta'):
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="recomandare_produse"
        )
        cursor = db.cursor(dictionary=True)
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "INSERT IGNORE INTO users (username, email, password) VALUES (%s, %s, %s)",
            ('testuser', email, hashed_password)
        )
        db.commit()
        cursor.close()
        db.close()
    return _create_user
def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200

def test_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200

def test_produse_page(client):
    response = client.get('/produse')
    assert response.status_code == 200

def test_favorite_page(client):
    response = client.get('/favorite', follow_redirects=True)
    assert response.status_code == 200

def test_rutina_mea_page(client):
    response = client.get('/rutina_mea', follow_redirects=True)
    assert response.status_code == 200

def test_profile_page(client):
    response = client.get('/profile', follow_redirects=True)
    assert response.status_code == 200

def test_analiza_tenului_page(client):
    response = client.get('/analiza_tenului')
    assert response.status_code == 200

def test_beauty_quiz_page(client):
    response = client.get('/beauty_quiz')
    assert response.status_code == 200

def test_recomandari_ten_page(client):
    response = client.get('/recomandari_ten/uscat', follow_redirects=True)
    assert response.status_code == 200

def test_recomandari_api(client):
    response = client.get('/recomandari/uscat')
    assert response.status_code == 200 or response.status_code == 302  

def test_cautare_api(client):
    response = client.get('/cautare?query=test')
    assert response.status_code == 200
    assert response.is_json

def test_chatbot_api(client):
    response = client.post('/chatbot', json={'message': 'Ce îmi recomanzi pentru ten uscat?'}, follow_redirects=True)
    assert response.status_code == 200
    assert response.is_json
    assert 'response' in response.get_json()

def test_logout(client):
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
import io

def test_upload_image(client):
    with open('tests/test_image.png', 'rb') as img_file:
        data = {
            'image': (img_file, 'test_image.jpg')
        }
        response = client.post('/upload_image', data=data, content_type='multipart/form-data')
        assert response.status_code in [200, 500]  

def test_beauty_quiz_post(client):
    data = {
        'piele_dupa_curatare': 'uscata',
        'acnee': 'nu',
        'preocupare': 'riduri',
        'spf': 'da',
        'parfum': 'nu'
    }
    response = client.post('/beauty_quiz', data=data, follow_redirects=True)
    assert response.status_code == 200

def test_toggle_favorite_not_logged_in(client):
    data = {
        'product_id': 1,
        'action': 'add'
    }
    response = client.post('/toggle_favorite', json=data)
    assert response.status_code == 401
    assert response.is_json
    assert 'error' in response.get_json()

def test_profile_post_not_logged_in(client):
    data = {
        'nume': 'Test User',
        'varsta': '25',
        'gen': 'feminin',
        'tip_ten': 'uscat',
        'alergii': 'parfum',
        'textura': 'usoara'
    }
    response = client.post('/profile', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Autentificare' in response.data or b'Login' in response.data

def test_adauga_in_rutina_not_logged_in(client):
    data = {
        'product_id': '1',
        'product_type': 'cleanser'
    }
    response = client.post('/adauga_in_rutina', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Autentificare' in response.data or b'Login' in response.data

def test_favorite_page_logged_in(client, login):
    login()  
    response = client.get('/favorite')
    assert response.status_code == 200
    assert b'Favorite' in response.data or b'favorite' in response.data

def test_toggle_favorite_logged_in(client, login):
    login()  

    data = {
        'product_id': 1,  
        'action': 'add'
    }

    response = client.post('/toggle_favorite', json=data)
    assert response.status_code == 200
    assert response.is_json
    assert 'success' in response.get_json()
    assert response.get_json()['success'] == True

def test_login_page_content(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Autentificare' in response.data or b'Login' in response.data
def test_login_post_valid(client, create_user):
    create_user()
    data = {"email": "exist@example.com", "password": "parola_corecta"}
    response = client.post('/login', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/'


def test_sterge_din_rutina_not_logged_in(client):
    data = {
        'product_id': '1'
    }
    response = client.post('/sterge_din_rutina', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Autentificare' in response.data or b'Login' in response.data
def test_sterge_din_rutina_logged_in(client, login):
    login()
    data = {
        'product_id': '1'
    }
    response = client.post('/sterge_din_rutina', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Rutina mea' in response.data or b'Rutina' in response.data or b'Profilul Meu' in response.data

def test_profile_post_logged_in(client, login):
    login()  
    data = {
        'nume': 'Test User',
        'varsta': '25',
        'gen': 'feminin',
        'tip_ten': 'uscat',
        'alergii': 'parfum',
        'textura': 'usoara'
    }
    response = client.post('/profile', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Profilul Meu' in response.data or b'Profil' in response.data

def test_adauga_in_rutina_logged_in(client, login):
    login()  
    data = {
        'product_id': '1',  
        'product_type': 'cleanser'  
    }
    response = client.post('/adauga_in_rutina', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Rutina mea' in response.data or b'Rutina' in response.data

def test_toggle_favorite_remove_logged_in(client, login):
    login()  

    data_add = {
        'product_id': 1,  
        'action': 'add'
    }

    response_add = client.post('/toggle_favorite', json=data_add)
    assert response_add.status_code == 200
    assert response_add.is_json
    assert response_add.get_json()['success'] == True

    data_remove = {
        'product_id': 1, 
        'action': 'remove'
    }

    response_remove = client.post('/toggle_favorite', json=data_remove)
    assert response_remove.status_code == 200
    assert response_remove.is_json
    assert response_remove.get_json()['success'] == True

def test_product_page_get(client):
    response = client.get('/product/1', follow_redirects=True)
    assert response.status_code == 200
    assert b'Produsul' in response.data or b'produs' in response.data

def test_product_page_post_review_logged_in(client, login):
    login()
    data = {
        'rating': '5',
        'review_text': 'Test review automat'
    }
    response = client.post('/product/1', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Produsul' in response.data or b'produs' in response.data

def test_product_page_404(client):
    response = client.get('/product/99999', follow_redirects=True)
    assert response.status_code == 404
def test_product_post_without_login(client):
    data = {
        'rating': '5',
        'review_text': 'Test review fara login'
    }
    response = client.post('/product/1', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert 'Autentificare' in response.data.decode('utf-8') or 'Login' in response.data.decode('utf-8')

def test_upload_image_no_file(client):
    response = client.post('/upload_image', data={}, content_type='multipart/form-data')
    assert response.status_code == 400

def test_genereaza_rutina_ai_logged_in(client, login):
    login()  

    response = client.post('/genereaza_rutina_ai', follow_redirects=True)
    assert response.status_code == 200
    assert 'Rutina mea' in response.data.decode('utf-8') or 'Rutina' in response.data.decode('utf-8') or 'Profilul Meu' in response.data.decode('utf-8')
