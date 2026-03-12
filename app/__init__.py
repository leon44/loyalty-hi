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

    from app.google_wallet import bp as google_wallet_bp
    app.register_blueprint(google_wallet_bp)

    # Context processor to detect in-app webview
    @app.context_processor
    def inject_is_in_app():
        from flask import request
        import logging
        user_agent = request.user_agent.string.lower() if request.user_agent else ''
        is_in_app = 'loyaltyapp' in user_agent
        if is_in_app:
            logging.info(f'IN-APP DETECTED: User-Agent contains "loyaltyapp" - hiding header')
        return dict(is_in_app=is_in_app)

    with app.app_context():
        db.create_all()

    return app
