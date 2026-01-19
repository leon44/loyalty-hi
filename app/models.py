import datetime
from app import db

class MagicLinkToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    token_hash = db.Column(db.String(128), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    request_ip = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(200), nullable=False)

    def is_valid(self):
        return self.used_at is None and self.expires_at > datetime.datetime.utcnow()

class RateLimit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), nullable=False, index=True) # e.g., 'email:user@example.com' or 'ip:127.0.0.1'
    count = db.Column(db.Integer, default=1)
    window_start = db.Column(db.DateTime, default=datetime.datetime.utcnow)
