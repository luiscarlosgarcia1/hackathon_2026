# Plan: Phase 2 — Hearing Summarization

> Builds on Phase 1. Auto-triggers when a hearing is created or updated.
> Produces a structured digest: issue description, stakeholders, key arguments, community impact.

---

## Dependency map

```
Slice 1 ──┐
           ├──► Slice 3 ──► Slice 4
Slice 2 ──┘
```

Slices 1 and 2 are fully independent — run them in parallel.
Slice 3 requires both. Slice 4 can start once Slice 1 is done (use mock data until Slice 3 lands).

---

## Slice 1 — HearingSummary model + migration

**What to build**

A new `HearingSummary` model linked to `Hearing`. One summary per hearing (upsert on re-run, not append).

Fields:
- `id`, `hearing_id` (FK → hearings, unique)
- `issue_description` (Text)
- `stakeholders` (Text)
- `key_arguments` (Text)
- `community_impact` (Text)
- `created_at`, `updated_at`

Files to create/touch:
- `app/models/hearing_summary.py` — model definition with `to_dict()`
- `app/models/__init__.py` — register the model
- a Flask-Migrate migration

Acceptance:
- [ ] `HearingSummary` can be created, fetched by `hearing_id`, and updated in place
- [ ] `Hearing.summary` backref available (one-to-one relationship)
- [ ] Migration runs cleanly with `flask db upgrade`

---

## Slice 2 — Claude summarization service

**What to build**

An isolated AI service that takes a `Hearing` object and returns a structured summary dict. Nothing else calls Claude — all AI access goes through here.

Files to create:
- `app/services/summarization_service.py`
  - `summarize_hearing(hearing) -> dict` — calls Claude, returns `{issue_description, stakeholders, key_arguments, community_impact}`

Implementation notes:
- Use the OpenAI SDK (`openai` package). Model: `codex-mini-latest` (or override via env var `SUMMARIZATION_MODEL`).
- Prompt should instruct Claude to return a JSON object with exactly those 4 keys.
- Input to Claude: hearing title, date, and whichever of `transcript` / `agenda` are present.
- Parse and validate the JSON response before returning — raise a clear error if it's malformed.
- Keep the prompt in a constant at the top of the file so it's easy to iterate.

Acceptance:
- [ ] `summarize_hearing(hearing)` returns a dict with all 4 keys populated
- [ ] Works when only agenda is present, only transcript is present, or both
- [ ] Raises `ValueError` if Claude returns unparseable output

---

## Slice 3 — Orchestration, auto-trigger, and re-run route

**What to build**

The glue layer: persists summaries to the DB, wires auto-triggering into the hearing creation flow, and exposes a re-run endpoint.

Depends on: Slice 1 (model) + Slice 2 (AI service)

Files to create/touch:
- `app/services/summary_orchestrator.py`
  - `run_summary(hearing_id)` — fetches hearing, calls `summarize_hearing`, upserts `HearingSummary`
- `app/services/hearing_service.py` — call `run_summary` at the end of `create_hearing` and any future `update_hearing`
- `app/routes/api.py` — add `POST /api/hearings/<id>/summarize` to trigger re-run manually

Acceptance:
- [ ] Creating a hearing automatically generates a summary
- [ ] `POST /api/hearings/<id>/summarize` regenerates and overwrites the existing summary
- [ ] If summarization fails, the hearing is still saved (catch and log the error — don't block creation)
- [ ] Calling re-run multiple times is safe (idempotent upsert)

---

## Slice 4 — Hearing detail UI — summary panel + re-run button

**What to build**

Update the hearing detail page to show the digest and let users trigger a re-run.

Depends on: Slice 1 (for data shape). Can be built with mock template data while Slice 3 is in progress.

Files to touch:
- `app/templates/hearings/detail.html` — add summary section
- `app/routes/web.py` — pass `hearing.summary` to the template
- `app/static/style.css` — style the summary cards

UI spec:
- Show a 2×2 grid of labeled cards: Issue, Stakeholders, Key Arguments, Community Impact
- If `hearing.summary` is `None`, show a subtle "Summary pending..." placeholder (it's being generated async conceptually, or just created)
- Add a "Re-summarize" button that posts to `/api/hearings/<id>/summarize` and refreshes the page
- The summary section sits above the raw transcript/agenda sections

Acceptance:
- [ ] All 4 digest fields render on the detail page
- [ ] "Summary pending..." state is shown when no summary exists
- [ ] Re-summarize button triggers the API route and the page reloads with updated content
- [ ] Layout holds up at narrow viewport widths
