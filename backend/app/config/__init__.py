import os


class Base:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    META_WEBHOOK_VERIFY_TOKEN = os.environ.get('META_WEBHOOK_VERIFY_TOKEN', '')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')


class Development(Base):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///emlakisim.db')


class Production(Base):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '')


config = {
    'development': Development,
    'production': Production,
}
