import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User


@pytest.fixture
def user(db):
    u = User(email="alice@example.com", name="Alice", role="citizen")
    u.set_password("secret123")
    db.session.add(u)
    db.session.commit()
    return u


def test_set_and_check_password(user):
    assert user.check_password("secret123") is True


def test_wrong_password_fails(user):
    assert user.check_password("wrongpass") is False


def test_is_admin_false_for_citizen(user):
    assert user.is_admin is False


def test_is_admin_true_for_admin(db):
    u = User(email="admin@example.com", name="Admin", role="admin")
    u.set_password("adminpass")
    db.session.add(u)
    db.session.commit()
    assert u.is_admin is True


def test_to_dict_excludes_password_hash(user):
    d = user.to_dict()
    assert "password_hash" not in d
    assert d["email"] == "alice@example.com"
    assert d["name"] == "Alice"
    assert d["role"] == "citizen"


def test_duplicate_email_raises(db, user):
    duplicate = User(email="alice@example.com", name="Alice2", role="citizen")
    duplicate.set_password("other")
    db.session.add(duplicate)
    with pytest.raises(IntegrityError):
        db.session.commit()
