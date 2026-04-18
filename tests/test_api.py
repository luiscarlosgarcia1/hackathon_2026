import json
from datetime import date
from app.services.hearing_service import create_hearing


def test_post_creates_hearing(test_client, app):
    with app.app_context():
        resp = test_client.post(
            "/api/hearings",
            data=json.dumps({"title": "API Test Hearing", "date": "2026-05-01"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "API Test Hearing"
        assert data["date"] == "2026-05-01"
        assert "id" in data


def test_post_missing_title_returns_400(test_client, app):
    with app.app_context():
        resp = test_client.post(
            "/api/hearings",
            data=json.dumps({"date": "2026-05-01"}),
            content_type="application/json",
        )
        assert resp.status_code == 400


def test_get_list_returns_all_hearings(test_client, app):
    with app.app_context():
        create_hearing("Hearing A", date(2026, 1, 10))
        create_hearing("Hearing B", date(2026, 2, 20))
        resp = test_client.get("/api/hearings")
        assert resp.status_code == 200
        data = resp.get_json()
        titles = {h["title"] for h in data}
        assert "Hearing A" in titles
        assert "Hearing B" in titles


def test_get_by_id_returns_hearing(test_client, app):
    with app.app_context():
        h = create_hearing("Detail Hearing", date(2026, 3, 15))
        resp = test_client.get(f"/api/hearings/{h.id}")
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "Detail Hearing"


def test_get_unknown_id_returns_404(test_client, app):
    with app.app_context():
        resp = test_client.get("/api/hearings/99999")
        assert resp.status_code == 404
