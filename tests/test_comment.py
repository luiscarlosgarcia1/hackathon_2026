from datetime import date
from unittest.mock import patch

import pytest

from app.services.comment_service import create_comment
from app.services.hearing_service import create_hearing


@pytest.fixture
def hearing(app):
    with app.app_context():
        with patch("app.services.hearing_service._trigger_summary"):
            h = create_hearing("Test Hearing", date(2026, 4, 18))
        yield h


def test_create_comment(app, hearing):
    with app.app_context():
        comment = create_comment(hearing.id, "This road needs more lighting.")
        assert comment.id is not None
        assert comment.hearing_id == hearing.id
        assert comment.body == "This road needs more lighting."


def test_create_comment_unknown_hearing_raises(app):
    with app.app_context():
        with pytest.raises(ValueError, match="not found"):
            create_comment(99999, "Some comment")


def test_comment_api_post(test_client, app, hearing):
    with app.app_context():
        resp = test_client.post(
            f"/api/hearings/{hearing.id}/comments",
            json={"body": "Please fix the potholes."},
        )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["body"] == "Please fix the potholes."
    assert data["hearing_id"] == hearing.id


def test_comment_api_missing_body_returns_400(test_client, app, hearing):
    with app.app_context():
        resp = test_client.post(f"/api/hearings/{hearing.id}/comments", json={})
    assert resp.status_code == 400


def test_comment_api_unknown_hearing_returns_404(test_client, app):
    with app.app_context():
        resp = test_client.post(
            "/api/hearings/99999/comments", json={"body": "Hello"}
        )
    assert resp.status_code == 404
