# Plan: Phase 3 — Public Comment Ingestion & Clustering

> Builds on Phase 2. Comments are anonymous. Clustering is manually triggered (not auto on every submit).
> AI provider: Ollama via OpenAI-compatible SDK — same pattern as `summarization_service.py`.

---

## Dependency map

```
Slice 1 ──► Slice 3 ──┐
         └──► Slice 5  │
                       ▼
Slice 2 ──────────► Slice 4
```

**Batch 1 (fully parallel):** Slice 1 + Slice 2
**Batch 2 (both need Slice 1):** Slice 3 + Slice 5 — start once Slice 1 merges; Slice 5 uses mock data until Slice 4 lands
**Batch 3:** Slice 4 — needs Slice 1 + Slice 2; uses real comments from Slice 3 for end-to-end testing

---

## Slice 1 — Data models + migration

**What to build**

Two new models wired into the existing SQLAlchemy setup.

`PublicComment`:
- `id` (Integer PK)
- `hearing_id` (FK → hearings, not null)
- `body` (Text, not null)
- `cluster_id` (FK → comment_clusters, nullable — null until clustering runs)
- `created_at`

`CommentCluster`:
- `id` (Integer PK)
- `hearing_id` (FK → hearings, not null)
- `name` (String 255, not null) — AI-assigned theme label e.g. "Affordability"
- `description` (Text) — 1–2 sentence cluster summary
- `created_at`, `updated_at`

Relationships:
- `Hearing` → `comments` (one-to-many backref)
- `Hearing` → `clusters` (one-to-many backref)
- `CommentCluster` → `comments` (one-to-many backref)

Files to create/touch:
- `app/models/public_comment.py` — model + `to_dict()`
- `app/models/comment_cluster.py` — model + `to_dict()` (include `comment_count` property)
- `app/models/__init__.py` — register both models
- `app/models/hearing.py` — add `comments` + `clusters` relationships
- Flask-Migrate migration

Acceptance:
- [ ] Both models can be created, fetched, and related to a `Hearing` in a test
- [ ] `hearing.comments` and `hearing.clusters` backrefs work
- [ ] A comment's `cluster_id` can be set after the fact (update, not recreate)
- [ ] Migration runs cleanly with `flask db upgrade`

---

## Slice 2 — AI clustering service

**What to build**

An isolated service that takes a list of comment bodies and returns a structured cluster assignment. Nothing else calls Ollama for clustering — all AI access goes through here.

Files to create:
- `app/services/clustering_service.py`
  - `cluster_comments(comments: list) -> list[dict]`
  - Input: list of `{"id": int, "body": str}` dicts
  - Output: list of `{"name": str, "description": str, "comment_ids": [int, ...]}`

Implementation notes:
- Use the OpenAI SDK with `OLLAMA_BASE_URL` and `CLUSTERING_MODEL` env vars (default same model as summarization).
- Prompt instructs the model to return a JSON array. Each element is one cluster with a label, a 1–2 sentence description, and the list of comment IDs that belong to it. Every comment ID in the input must appear in exactly one cluster.
- Keep the system prompt as a top-level constant for easy iteration.
- Parse and validate the JSON before returning — raise `ValueError` on malformed output or if any input ID is missing from the output.
- Guard: if fewer than 2 comments are passed in, raise `ValueError("need at least 2 comments to cluster")`.

Acceptance:
- [ ] Returns a valid cluster list for a set of ≥2 diverse comments
- [ ] Every input comment ID appears in exactly one cluster in the output
- [ ] Raises `ValueError` for < 2 comments
- [ ] Raises `ValueError` if response is unparseable JSON

---

## Slice 3 — Comment submission (API + web form)

**Depends on:** Slice 1

**What to build**

Everything needed for a user to submit an anonymous comment on a hearing and see it listed.

Files to create/touch:
- `app/services/comment_service.py`
  - `create_comment(hearing_id: int, body: str) -> PublicComment` — validates hearing exists, saves and returns the comment
