import logging

from app import db
from app.models.hearing_summary import HearingSummary
from app.services.hearing_service import get_hearing
from app.services.summarization_service import summarize_hearing

logger = logging.getLogger(__name__)


def run_summary(hearing_id: int) -> HearingSummary:
    hearing = get_hearing(hearing_id)
    if hearing is None:
        raise ValueError(f"Hearing {hearing_id} not found")

    summary_data = summarize_hearing(hearing)

    summary = db.session.query(HearingSummary).filter_by(hearing_id=hearing_id).first()
    if summary is None:
        summary = HearingSummary(hearing_id=hearing_id)
        db.session.add(summary)

    summary.issue_description = summary_data["issue_description"]
    summary.stakeholders = summary_data["stakeholders"]
    summary.key_arguments = summary_data["key_arguments"]
    summary.community_impact = summary_data["community_impact"]

    db.session.commit()
    return summary
