# Plan: Phase 5 — Accountability Layer

> Builds on Phase 3 (clusters) and Phase 2 (summary). Records the final government decision for a hearing, runs an AI comparison against the public comment clusters, and displays an alignment result on the hearing detail page.
> AI transport: Ollama via OpenAI-compat client — same pattern as `summarization_service.py`.

---

## Dependency map

```
Slice 1 (models + migrations) ──────────────────► Slice 3 (API routes)──► Slice 4 (UI)
Slice 2 (AI accountability service) ────────────► Slice 3 (API routes)
```

**Batch 1 (fully parallel):** Slice 1 + Slice 2
- Slice 1 owns data layer; Slice 2 works against a stub hearing/clusters dict — no DB needed
- Slice 2 merges independently; Slice 3 wires them together

**Batch 2:** Slice 3 — needs Slices 1 + 2 merged

**Batch 3:** Slice 4 — needs Slice 3 merged (can start HTML/CSS against hardcoded data, one-line swap when API is ready)

---

## Slice 1 — Data layer: GovernmentDecision + AccountabilitySummary models

**What to build**

Two new models and their migrations. One records the government's final decision text; the other stores the AI comparison result. Both are 1-per-hearing (upsert semantics: re-running overwrites the previous record).

Files to create/touch:
- `app/models/government_decision.py` — new model
  - `id`, `hearing_id` (FK → hearings, unique), `decision_text` (Text, non-null), `decision_date` (Date, nullable), `recorded_at` (DateTime, UTC default)
  - `to_dict()`: id, hearing_id, decision_text, decision_date (isoformat or null), recorded_at
- `app/models/accountability_summary.py` — new model
  - `id`, `hearing_id` (FK → hearings, unique), `alignment` (String(20): `"aligned"` / `"partial"` / `"diverged"`), `reasoning` (Text), `created_at`, `updated_at`
  - `to_dict()`: all fields
- `app/models/__init__.py` — import both new models so Flask-Migrate sees them
- `app/models/hearing.py` — add two `uselist=False` relationships: `decision` and `accountability`
- Migration: `flask db migrate -m "add government decision and accountability summary"`

Implementation notes:
- `unique=True` on `hearing_id` in both models enforces one-per-hearing at the DB level
- Use `onupdate` lambda for `accountability_summary.updated_at` (same pattern as `CommentCluster`)
- `decision_date` is optional — some decisions come without a formal date

Acceptance:
- [ ] `GovernmentDecision` and `AccountabilitySummary` tables exist after migration
- [ ] `hearing.decision` and `hearing.accountability` relationships resolve without error
- [ ] `to_dict()` returns the expected keys for both models
- [ ] Inserting a second decision for the same hearing raises an IntegrityError (enforcing uniqueness)

---

## Slice 2 — AI accountability comparison service

**What to build**

A standalone service module that takes a hearing's decision text, its comment clusters (with descriptions), and optionally the hearing summary, then calls Ollama and returns a structured alignment result. No DB access — pure input/output function.

Files to create:
- `app/services/accountability_service.py`

```python
def compare_decision_to_clusters(decision_text: str, clusters: list[dict], summary: dict | None) -> dict:
    """
    clusters: list of {name, description, comment_count}
    summary:  {issue_description, key_arguments, community_impact} or None
    returns:  {alignment: "aligned"|"partial"|"diverged", reasoning: str}
    """
```

System prompt (draft — tune as needed):
```
You are a civic accountability analyst. You are given:
1. A government decision (what was decided).
2. The dominant themes from public comments submitted before the decision.
3. Optionally, a summary of the hearing.

Return a JSON object with exactly two keys:
- alignment: one of "aligned", "partial", or "diverged"
  - "aligned": the decision directly addresses the major concerns raised
  - "partial": the decision addresses some concerns but ignores others
  - "diverged": the decision contradicts or ignores the dominant public concerns
- reasoning: 2-4 sentences explaining why you chose this alignment label, citing specific cluster themes

Return ONLY valid JSON. No markdown, no explanation, no extra text.
```

User message format: serialize decision_text + clusters (name + description + comment_count) + summary as readable text block — same approach as `summarize_hearing`.

Implementation notes:
- Follow the exact error-handling pattern in `summarization_service.py`: parse JSON, check required keys, raise `ValueError` on bad response
- Env vars: `ACCOUNTABILITY_MODEL` (default `"llama3.2"`), reuse `OLLAMA_BASE_URL`
- Keep clusters input as plain dicts (not ORM objects) so this function is testable in isolation

Acceptance:
- [ ] `compare_decision_to_clusters(...)` returns `{alignment, reasoning}` given valid inputs
- [ ] Raises `ValueError` if the model response is not valid JSON or is missing required keys
- [ ] `alignment` value is always one of the three valid strings (add a guard after JSON parse)
- [ ] Function can be called from a plain Python script with no Flask app context

---

## Slice 3 — API routes: decision CRUD + accountability trigger

**Depends on:** Slices 1 + 2 merged

**What to build**

