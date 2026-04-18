import logging

from app import db
from app.models.hearing import Hearing

logger = logging.getLogger(__name__)


def create_hearing(title, date, transcript=None, agenda=None):
    hearing = Hearing(title=title, date=date, transcript=transcript, agenda=agenda)
    db.session.add(hearing)
    db.session.commit()

    _trigger_summary(hearing.id)
    return hearing


def get_hearing(hearing_id):
    return db.session.get(Hearing, hearing_id)


def list_hearings():
    return Hearing.query.order_by(Hearing.date.desc()).all()


def _trigger_summary(hearing_id: int) -> None:
    try:
        from app.services.summary_orchestrator import run_summary
        run_summary(hearing_id)
    except Exception:
        logger.exception("Summarization failed for hearing %d — hearing saved successfully", hearing_id)
