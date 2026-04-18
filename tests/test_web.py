from datetime import date
from app.services.hearing_service import create_hearing


def test_list_page_returns_200(test_client, app):
    with app.app_context():
        create_hearing("Web List Hearing", date(2026, 4, 10))
        resp = test_client.get("/hearings")
        assert resp.status_code == 200
        assert b"Web List Hearing" in resp.data


def test_detail_page_returns_200(test_client, app):
    with app.app_context():
        h = create_hearing("Detail Page Hearing", date(2026, 4, 11), transcript="Some transcript")
        resp = test_client.get(f"/hearings/{h.id}")
        assert resp.status_code == 200
        assert b"Detail Page Hearing" in resp.data
        assert b"Some transcript" in resp.data


def test_detail_unknown_returns_404(test_client, app):
    with app.app_context():
        resp = test_client.get("/hearings/99999")
        assert resp.status_code == 404


def test_new_hearing_post_redirects_to_detail(test_client, app):
    with app.app_context():
        resp = test_client.post(
            "/hearings/new",
            data={"title": "Form Hearing", "date": "2026-06-01"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/hearings/" in resp.headers["Location"]


def test_new_hearing_post_missing_title_rerenders_form(test_client, app):
    with app.app_context():
        resp = test_client.post(
            "/hearings/new",
            data={"title": "", "date": "2026-06-01"},
        )
        assert resp.status_code == 200
        assert b"Title is required" in resp.data