Four endpoints in `app/routes/api.py`. The decision endpoints handle saving/fetching the government decision. The accountability endpoints trigger the AI comparison and return the stored result.

Endpoints to add to `app/routes/api.py`:

```
POST   /api/hearings/<id>/decision        — save (upsert) the government decision
GET    /api/hearings/<id>/decision        — fetch current decision (404 if none)
POST   /api/hearings/<id>/accountability  — run AI comparison, persist result, return it
GET    /api/hearings/<id>/accountability  — fetch stored accountability result (404 if none)
```

**POST /api/hearings/<id>/decision**
- Body: `{ "decision_text": "...", "decision_date": "YYYY-MM-DD" (optional) }`
- Upsert: if a `GovernmentDecision` exists for this hearing, update it; otherwise insert
- Returns `201` with `decision.to_dict()`

**GET /api/hearings/<id>/decision**
- Returns `200` with `decision.to_dict()` or `404` if none recorded

**POST /api/hearings/<id>/accountability**
- Fetch hearing's clusters (with descriptions) and decision — return `409` if no decision recorded yet, `409` if no clusters exist yet
- Call `compare_decision_to_clusters(...)` — pass hearing summary if available
- Upsert `AccountabilitySummary` for this hearing
- Returns `200` with `accountability.to_dict()`

**GET /api/hearings/<id>/accountability**
- Returns `200` with `accountability.to_dict()` or `404` if not yet run

Implementation notes:
- The `409` on missing prerequisites keeps the UI simple — it can show "run clustering first"
- For the upsert pattern, use `db.session.merge()` or query-then-update (same as any existing upsert in the codebase)
- Pass clusters as `[c.to_dict() for c in hearing.clusters]` — matches the `accountability_service` input contract

Acceptance:
- [ ] `POST /api/hearings/<id>/decision` creates or updates the decision; returns `201`
- [ ] `GET /api/hearings/<id>/decision` returns the decision or `404`
- [ ] `POST /api/hearings/<id>/accountability` returns `409` when no decision or no clusters exist
- [ ] `POST /api/hearings/<id>/accountability` returns `200` with `alignment` + `reasoning` after a successful run
- [ ] `GET /api/hearings/<id>/accountability` returns the stored result or `404`
- [ ] All four endpoints return `404` when the hearing itself doesn't exist

---

## Slice 4 — UI: decision form + accountability panel on hearing detail page

**Depends on:** Slice 3 merged (can start from hardcoded Jinja data, one-line swap to fetch from API)

**What to build**

Two new sections at the bottom of the hearing detail page, below the clusters graph:

1. **Record Decision** — a textarea + date input + submit button to save the government's final decision. Shows the existing decision text if one is already recorded.
2. **Accountability Summary** — a trigger button + result display. Shows the alignment badge and reasoning after analysis runs. Only shown when a decision exists.

Files to touch:
- `app/templates/hearings/detail.html` — add both sections
- `app/static/style.css` — alignment badge styles, section layout

**Section 1 — Record Decision (rendered from Jinja + JS for submission):**
```
┌─ Government Decision ───────────────────────────────────┐
│  [textarea: decision text, pre-filled if exists]        │
│  Decision date: [date input, optional]                  │
│  [Save Decision]                                        │
└─────────────────────────────────────────────────────────┘
```
- On submit: `POST /api/hearings/<id>/decision` via `fetch`, show success/error inline
- If a decision already exists, pre-fill the textarea and date from `hearing.decision` (passed via Jinja)

**Section 2 — Accountability Summary (JS-driven):**
```
┌─ Accountability ────────────────────────────────────────┐
│  [Run Accountability Analysis]  ← only if decision exists│
│                                                         │
│  ┌──────────┐                                           │
│  │ ALIGNED  │  ← badge: green/yellow/red by value      │
│  └──────────┘                                           │
│  The decision directly addressed the top three themes…  │
└─────────────────────────────────────────────────────────┘
```
- "Run" button calls `POST /api/hearings/<id>/accountability` — disable during fetch, show spinner
- On success: render alignment badge + reasoning (no page reload)
- If `hearing.accountability` already exists (passed via Jinja), render result immediately on load
- Alignment badge colors: `aligned` → green (`#2ea043`), `partial` → amber (`#d29922`), `diverged` → red (`#da3633`)

Implementation notes:
- Pass `hearing.decision` and `hearing.accountability` from the web route into the Jinja template — no extra fetch on page load
- The "Run" button should be hidden (not just disabled) when no decision has been saved yet — use a Jinja conditional
- Use the same dark-panel aesthetic from Phase 4 for visual consistency

Acceptance:
- [ ] Decision textarea pre-fills with existing decision text on page load
- [ ] Submitting the form saves the decision and shows a confirmation without a full page reload
- [ ] "Run Accountability Analysis" button is absent when no decision has been recorded
- [ ] Clicking "Run" disables the button, fetches the result, and renders the badge + reasoning
- [ ] Alignment badge color matches the value (green / amber / red)
- [ ] If an accountability result already exists, it renders immediately on page load without clicking "Run"
- [ ] Page degrades gracefully when neither decision nor accountability result exists yet
