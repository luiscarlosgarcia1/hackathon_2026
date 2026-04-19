from datetime import date as date_type
from flask import Blueprint, render_template, request, redirect, url_for, abort, session
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


def _format_comments(comments):
    for c in comments:
        c.created_at_display = c.created_at.strftime('%b %d, %Y at %I:%M %p').replace(' 0', ' ')
    return comments


@web_bp.route("/hearings/<int:hearing_id>")
def hearing_detail(hearing_id):
    hearing = get_hearing(hearing_id)
    if hearing is None:
        abort(404)
    comments = _format_comments(hearing.comments.order_by("created_at").all())
    comments_data = [c.to_dict() for c in comments]
    clusters = hearing.clusters.all()
    clusters_data = [c.to_dict(include_comments=True) for c in clusters]
    return render_template(
        "hearings/detail.html",
        hearing=hearing,
        summary=hearing.summary,
        comments=comments,
        comments_data=comments_data,
        clusters=clusters,
        clusters_data=clusters_data,
        comment_error=None,
        decision=hearing.decision,
        accountability=hearing.accountability,
    )


@web_bp.route("/hearings/<int:hearing_id>/comments", methods=["POST"])
def submit_comment(hearing_id):
    hearing = get_hearing(hearing_id)
    if hearing is None:
        abort(404)
    body = request.form.get("body", "").strip()
    if not body:
        comments = _format_comments(hearing.comments.order_by("created_at").all())
        comments_data = [c.to_dict() for c in comments]
        clusters = hearing.clusters.all()
        clusters_data = [c.to_dict(include_comments=True) for c in clusters]
        return render_template(
            "hearings/detail.html",
            hearing=hearing,
            summary=hearing.summary,
            comments=comments,
            comments_data=comments_data,
            clusters=clusters,
            clusters_data=clusters_data,
            comment_error="Comment cannot be empty.",
            decision=hearing.decision,
            accountability=hearing.accountability,
        )
    create_comment(hearing_id, body)
    return redirect(url_for("web.hearing_detail", hearing_id=hearing_id))


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html", error=None)
    from app.models.user import User
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return render_template("auth/login.html", error="Invalid email or password.")
    session["user_id"] = user.id
    return redirect(url_for("web.list_hearings"))


@web_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("auth/signup.html", error=None)
    from app import db
    from app.models.user import User
    name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    if not name or not email or not password:
        return render_template("auth/signup.html", error="All fields are required.")
    if User.query.filter_by(email=email).first():
        return render_template("auth/signup.html", error="An account with that email already exists.")
    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    session["user_id"] = user.id
    return redirect(url_for("web.list_hearings"))


@web_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("web.list_hearings"))


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