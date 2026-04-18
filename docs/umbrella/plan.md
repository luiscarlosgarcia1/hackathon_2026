# Plan: Civic Engagement Platform

> Source: README.md project vision

## Architectural decisions

- **Core stack**: Python, Flask
- **Key models**: Hearing, HearingSummary, PublicComment, CommentCluster, GovernmentDecision
- **AI boundary**: All AI processing (summarization, clustering, comparison) is isolated behind a service layer so the transport and storage layers never change when the AI provider does
- **Routes**: `/hearings`, `/hearings/<id>`, `/hearings/<id>/comments`, `/hearings/<id>/clusters`, `/hearings/<id>/accountability`

---

## Phase 1: Foundation & Hearing Ingestion

**User stories**: As a civic platform user, I want to submit or view public hearing content so that the system has material to process.

### What to build

A working Flask app where hearings (transcripts, agendas, recordings) can be submitted and stored. Includes a minimal UI to upload or browse hearings. This is the baseline layer everything else builds on.

### Acceptance criteria

- [ ] A hearing (title, date, transcript or agenda text) can be submitted through the UI or API
- [ ] Submitted hearings are persisted and retrievable by ID
- [ ] A list of all hearings is browsable
- [ ] App runs locally with a single start command

---

## Phase 2: Hearing Summarization

**User stories**: As a community member, I want a plain-language summary of a hearing so that I can understand what was decided without reading the full transcript.

### What to build

An AI pipeline that processes each hearing and produces a structured digest: what issue is being discussed, who the key stakeholders are, what arguments were raised, and how the outcome could affect the community. Summaries are displayed on the hearing detail page.

### Acceptance criteria

- [ ] Triggering summarization on a hearing produces a structured digest
- [ ] Digest surfaces: issue description, stakeholders, key arguments, community impact
- [ ] Summary is displayed on the hearing detail page
- [ ] Summarization can be re-run if the hearing content is updated

---

## Phase 3: Public Comment Ingestion & Clustering

**User stories**: As a community member, I want to submit a comment on a hearing and see how my view relates to others, so that I understand where public opinion stands.

### What to build

Public comments can be submitted against a hearing. An AI agent groups them into named theme clusters (e.g. affordability, safety, environment). Clusters and their comments are browsable as a structured list.

### Acceptance criteria

- [ ] A comment can be submitted against a hearing
- [ ] Triggering clustering groups comments into labeled themes
- [ ] Each cluster has a name, a count, and is browsable to see individual comments
- [ ] Clustering can be re-run as new comments arrive

---

## Phase 4: Brain-Map Visualization via Obsidian Sync

**User stories**: As a community member, I want to explore public opinion as a visual graph so that I can quickly grasp the shape and intensity of community sentiment.

### What to build

After clustering, the backend pushes each hearing and its comment clusters to Obsidian as linked notes via the [Obsidian Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api). Obsidian's built-in graph view renders the brain map — hearings as root nodes, clusters as child nodes linked by theme. No custom renderer needed.

### Acceptance criteria

- [ ] Each hearing is created as a note in Obsidian on ingestion
- [ ] Each comment cluster is created as a linked note under its hearing
- [ ] Links between notes reflect theme relationships so Obsidian graph view shows the correct structure
- [ ] Sync can be re-triggered when clusters are updated
- [ ] The hearing detail page links out to the Obsidian note for that hearing

---

## Phase 5: Accountability Layer

**User stories**: As a resident, I want to see whether a government decision aligned with public comment patterns so that I can evaluate whether my representatives acted in line with community concerns.

### What to build

Government decisions are recorded against a hearing. An AI comparison surfaces whether the outcome aligned with, partially addressed, or diverged from the dominant themes in the public comment clusters. Results are displayed as an accountability summary on the hearing page.

### Acceptance criteria

- [ ] A final government decision can be recorded against a hearing
- [ ] The system compares the decision against comment clusters and produces an alignment summary
- [ ] Alignment result (aligned / partial / diverged) is shown with supporting reasoning
- [ ] The accountability summary is visible on the hearing detail page
