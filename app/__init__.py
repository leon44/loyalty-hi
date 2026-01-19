from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from config import Config

db = SQLAlchemy()
csrf = CSRFProtect()

def create_app(config_class=Config):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    csrf.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    from app.wallet import bp as wallet_bp
    app.register_blueprint(wallet_bp)

    with app.app_context():
        db.create_all()

    return app
