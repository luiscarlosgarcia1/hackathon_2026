from datetime import date
from app import db as _db
from app.models.hearing import Hearing
from app.models.hearing_summary import HearingSummary


def _make_hearing(app, title="Test Hearing", d=None):
    with app.app_context():
        h = Hearing(title=title, date=d or date(2026, 4, 1))
        _db.session.add(h)
        _db.session.commit()
        return h.id


def test_create_summary(app):
    hearing_id = _make_hearing(app)
    with app.app_context():
        s = HearingSummary(
            hearing_id=hearing_id,
            issue_description="Budget shortfall",
            stakeholders="City council, residents",
            key_arguments="Raise taxes vs. cut services",
            community_impact="Schools affected",
        )
        _db.session.add(s)
        _db.session.commit()

        fetched = HearingSummary.query.filter_by(hearing_id=hearing_id).one()
        assert fetched.issue_description == "Budget shortfall"
        assert fetched.stakeholders == "City council, residents"
        assert fetched.key_arguments == "Raise taxes vs. cut services"
        assert fetched.community_impact == "Schools affected"


def test_fetch_by_hearing_id(app):
    hearing_id = _make_hearing(app, title="Zoning Hearing")
    with app.app_context():
        _db.session.add(HearingSummary(hearing_id=hearing_id, issue_description="Zoning dispute"))
        _db.session.commit()

        result = HearingSummary.query.filter_by(hearing_id=hearing_id).one_or_none()
        assert result is not None
        assert result.issue_description == "Zoning dispute"


def test_update_in_place(app):
    hearing_id = _make_hearing(app, title="Update Hearing")
    with app.app_context():
        s = HearingSummary(hearing_id=hearing_id, issue_description="Original")
        _db.session.add(s)
        _db.session.commit()

        s = HearingSummary.query.filter_by(hearing_id=hearing_id).one()
        s.issue_description = "Updated"
        _db.session.commit()

        updated = HearingSummary.query.filter_by(hearing_id=hearing_id).one()
        assert updated.issue_description == "Updated"
        assert HearingSummary.query.count() == 1


def test_hearing_summary_backref(app):
    hearing_id = _make_hearing(app, title="Backref Hearing")
    with app.app_context():
        s = HearingSummary(hearing_id=hearing_id, community_impact="High")
        _db.session.add(s)
        _db.session.commit()

        h = _db.session.get(Hearing, hearing_id)
        assert h.summary is not None
        assert h.summary.community_impact == "High"


def test_to_dict(app):
    hearing_id = _make_hearing(app, title="Dict Hearing")
    with app.app_context():
        s = HearingSummary(
            hearing_id=hearing_id,
            issue_description="desc",
            stakeholders="s",
            key_arguments="k",
            community_impact="c",
        )
        _db.session.add(s)
        _db.session.commit()

        d = HearingSummary.query.filter_by(hearing_id=hearing_id).one().to_dict()
        assert d["issue_description"] == "desc"
        assert d["stakeholders"] == "s"
        assert d["key_arguments"] == "k"
        assert d["community_impact"] == "c"
        assert d["hearing_id"] == hearing_id
        assert "created_at" in d
        assert "updated_at" in d
