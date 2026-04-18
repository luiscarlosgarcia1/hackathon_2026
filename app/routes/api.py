from datetime import date as date_type
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload
from app import db
from app.models.hearing import Hearing
from app.models.comment_cluster import CommentCluster
from app.services.hearing_service import create_hearing, get_hearing, list_hearings
from app.services.summary_orchestrator import run_summary
from app.services.comment_service import create_comment
from app.services.cluster_orchestrator import run_clustering

api_bp = Blueprint("api", __name__)


@api_bp.route("/hearings", methods=["GET"])
def get_hearings():
    return jsonify([h.to_dict() for h in list_hearings()])


@api_bp.route("/hearings/<int:hearing_id>", methods=["GET"])
def get_hearing_by_id(hearing_id):
    hearing = get_hearing(hearing_id)
    if hearing is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(hearing.to_dict())


@api_bp.route("/hearings", methods=["POST"])
def create_hearing_route():
    data = request.get_json(silent=True) or {}

    title = data.get("title", "").strip() if isinstance(data.get("title"), str) else ""
    raw_date = data.get("date", "")
    transcript = data.get("transcript") or None
    agenda = data.get("agenda") or None

    if not title:
        return jsonify({"error": "title is required"}), 400

    if not raw_date:
        return jsonify({"error": "date is required"}), 400

    try:
        parsed_date = date_type.fromisoformat(raw_date)
    except (ValueError, TypeError):
        return jsonify({"error": "date must be ISO format (YYYY-MM-DD)"}), 400

    hearing = create_hearing(title, parsed_date, transcript=transcript, agenda=agenda)
    return jsonify(hearing.to_dict()), 201


@api_bp.route("/hearings/<int:hearing_id>/comments", methods=["POST"])
def create_comment_route(hearing_id):
    data = request.get_json(silent=True) or {}
    body = data.get("body", "").strip() if isinstance(data.get("body"), str) else ""
    if not body:
        return jsonify({"error": "body is required"}), 400
    try:
        comment = create_comment(hearing_id, body)
    except ValueError:
        return jsonify({"error": "Not found"}), 404
    return jsonify(comment.to_dict()), 201


@api_bp.route("/hearings/<int:hearing_id>/clusters", methods=["GET"])
def get_clusters(hearing_id):
    hearing = db.session.get(Hearing, hearing_id)
    if hearing is None:
        return jsonify({"error": "Not found"}), 404
    clusters = (
        db.session.query(CommentCluster)
        .options(joinedload(CommentCluster.comments))
        .filter_by(hearing_id=hearing_id)
        .all()
    )
    return jsonify([c.to_dict(include_comments=True) for c in clusters]), 200


@api_bp.route("/hearings/<int:hearing_id>/cluster", methods=["POST"])
def cluster_hearing_route(hearing_id):
    hearing = get_hearing(hearing_id)
    if hearing is None:
        return jsonify({"error": "Not found"}), 404

    try:
        clusters = run_clustering(hearing_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify([c.to_dict() for c in clusters]), 200


@api_bp.route("/hearings/<int:hearing_id>/summarize", methods=["POST"])
def summarize_hearing_route(hearing_id):
    hearing = get_hearing(hearing_id)
    if hearing is None:
        return jsonify({"error": "Not found"}), 404

    try:
        summary = run_summary(hearing_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422

    return jsonify(summary.to_dict()), 200