- `app/routes/api.py` — add `POST /api/hearings/<id>/comments`
  - Body: `{"body": "..."}` — returns 201 with `comment.to_dict()`
  - Returns 404 if hearing not found, 400 if body is missing/empty
- `app/routes/web.py` — add `POST /hearings/<id>/comments`
  - Reads form field `body`, calls `create_comment`, redirects back to hearing detail
- `app/templates/hearings/detail.html` — add comment submission form and comment list below the summary panel

UI spec for comment section:
- A single `<textarea>` labeled "Add your comment" with a Submit button
- Below the form: a flat list of submitted comments showing `body` and a relative timestamp (e.g. "2 hours ago")
- If no comments yet: subtle placeholder "No comments yet — be the first."

Acceptance:
- [ ] Submitting a valid comment via the web form persists it and shows it in the list on reload
- [ ] `POST /api/hearings/<id>/comments` returns 201 with the comment JSON
- [ ] Submitting empty body returns 400 (API) or re-renders with an inline error (web)
- [ ] Comments appear in chronological order (oldest first)

---

## Slice 4 — Clustering orchestration + trigger endpoint

**Depends on:** Slice 1 + Slice 2 (Slice 3 needed for realistic end-to-end testing)

**What to build**

The glue that runs clustering, persists results, and links each comment to its cluster. Exposes a manual trigger endpoint.

Files to create/touch:
- `app/services/cluster_orchestrator.py`
  - `run_clustering(hearing_id: int) -> list[CommentCluster]`
  - Fetches all comments for the hearing
  - Calls `cluster_comments()`
  - **Full replace**: deletes existing clusters for this hearing, then inserts new ones and sets `comment.cluster_id` for every comment
  - Returns the saved cluster objects
- `app/routes/api.py` — add `POST /api/hearings/<id>/cluster`
  - Calls `run_clustering`, returns 200 with list of `cluster.to_dict()` (including `comment_count`)
  - Returns 400 with `{"error": "need at least 2 comments to cluster"}` if < 2 comments exist
  - Returns 404 if hearing not found

Implementation notes:
- Full replace (delete + reinsert) is simpler and safe for a hackathon — re-running is always deterministic over the current comment set.
- Wrap the delete+insert+update in a single DB transaction so a clustering failure doesn't leave partial state.
- If `clustering_service` raises, roll back and re-raise — let the route return 500.

Acceptance:
- [ ] `run_clustering` produces named clusters and all comments have a non-null `cluster_id` afterward
- [ ] Re-running replaces clusters cleanly (old clusters gone, new ones in)
- [ ] `POST /api/hearings/<id>/cluster` returns 400 when < 2 comments exist
- [ ] A clustering service failure does not corrupt existing cluster state (transaction rollback)

---

## Slice 5 — Clusters UI panel

**Depends on:** Slice 1 (for data shape). Build with mock template data while Slice 4 is in progress.

**What to build**

The clusters section on the hearing detail page: browsable theme list with comment drill-down and a trigger button.

Files to touch:
- `app/routes/web.py` — pass `hearing.clusters` (with `.comments`) to the detail template
- `app/templates/hearings/detail.html` — add clusters panel below the comment list
- `app/static/style.css` — style cluster cards and expandable comment lists

UI spec:
- A "Cluster Comments" button that posts to `/api/hearings/<id>/cluster` and reloads the page
- If no clusters exist: show "No clusters yet — submit at least 2 comments and click Cluster Comments."
- Each cluster renders as a card: **name** (bold), description (muted), comment count badge
- Each card has a disclosure toggle ("Show comments / Hide comments") that expands an indented list of comment bodies
- Cluster cards are ordered by comment count descending (most comments first)

Acceptance:
- [ ] Clusters render on the hearing detail page after clustering runs
- [ ] Each cluster card shows name, description, and comment count
- [ ] Comment list inside each cluster is togglable (expand/collapse)
- [ ] "Cluster Comments" button triggers the API and the page reloads with updated clusters
- [ ] Empty state is shown when no clusters exist yet
- [ ] Layout holds at narrow viewport widths
