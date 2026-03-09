import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EPOS_API_KEY = os.environ.get('EPOS_API_KEY')
    EPOS_API_SECRET = os.environ.get('EPOS_API_SECRET')
    
    # Apple Wallet Pass Configuration
    APPLE_TEAM_ID = os.environ.get('APPLE_TEAM_ID')
    PASS_TYPE_ID = os.environ.get('PASS_TYPE_ID')
    PASS_CERT_PASSWORD = os.environ.get('PASS_CERT_PASSWORD', '')
    
    # Google Wallet Pass Configuration
    GOOGLE_WALLET_ISSUER_ID = os.environ.get('GOOGLE_WALLET_ISSUER_ID')
    GOOGLE_WALLET_CLASS_ID = os.environ.get('GOOGLE_WALLET_CLASS_ID')
