from datetime import date
from unittest.mock import patch

import pytest

from app.services.clustering_service import cluster_comments
from app.services.cluster_orchestrator import run_clustering
from app.services.comment_service import create_comment
from app.services.hearing_service import create_hearing


MOCK_CLUSTERS = [
    {"name": "Safety", "description": "Road safety concerns.", "comment_ids": [1]},
    {"name": "Noise", "description": "Noise pollution issues.", "comment_ids": [2]},
]


@pytest.fixture
def hearing_with_comments(app):
    with app.app_context():
        with patch("app.services.hearing_service._trigger_summary"):
            h = create_hearing("Council Meeting", date(2026, 4, 18))
        c1 = create_comment(h.id, "The intersection is dangerous.")
        c2 = create_comment(h.id, "Night noise is unbearable.")
        yield h, c1, c2


# --- clustering_service (pure, no DB) ---

def test_cluster_comments_groups_correctly():
    comments = [{"id": 1, "body": "Fix the lights."}, {"id": 2, "body": "Too loud at night."}]
    clusters = [
        {"name": "Lights", "description": "Lighting issues.", "comment_ids": [1]},
        {"name": "Noise", "description": "Noise issues.", "comment_ids": [2]},
    ]
    with patch("app.services.clustering_service.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = '[{"name":"Lights","description":"Lighting issues.","comment_ids":[1]},{"name":"Noise","description":"Noise issues.","comment_ids":[2]}]'
        result = cluster_comments(comments)
    assert len(result) == 2
    assert result[0]["name"] == "Lights"


def test_cluster_comments_requires_min_two():
    with pytest.raises(ValueError, match="at least 2"):
        cluster_comments([{"id": 1, "body": "Only one."}])


def test_cluster_comments_rejects_duplicate_ids():
    comments = [{"id": 1, "body": "A"}, {"id": 2, "body": "B"}]
    bad_response = '[{"name":"X","description":"d","comment_ids":[1,2]},{"name":"Y","description":"d","comment_ids":[1]}]'
    with patch("app.services.clustering_service.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = bad_response
        with pytest.raises(ValueError, match="multiple clusters"):
            cluster_comments(comments)


def test_cluster_comments_rejects_missing_ids():
    comments = [{"id": 1, "body": "A"}, {"id": 2, "body": "B"}]
    bad_response = '[{"name":"X","description":"d","comment_ids":[1]}]'
    with patch("app.services.clustering_service.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = bad_response
        with pytest.raises(ValueError, match="missing from output"):
            cluster_comments(comments)


# --- cluster_orchestrator ---

def test_run_clustering_saves_clusters(app, hearing_with_comments):
    h, c1, c2 = hearing_with_comments
    mock_data = [
        {"name": "Safety", "description": "Safety concerns.", "comment_ids": [c1.id]},
        {"name": "Noise", "description": "Noise concerns.", "comment_ids": [c2.id]},
    ]
    with app.app_context():
        with patch("app.services.cluster_orchestrator.cluster_comments", return_value=mock_data):
            clusters = run_clustering(h.id)
        assert len(clusters) == 2
        assert {c.name for c in clusters} == {"Safety", "Noise"}


def test_run_clustering_upserts(app, hearing_with_comments):
    h, c1, c2 = hearing_with_comments
    first = [
        {"name": "Old", "description": "Old theme.", "comment_ids": [c1.id, c2.id]},
    ]
    second = [
        {"name": "Safety", "description": "New.", "comment_ids": [c1.id]},
        {"name": "Noise", "description": "New.", "comment_ids": [c2.id]},
    ]
    with app.app_context():
        with patch("app.services.cluster_orchestrator.cluster_comments", return_value=first):
            run_clustering(h.id)
        with patch("app.services.cluster_orchestrator.cluster_comments", return_value=second):
            clusters = run_clustering(h.id)
        from app import db
        from app.models.comment_cluster import CommentCluster
        count = db.session.query(CommentCluster).filter_by(hearing_id=h.id).count()
        assert count == 2
        assert {c.name for c in clusters} == {"Safety", "Noise"}


def test_run_clustering_missing_hearing_raises(app):
    with app.app_context():
        with pytest.raises(LookupError):
            run_clustering(99999)


# --- API endpoints ---

def test_clusters_api_get(test_client, app, hearing_with_comments):
    h, c1, c2 = hearing_with_comments
    mock_data = [
        {"name": "Safety", "description": "Safety.", "comment_ids": [c1.id]},
        {"name": "Noise", "description": "Noise.", "comment_ids": [c2.id]},
    ]
    with app.app_context():
        with patch("app.services.cluster_orchestrator.cluster_comments", return_value=mock_data):
            run_clustering(h.id)
        resp = test_client.get(f"/api/hearings/{h.id}/clusters")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_cluster_api_post(test_client, app, hearing_with_comments):
    h, c1, c2 = hearing_with_comments
    mock_data = [
        {"name": "Safety", "description": "Safety.", "comment_ids": [c1.id]},
        {"name": "Noise", "description": "Noise.", "comment_ids": [c2.id]},
    ]
    with app.app_context():
        with patch("app.services.cluster_orchestrator.cluster_comments", return_value=mock_data):
            resp = test_client.post(f"/api/hearings/{h.id}/cluster")
    assert resp.status_code == 200


def test_cluster_api_404_unknown_hearing(test_client, app):
    with app.app_context():
        resp = test_client.post("/api/hearings/99999/cluster")
    assert resp.status_code == 404
