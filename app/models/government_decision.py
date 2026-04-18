from datetime import datetime, timezone
from app import db


class GovernmentDecision(db.Model):
    __tablename__ = "government_decisions"

    id = db.Column(db.Integer, primary_key=True)
    hearing_id = db.Column(db.Integer, db.ForeignKey("hearings.id"), nullable=False, unique=True)
    decision_text = db.Column(db.Text, nullable=False)
    decision_date = db.Column(db.Date, nullable=True)
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "hearing_id": self.hearing_id,
            "decision_text": self.decision_text,
            "decision_date": self.decision_date.isoformat() if self.decision_date else None,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
