import os


def _get_database_url():
    url = os.environ.get("DATABASE_URL", "sqlite:///hearings.db")
    # Railway (and legacy Heroku) emit postgres:// which SQLAlchemy 2.x rejects
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = _get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True


class DevelopmentConfig(Config):
    pass