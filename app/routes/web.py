from datetime import date as date_type
from flask import Blueprint, render_template, request, redirect, url_for, abort
from app.services.hearing_service import (
    create_hearing,
    get_hearing,
    list_hearings as fetch_hearings,
)
from app.services.comment_service import create_comment

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    return redirect(url_for("web.list_hearings"))


@web_bp.route("/hearings")
def list_hearings():
    hearings = fetch_hearings()
    return render_template("hearings/list.html", hearings=hearings)


@web_bp.route("/hearings/<int:hearing_id>")
def hearing_detail(hearing_id):
    hearing = get_hearing(hearing_id)
    if hearing is None:
        abort(404)
    comments = hearing.comments.order_by("created_at").all()
    clusters = hearing.clusters.all()
    return render_template(
        "hearings/detail.html",
        hearing=hearing,
        summary=hearing.summary,
        comments=comments,
        clusters=clusters,
        comment_error=None,
    )


@web_bp.route("/hearings/<int:hearing_id>/comments", methods=["POST"])
def submit_comment(hearing_id):
    hearing = get_hearing(hearing_id)
    if hearing is None:
        abort(404)
    body = request.form.get("body", "").strip()
    if not body:
        comments = hearing.comments.order_by("created_at").all()
        clusters = hearing.clusters.all()
        return render_template(
            "hearings/detail.html",
            hearing=hearing,
            summary=hearing.summary,
            comments=comments,
            clusters=clusters,
            comment_error="Comment cannot be empty.",
        )
    create_comment(hearing_id, body)
    return redirect(url_for("web.hearing_detail", hearing_id=hearing_id))


@web_bp.route("/hearings/new", methods=["GET", "POST"])
def new_hearing():
    if request.method == "GET":
        return render_template("hearings/new.html", error=None, form_data={})

    title = request.form.get("title", "").strip()
    raw_date = request.form.get("date", "").strip()
    transcript = request.form.get("transcript", "").strip() or None
    agenda = request.form.get("agenda", "").strip() or None

    form_data = {"title": title, "date": raw_date, "transcript": transcript, "agenda": agenda}

    if not title:
        return render_template("hearings/new.html", error="Title is required.", form_data=form_data)

    if not raw_date:
        return render_template("hearings/new.html", error="Date is required.", form_data=form_data)

    try:
        parsed_date = date_type.fromisoformat(raw_date)
    except ValueError:
        return render_template("hearings/new.html", error="Invalid date format.", form_data=form_data)

    hearing = create_hearing(title, parsed_date, transcript=transcript, agenda=agenda)
    return redirect(url_for("web.hearing_detail", hearing_id=hearing.id))
