import pytest
import datetime
import hashlib
import secrets
from app import create_app, db
from app.models import MagicLinkToken
from config import Config
from flask import session

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
    with app.app_context():
        db.drop_all()

def test_magic_link_creation_and_expiry(client):
    """Test that a magic link is created and expires correctly."""
    with client.application.app_context():
        # 1. Request a magic link
        response = client.post('/login', data={'email': 'test@example.com'})
        assert response.status_code == 302 # Redirect to check_inbox

        # 2. Check the token in the database
        token_entry = MagicLinkToken.query.filter_by(email='test@example.com').first()
        assert token_entry is not None
        assert token_entry.is_valid()

        # 3. Simulate token expiry
        token_entry.expires_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        db.session.commit()
        assert not token_entry.is_valid()

def test_magic_link_single_use(client):
    """Test that a magic link can only be used once."""
    with client.application.app_context():
        # 1. Create a valid token
        email = 'single-use@example.com'
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        new_token = MagicLinkToken(
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
            request_ip='127.0.0.1',
            user_agent='pytest'
        )
        db.session.add(new_token)
        db.session.commit()

        # 2. Use the link for the first time
        response = client.get(f'/login/verify/{token}')
        assert response.status_code == 302 # Redirect to dashboard
        assert response.location == '/dashboard'
        
        # Verify session is created
        with client.session_transaction() as sess:
            assert sess['user_email'] == email

        # 3. Check that the token is marked as used
        used_token = MagicLinkToken.query.filter_by(token_hash=token_hash).first()
        assert used_token.used_at is not None
        assert not used_token.is_valid()

        # 4. Try to use the link again
        response2 = client.get(f'/login/verify/{token}')
        assert response2.status_code == 302 # Redirect to login
        assert response2.location == '/login'

def test_login_session_creation(client):
    """Test that a valid magic link creates a persistent session."""
    with client.application.app_context():
        email = 'session@example.com'
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        new_token = MagicLinkToken(
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
            request_ip='127.0.0.1',
            user_agent='pytest'
        )
        db.session.add(new_token)
        db.session.commit()

        # Use the link to log in
        client.get(f'/login/verify/{token}')

        # Check that the session is created and the user is on the dashboard
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Your Profile' in response.data

        # Check session cookie details
        with client.session_transaction() as sess:
            assert sess.permanent
