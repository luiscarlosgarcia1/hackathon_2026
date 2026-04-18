from datetime import datetime, timezone
from app import db


class PublicComment(db.Model):
    __tablename__ = "public_comments"

    id = db.Column(db.Integer, primary_key=True)
    hearing_id = db.Column(db.Integer, db.ForeignKey("hearings.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    cluster_id = db.Column(db.Integer, db.ForeignKey("comment_clusters.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "hearing_id": self.hearing_id,
            "body": self.body,
            "cluster_id": self.cluster_id,
            "created_at": self.created_at.isoformat(),
        }
