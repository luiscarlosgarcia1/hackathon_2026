from datetime import date
from unittest.mock import patch

import pytest

from app.services.accountability_service import compare_decision_to_clusters
from app.services.comment_service import create_comment
from app.services.hearing_service import create_hearing


MOCK_AI_RESULT = '{"alignment": "partial", "reasoning": "The decision addressed noise but ignored safety."}'

CLUSTERS = [
    {"name": "Safety", "description": "Road safety.", "comment_count": 3},
    {"name": "Noise", "description": "Noise pollution.", "comment_count": 2},
]


@pytest.fixture
def hearing_with_decision(app, test_client):
    with app.app_context():
        with patch("app.services.hearing_service._trigger_summary"):
            h = create_hearing("Zoning Hearing", date(2026, 4, 18))
        test_client.post(
            f"/api/hearings/{h.id}/decision",
            json={"decision_text": "Rezoning approved."},
        )
        yield h


@pytest.fixture
def hearing_with_clusters(app, test_client, hearing_with_decision):
    h = hearing_with_decision
    with app.app_context():
        c1 = create_comment(h.id, "The intersection is dangerous.")
        c2 = create_comment(h.id, "Night noise is unbearable.")
        mock_data = [
            {"name": "Safety", "description": "Safety.", "comment_ids": [c1.id]},
            {"name": "Noise", "description": "Noise.", "comment_ids": [c2.id]},
        ]
        with patch("app.services.cluster_orchestrator.cluster_comments", return_value=mock_data):
            from app.services.cluster_orchestrator import run_clustering
            run_clustering(h.id)
    yield h


# --- accountability_service (pure, mocked Groq) ---

def test_compare_decision_returns_alignment():
    with patch("app.services.accountability_service.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = MOCK_AI_RESULT
        result = compare_decision_to_clusters("Rezoning approved.", CLUSTERS, summary=None)
    assert result["alignment"] == "partial"
    assert "noise" in result["reasoning"].lower()


def test_compare_decision_includes_summary_context():
    summary = {"issue_description": "Housing shortage", "key_arguments": "Density needed"}
    with patch("app.services.accountability_service.Groq") as MockGroq:
        mock_create = MockGroq.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = (
            '{"alignment": "aligned", "reasoning": "Decision aligns with housing needs."}'
        )
        result = compare_decision_to_clusters("Approve high-density zoning.", CLUSTERS, summary=summary)
        call_args = mock_create.call_args
        user_content = call_args[1]["messages"][1]["content"]
    assert "Housing shortage" in user_content
    assert result["alignment"] == "aligned"


def test_compare_decision_rejects_invalid_alignment():
    with patch("app.services.accountability_service.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = '{"alignment": "unknown_value", "reasoning": "Something."}'
        with pytest.raises(ValueError, match="invalid alignment"):
            compare_decision_to_clusters("Some decision.", CLUSTERS, summary=None)


def test_compare_decision_rejects_missing_keys():
    with patch("app.services.accountability_service.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = '{"alignment": "aligned"}'
        with pytest.raises(ValueError, match="missing keys"):
            compare_decision_to_clusters("Some decision.", CLUSTERS, summary=None)


# --- API endpoints ---

def test_accountability_api_post(test_client, app, hearing_with_clusters):
    h = hearing_with_clusters
    with app.app_context():
        with patch("app.services.accountability_service.Groq") as MockGroq:
            MockGroq.return_value.chat.completions.create.return_value.choices[
                0
            ].message.content = MOCK_AI_RESULT
            resp = test_client.post(f"/api/hearings/{h.id}/accountability")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["alignment"] == "partial"
    assert data["hearing_id"] == h.id


def test_accountability_api_upserts(test_client, app, hearing_with_clusters):
    h = hearing_with_clusters
    first = '{"alignment": "aligned", "reasoning": "First run."}'
    second = '{"alignment": "diverged", "reasoning": "Second run."}'
    with app.app_context():
        with patch("app.services.accountability_service.Groq") as MockGroq:
            MockGroq.return_value.chat.completions.create.return_value.choices[
                0
            ].message.content = first
            test_client.post(f"/api/hearings/{h.id}/accountability")
        with patch("app.services.accountability_service.Groq") as MockGroq:
            MockGroq.return_value.chat.completions.create.return_value.choices[
                0
            ].message.content = second
            test_client.post(f"/api/hearings/{h.id}/accountability")
        from app import db
        from app.models.accountability_summary import AccountabilitySummary
        count = db.session.query(AccountabilitySummary).filter_by(hearing_id=h.id).count()
    assert count == 1


def test_accountability_api_409_no_decision(test_client, app):
    with app.app_context():
        with patch("app.services.hearing_service._trigger_summary"):
            h = create_hearing("No Decision Yet", date(2026, 4, 18))
        resp = test_client.post(f"/api/hearings/{h.id}/accountability")
    assert resp.status_code == 409


def test_accountability_api_409_no_clusters(test_client, app, hearing_with_decision):
    h = hearing_with_decision
    with app.app_context():
        resp = test_client.post(f"/api/hearings/{h.id}/accountability")
    assert resp.status_code == 409


def test_accountability_api_404_unknown_hearing(test_client, app):
    with app.app_context():
        resp = test_client.post("/api/hearings/99999/accountability")
    assert resp.status_code == 404


def test_get_accountability(test_client, app, hearing_with_clusters):
    h = hearing_with_clusters
    with app.app_context():
        with patch("app.services.accountability_service.Groq") as MockGroq:
            MockGroq.return_value.chat.completions.create.return_value.choices[
                0
            ].message.content = MOCK_AI_RESULT
            test_client.post(f"/api/hearings/{h.id}/accountability")
        resp = test_client.get(f"/api/hearings/{h.id}/accountability")
    assert resp.status_code == 200
    assert resp.get_json()["alignment"] == "partial"


def test_get_accountability_404_not_run(test_client, app, hearing_with_decision):
    h = hearing_with_decision
    with app.app_context():
        resp = test_client.get(f"/api/hearings/{h.id}/accountability")
    assert resp.status_code == 404
