import json


def test_full_happy_path(test_client, app):
    with app.app_context():
        # Create via API
        resp = test_client.post(
            "/api/hearings",
            data=json.dumps({
                "title": "Integration Test Hearing",
                "date": "2026-07-04",
                "transcript": "Full integration transcript.",
                "agenda": "Item 1\nItem 2",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201
        hearing_id = resp.get_json()["id"]

        # Fetch by ID via API
        resp = test_client.get(f"/api/hearings/{hearing_id}")
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "Integration Test Hearing"

        # Appears in list via API
        resp = test_client.get("/api/hearings")
        assert resp.status_code == 200
        ids = [h["id"] for h in resp.get_json()]
        assert hearing_id in ids

        # Detail page loads via web
        resp = test_client.get(f"/hearings/{hearing_id}")
        assert resp.status_code == 200
        assert b"Integration Test Hearing" in resp.data
