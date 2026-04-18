from app import db
from app.models.hearing import Hearing


def create_hearing(title, date, transcript=None, agenda=None):
    hearing = Hearing(title=title, date=date, transcript=transcript, agenda=agenda)
    db.session.add(hearing)
    db.session.commit()
    return hearing


def get_hearing(hearing_id):
    return db.session.get(Hearing, hearing_id)


def list_hearings():
    return Hearing.query.order_by(Hearing.date.desc()).all()
