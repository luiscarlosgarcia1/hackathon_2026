import logging
import threading

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
logger = logging.getLogger(__name__)


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)

    with app.app_context():
        from app.models import hearing, hearing_summary  # noqa: F401 — ensures models are registered
        db.create_all()

        from app.routes.web import web_bp
        from app.routes.api import api_bp
        app.register_blueprint(web_bp)
        app.register_blueprint(api_bp, url_prefix="/api")

    _start_background_summarizer(app)

    return app


def _start_background_summarizer(app):
    def run():
        with app.app_context():
            from app.models.hearing import Hearing
            from app.models.hearing_summary import HearingSummary
            from app.services.summary_orchestrator import run_summary

            unsummarized = (
                db.session.query(Hearing)
                .outerjoin(HearingSummary, Hearing.id == HearingSummary.hearing_id)
                .filter(HearingSummary.id.is_(None))
                .all()
            )

            for h in unsummarized:
                try:
                    logger.info("Background summarizer: generating summary for hearing %d", h.id)
                    run_summary(h.id)
                except Exception:
                    logger.exception("Background summarizer: failed for hearing %d", h.id)

    t = threading.Thread(target=run, daemon=True)
    t.start()
