from datetime import date as date_type
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload
from app import db
from app.models.hearing import Hearing
from app.models.comment_cluster import CommentCluster
from app.models.government_decision import GovernmentDecision
from app.models.accountability_summary import AccountabilitySummary
from app.services.hearing_service import create_hearing, get_hearing, list_hearings, delete_hearing
from app.services.summary_orchestrator import run_summary
from app.services.comment_service import create_comment, delete_comment
from app.services.cluster_orchestrator import run_clustering
from app.services.accountability_service import compare_decision_to_clusters
from app.auth import login_required, admin_required

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
@admin_required
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


@api_bp.route("/hearings/<int:hearing_id>", methods=["DELETE"])
@admin_required
def delete_hearing_api(hearing_id):
    if not delete_hearing(hearing_id):
        return jsonify({"error": "Not found"}), 404
    return "", 204


@api_bp.route("/hearings/<int:hearing_id>/comments/<int:comment_id>", methods=["DELETE"])
@admin_required
def delete_comment_api(hearing_id, comment_id):
    if not delete_comment(comment_id):
        return jsonify({"error": "Not found"}), 404
    return "", 204


@api_bp.route("/hearings/<int:hearing_id>/comments", methods=["POST"])
@login_required
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


@api_bp.route("/hearings/<int:hearing_id>/decision", methods=["POST"])
def save_decision_route(hearing_id):
    hearing = db.session.get(Hearing, hearing_id)
    if hearing is None:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}
    decision_text = data.get("decision_text", "").strip() if isinstance(data.get("decision_text"), str) else ""
    if not decision_text:
        return jsonify({"error": "decision_text is required"}), 400

    raw_date = data.get("decision_date")
    decision_date = None
    if raw_date:
        try:
            decision_date = date_type.fromisoformat(raw_date)
        except (ValueError, TypeError):
            return jsonify({"error": "decision_date must be ISO format (YYYY-MM-DD)"}), 400

    decision = db.session.query(GovernmentDecision).filter_by(hearing_id=hearing_id).first()
    if decision is None:
        decision = GovernmentDecision(hearing_id=hearing_id)
        db.session.add(decision)

    decision.decision_text = decision_text
    decision.decision_date = decision_date
    db.session.commit()

    return jsonify(decision.to_dict()), 201


@api_bp.route("/hearings/<int:hearing_id>/decision", methods=["GET"])
def get_decision_route(hearing_id):
    hearing = db.session.get(Hearing, hearing_id)
    if hearing is None:
        return jsonify({"error": "Not found"}), 404

    decision = db.session.query(GovernmentDecision).filter_by(hearing_id=hearing_id).first()
    if decision is None:
        return jsonify({"error": "No decision recorded"}), 404

    return jsonify(decision.to_dict()), 200


@api_bp.route("/hearings/<int:hearing_id>/accountability", methods=["POST"])
def run_accountability_route(hearing_id):
    hearing = db.session.get(Hearing, hearing_id)
    if hearing is None:
        return jsonify({"error": "Not found"}), 404

    decision = db.session.query(GovernmentDecision).filter_by(hearing_id=hearing_id).first()
    if decision is None:
        return jsonify({"error": "No decision recorded yet"}), 409

    clusters = (
        db.session.query(CommentCluster)
        .filter_by(hearing_id=hearing_id)
        .all()
    )
    if not clusters:
        return jsonify({"error": "No clusters exist yet"}), 409

    summary_dict = hearing.summary.to_dict() if hearing.summary else None

    try:
        result = compare_decision_to_clusters(
            decision_text=decision.decision_text,
            clusters=[c.to_dict() for c in clusters],
            summary=summary_dict,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422

    accountability = db.session.query(AccountabilitySummary).filter_by(hearing_id=hearing_id).first()
    if accountability is None:
        accountability = AccountabilitySummary(hearing_id=hearing_id)
        db.session.add(accountability)

    accountability.alignment = result["alignment"]
    accountability.reasoning = result["reasoning"]
    db.session.commit()

    return jsonify(accountability.to_dict()), 200


@api_bp.route("/hearings/<int:hearing_id>/accountability", methods=["GET"])
def get_accountability_route(hearing_id):
    hearing = db.session.get(Hearing, hearing_id)
    if hearing is None:
        return jsonify({"error": "Not found"}), 404

    accountability = db.session.query(AccountabilitySummary).filter_by(hearing_id=hearing_id).first()
    if accountability is None:
        return jsonify({"error": "Accountability analysis not yet run"}), 404

    return jsonify(accountability.to_dict()), 200

@api_bp.route("/hearings/<int:hearing_id>/extract-decision", methods=["POST"])
def extract_decision_route(hearing_id):
    hearing = get_hearing(hearing_id)
    if hearing is None:
        return jsonify({"error": "Not found"}), 404
    try:
        from app.services.summarization_service import extract_decision
        decision_text = extract_decision(hearing)
        print(f"DEBUG decision_text: {decision_text!r}")
        decision = db.session.query(GovernmentDecision).filter_by(hearing_id=hearing_id).first()
        if decision is None:
            decision = GovernmentDecision(hearing_id=hearing_id)
            db.session.add(decision)
        decision.decision_text = decision_text
        db.session.commit()
        return jsonify({"decision_text": decision_text}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
