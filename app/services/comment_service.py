from app import db
from app.models.hearing import Hearing
from app.models.public_comment import PublicComment


def create_comment(hearing_id: int, body: str) -> PublicComment:
    hearing = db.session.get(Hearing, hearing_id)
    if hearing is None:
        raise ValueError(f"Hearing {hearing_id} not found")
    comment = PublicComment(hearing_id=hearing_id, body=body)
    db.session.add(comment)
    db.session.commit()
    return comment
