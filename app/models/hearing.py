from datetime import datetime, timezone
from app import db


class Hearing(db.Model):
    __tablename__ = "hearings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    transcript = db.Column(db.Text, nullable=True)
    agenda = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    summary = db.relationship("HearingSummary", backref="hearing", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat(),
            "transcript": self.transcript,
            "agenda": self.agenda,
            "created_at": self.created_at.isoformat(),
        }
