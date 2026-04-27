from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .config import config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(env='production'):
    app = Flask(__name__)
    app.config.from_object(config[env])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))

    from .routes import auth, webhook, panel, musteri
    app.register_blueprint(auth.bp)
    app.register_blueprint(webhook.bp)
    app.register_blueprint(panel.bp)
    app.register_blueprint(musteri.bp)

    return app
