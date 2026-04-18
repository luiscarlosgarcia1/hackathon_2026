from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)

    with app.app_context():
        from app.models import hearing  # noqa: F401 — ensures model is registered
        db.create_all()

        from app.routes.web import web_bp
        from app.routes.api import api_bp
        app.register_blueprint(web_bp)
        app.register_blueprint(api_bp, url_prefix="/api")

    return app
