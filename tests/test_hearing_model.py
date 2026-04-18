import pytest
from datetime import date
from app import db as _db
from app.services.hearing_service import create_hearing, get_hearing, list_hearings


def test_create_and_retrieve_hearing(app):
    with app.app_context():
        h = create_hearing("Budget Meeting", date(2026, 3, 10), transcript="Full text here")
        fetched = get_hearing(h.id)
        assert fetched is not None
        assert fetched.title == "Budget Meeting"
        assert fetched.date == date(2026, 3, 10)
        assert fetched.transcript == "Full text here"


def test_list_hearings(app):
    with app.app_context():
        create_hearing("Zoning Hearing", date(2026, 1, 5))
        create_hearing("Budget Hearing", date(2026, 2, 15))
        hearings = list_hearings()
        assert len(hearings) == 2
        titles = {h.title for h in hearings}
        assert "Zoning Hearing" in titles
        assert "Budget Hearing" in titles


def test_missing_title_raises_error(app):
    with app.app_context():
        with pytest.raises(Exception):
            create_hearing(None, date(2026, 1, 1))


def test_missing_date_raises_error(app):
    with app.app_context():
        with pytest.raises(Exception):
            create_hearing("No Date Hearing", None)
