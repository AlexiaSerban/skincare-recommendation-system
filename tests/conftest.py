import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '/Users/alexiaserban/Documents/sistemDeRecomandare/')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def login(client):
    def do_login():
        return client.post('/login', data={
            'email': 'test@example.com',
            'password': 'test123'
        }, follow_redirects=True)
    return do_login
