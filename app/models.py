import datetime
from app import db


class RateLimit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), nullable=False, index=True) # e.g., 'email:user@example.com' or 'ip:127.0.0.1'
    count = db.Column(db.Integer, default=1)
    window_start = db.Column(db.DateTime, default=datetime.datetime.utcnow)
