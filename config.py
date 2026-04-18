import os


class DevelopmentConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///hearings.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
