from datetime import datetime, timezone
from app import db


class CommentCluster(db.Model):
    __tablename__ = "comment_clusters"

    id = db.Column(db.Integer, primary_key=True)
    hearing_id = db.Column(db.Integer, db.ForeignKey("hearings.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    comments = db.relationship("PublicComment", backref="cluster", lazy="select")

    @property
    def comment_count(self):
        return len(self.comments)

    def to_dict(self):
        return {
            "id": self.id,
            "hearing_id": self.hearing_id,
            "name": self.name,
            "description": self.description,
            "comment_count": self.comment_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
