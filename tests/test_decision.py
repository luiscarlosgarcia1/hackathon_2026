from datetime import date
from unittest.mock import patch

import pytest

from app.services.hearing_service import create_hearing


@pytest.fixture
def hearing(app):
    with app.app_context():
        with patch("app.services.hearing_service._trigger_summary"):
            h = create_hearing("Budget Hearing", date(2026, 4, 18))
        yield h


def test_save_decision(test_client, app, hearing):
    with app.app_context():
        resp = test_client.post(
            f"/api/hearings/{hearing.id}/decision",
            json={"decision_text": "Approved with amendments.", "decision_date": "2026-05-01"},
        )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["decision_text"] == "Approved with amendments."
    assert data["decision_date"] == "2026-05-01"
    assert data["hearing_id"] == hearing.id


def test_save_decision_upserts(test_client, app, hearing):
    with app.app_context():
        test_client.post(
            f"/api/hearings/{hearing.id}/decision",
            json={"decision_text": "First draft."},
        )
        test_client.post(
            f"/api/hearings/{hearing.id}/decision",
            json={"decision_text": "Final decision."},
        )
        from app import db
        from app.models.government_decision import GovernmentDecision
        count = db.session.query(GovernmentDecision).filter_by(hearing_id=hearing.id).count()
    assert count == 1


def test_save_decision_missing_text_returns_400(test_client, app, hearing):
    with app.app_context():
        resp = test_client.post(f"/api/hearings/{hearing.id}/decision", json={})
    assert resp.status_code == 400


def test_save_decision_bad_date_returns_400(test_client, app, hearing):
    with app.app_context():
        resp = test_client.post(
            f"/api/hearings/{hearing.id}/decision",
            json={"decision_text": "OK", "decision_date": "not-a-date"},
        )
    assert resp.status_code == 400


def test_save_decision_unknown_hearing_returns_404(test_client, app):
    with app.app_context():
        resp = test_client.post(
            "/api/hearings/99999/decision",
            json={"decision_text": "Something"},
        )
    assert resp.status_code == 404


def test_get_decision(test_client, app, hearing):
    with app.app_context():
        test_client.post(
            f"/api/hearings/{hearing.id}/decision",
            json={"decision_text": "Motion passed."},
        )
        resp = test_client.get(f"/api/hearings/{hearing.id}/decision")
    assert resp.status_code == 200
    assert resp.get_json()["decision_text"] == "Motion passed."


def test_get_decision_404_no_decision(test_client, app, hearing):
    with app.app_context():
        resp = test_client.get(f"/api/hearings/{hearing.id}/decision")
    assert resp.status_code == 404


def test_get_decision_404_unknown_hearing(test_client, app):
    with app.app_context():
        resp = test_client.get("/api/hearings/99999/decision")
    assert resp.status_code == 404
