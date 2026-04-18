import json
from datetime import date
from unittest.mock import patch

import pytest

from app.models.hearing_summary import HearingSummary
from app.services.hearing_service import create_hearing
from app.services.summary_orchestrator import run_summary

MOCK_SUMMARY = {
    "issue_description": "Test issue",
    "stakeholders": "Group A, Group B",
    "key_arguments": "Argument one. Argument two.",
    "community_impact": "Significant local impact.",
}


@pytest.fixture
def hearing(app):
    with app.app_context():
        with patch("app.services.hearing_service._trigger_summary"):
            h = create_hearing("Test Hearing", date(2026, 4, 18), agenda="Agenda text")
        yield h


def test_run_summary_creates_summary(app, hearing):
    with app.app_context():
        with patch(
            "app.services.summary_orchestrator.summarize_hearing",
            return_value=MOCK_SUMMARY,
        ):
            summary = run_summary(hearing.id)
        data = summary.to_dict()

    assert data["issue_description"] == "Test issue"
    assert data["stakeholders"] == "Group A, Group B"
    assert data["key_arguments"] == "Argument one. Argument two."
    assert data["community_impact"] == "Significant local impact."


def test_run_summary_upserts_on_rerun(app, hearing):
    with app.app_context():
        with patch(
            "app.services.summary_orchestrator.summarize_hearing",
            return_value=MOCK_SUMMARY,
        ):
            run_summary(hearing.id)

        updated = {**MOCK_SUMMARY, "issue_description": "Updated issue"}
        with patch(
            "app.services.summary_orchestrator.summarize_hearing",
            return_value=updated,
        ):
            summary = run_summary(hearing.id)

        from app import db
        count = db.session.query(HearingSummary).filter_by(hearing_id=hearing.id).count()
        assert count == 1
        assert summary.issue_description == "Updated issue"


def test_run_summary_raises_for_missing_hearing(app):
    with app.app_context():
        with pytest.raises(ValueError, match="not found"):
            run_summary(99999)


def test_summarize_endpoint_returns_summary(test_client, app, hearing):
    with app.app_context():
        with patch(
            "app.services.summary_orchestrator.summarize_hearing",
            return_value=MOCK_SUMMARY,
        ):
            resp = test_client.post(f"/api/hearings/{hearing.id}/summarize")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["issue_description"] == "Test issue"
    assert data["hearing_id"] == hearing.id


def test_summarize_endpoint_404_unknown_hearing(test_client, app):
    with app.app_context():
        resp = test_client.post("/api/hearings/99999/summarize")
    assert resp.status_code == 404


def test_summarize_endpoint_422_on_ai_failure(test_client, app, hearing):
    with app.app_context():
        with patch(
            "app.services.summary_orchestrator.summarize_hearing",
            side_effect=ValueError("unparseable response"),
        ):
            resp = test_client.post(f"/api/hearings/{hearing.id}/summarize")

    assert resp.status_code == 422
    assert "error" in resp.get_json()


def test_create_hearing_survives_summarization_failure(app):
    with app.app_context():
        with patch(
            "app.services.summarization_service.summarize_hearing",
            side_effect=ValueError("AI down"),
        ):
            hearing = create_hearing("Resilient Hearing", date(2026, 4, 18))

        assert hearing.id is not None
