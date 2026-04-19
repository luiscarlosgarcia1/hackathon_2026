from datetime import datetime, timezone
from app import db


class PublicComment(db.Model):
    __tablename__ = "public_comments"

    id = db.Column(db.Integer, primary_key=True)
    hearing_id = db.Column(db.Integer, db.ForeignKey("hearings.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    cluster_id = db.Column(db.Integer, db.ForeignKey("comment_clusters.id"), nullable=True)
    # NULL = fully anonymous; set when a logged-in user posts with their identity
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    # Used when commenter provides a name without having an account
    author_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    author = db.relationship("User", back_populates="comments", foreign_keys=[author_id])

    def to_dict(self):
        return {
            "id": self.id,
            "hearing_id": self.hearing_id,
            "body": self.body,
            "cluster_id": self.cluster_id,
            "author_id": self.author_id,
            "author_name": self.author_name or (self.author.name if self.author else None),
            "created_at": self.created_at.isoformat(),
        }
