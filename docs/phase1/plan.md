# Phase 1 Implementation Plan — Foundation & Hearing Ingestion

## Stack
- Python 3, Flask, SQLite (via SQLAlchemy), Jinja2 templates
- pytest for tests, Makefile as task runner

## Slice map

```
[Slice 1: Scaffold]
        |
   _____|_____
  |           |
[2A: Data]  [2B: UI Shell]
  |           |
  |___________|
        |
   _____|_____
  |           |
[3A: API]  [3B: UI Views]
  |           |
  |___________|
        |
[Slice 4: Integration]
```

Slices 2A and 2B run in parallel.
Slices 3A and 3B run in parallel (both require 2A; 3B also requires 2B).

---

## Slice 1 — Project Scaffold
**Sequential gate. Must land before all other work starts.**

### Deliverables
- Folder structure: `app/`, `app/models/`, `app/routes/`, `app/templates/`, `app/static/`, `tests/`
- Flask app factory (`app/__init__.py`) with `create_app(config)` pattern
- `config.py` with `DevelopmentConfig` (SQLite URI, debug, secret key from env with fallback)
- SQLAlchemy wired to app, `db.create_all()` on startup
- `requirements.txt` with pinned deps (Flask, SQLAlchemy, Flask-SQLAlchemy, pytest, pytest-flask)
- `Makefile` with targets: `install`, `run`, `test`, `seed`, `clean`
- `run.py` entry point so `make run` does `flask run`
- `.env.example` with `SECRET_KEY`, `DATABASE_URL`
- Passing `tests/conftest.py` with a `test_client` fixture using an in-memory SQLite DB

### Acceptance
- `make install && make run` starts the server with no errors
- `make test` runs (zero tests pass, zero fail — fixture smoke test only)

---

## Slice 2A — Hearing Data Layer
**Parallel with 2B. Requires Slice 1.**

### Deliverables
- `app/models/hearing.py`: `Hearing` model
  - `id` (int, PK), `title` (str, required), `date` (date, required), `transcript` (text, nullable), `agenda` (text, nullable), `created_at` (datetime, auto)
- `app/services/hearing_service.py`: thin service functions
  - `create_hearing(title, date, transcript, agenda) -> Hearing`
  - `get_hearing(id) -> Hearing | None`
  - `list_hearings() -> list[Hearing]`
- `tests/test_hearing_model.py`
  - create a hearing, assert it is persisted and retrievable by ID
  - list returns all created hearings
  - missing required fields raise an error
- `scripts/seed.py` — inserts 2–3 sample hearings so the UI has data on first run (`make seed`)

### Acceptance
- `make test` passes all model/service tests
- `make seed` populates the DB without errors

---

## Slice 2B — UI Shell
**Parallel with 2A. Requires Slice 1.**

### Deliverables
- `app/templates/base.html`: shared layout with nav (Home, Submit a Hearing), `<title>`, `{% block content %}`
- `app/templates/hearings/list.html`: extends base, renders a table/list of hearing rows (title, date, link to detail) — hardcoded placeholder rows for now
- `app/templates/hearings/detail.html`: extends base, displays one hearing (title, date, transcript block, agenda block) — hardcoded placeholder
- `app/templates/hearings/new.html`: extends base, HTML form with fields: Title (text), Date (date), Transcript (textarea), Agenda (textarea), Submit button
- `app/static/style.css`: minimal CSS (readable font, max-width container, basic form/table styles — no framework required)
- A single stub route (`GET /`) that renders `list.html` with empty data so the page loads

### Acceptance
- `make run` → visiting `/` renders the list page without errors
- All three templates render without Jinja errors when passed empty/placeholder data

---

## Slice 3A — Hearing API
**Parallel with 3B. Requires 2A.**

### Deliverables
- `app/routes/api.py` Blueprint registered at `/api`
- `POST /api/hearings` — accepts JSON `{title, date, transcript?, agenda?}`, returns `201` with hearing JSON; returns `400` on missing required fields
- `GET /api/hearings` — returns JSON array of all hearings
- `GET /api/hearings/<id>` — returns hearing JSON or `404`
- `tests/test_api.py`
  - POST creates and returns a hearing
  - POST with missing title returns 400
  - GET list returns all seeded hearings
  - GET by ID returns correct hearing
  - GET by unknown ID returns 404

### Acceptance
- `make test` passes all API tests
- `curl -X POST /api/hearings` with valid JSON returns a hearing object

---

## Slice 3B — UI Views (wire templates to backend)
**Parallel with 3A. Requires 2A + 2B.**

### Deliverables
- `app/routes/web.py` Blueprint registered at `/`
- `GET /hearings` — queries `list_hearings()`, renders `list.html` with real data
- `GET /hearings/<id>` — queries `get_hearing(id)`, renders `detail.html` or 404
- `GET /hearings/new` — renders `new.html` form
- `POST /hearings/new` — calls `create_hearing(...)`, redirects to detail page on success; re-renders form with error message on validation failure
- Update `list.html` and `detail.html` to use real Jinja variables (remove placeholder rows)
- `tests/test_web.py`
  - GET `/hearings` returns 200 with hearing titles in response
  - GET `/hearings/<id>` returns 200 with hearing content
  - GET `/hearings/<unknown>` returns 404
  - POST `/hearings/new` with valid data redirects to detail
  - POST `/hearings/new` with missing title re-renders form with error

### Acceptance
- `make test` passes all web route tests
- Full browser flow works: submit hearing → see it in list → click through to detail

---

## Slice 4 — Integration & Polish
**Sequential. Requires 3A + 3B.**

### Deliverables
- `tests/test_integration.py`: full happy-path test
  - Seed a hearing via `POST /api/hearings`
  - Fetch it via `GET /api/hearings/<id>`
  - Fetch the list via `GET /api/hearings` and assert the new hearing appears
  - Load the detail page via `GET /hearings/<id>` and assert title is in response body
- Makefile `test` target runs the full test suite (all test files)
- Makefile `seed` runs without duplicating if called twice (check before insert)
- `README.md` (root): Quick-start section — `make install`, `make seed`, `make run`, open `http://localhost:5000`
- Smoke-test the full flow manually and fix any rough edges

### Acceptance
- All acceptance criteria from `plan.md` Phase 1 are met
- `make install && make seed && make run` works on a fresh checkout with no extra steps
- `make test` is fully green
