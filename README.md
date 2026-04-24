# CivicLens

> **⚠️ This project is deprecated as of April 2026.** It was built during Frontera Devs' Hackathon 2026 and is no longer actively maintained. The Railway deployment (PostgreSQL database + hosting) has been shut down. The Groq API key used during the event is no longer active. The demos below show the app as it worked at the time of the hackathon.

---

## Project Overview

CivicLens makes local government hearings accessible to everyday people. Instead of watching hours of public meeting recordings or reading dense transcripts, users get AI-generated summaries, clustered public opinion, and an accountability score showing whether official decisions aligned with what the community actually said.

**Features built during the hackathon:**
- AI-generated summaries of public hearing transcripts and agendas (Groq / Llama 3)
- Public comment submission with citizen accounts
- Automatic clustering of comments into thematic groups (e.g. affordability, safety, environmental impact)
- Government decision tracking with accountability scoring against public comment clusters
- YouTube transcript ingestion via the YouTube Data API
- Admin panel for managing hearings, comments, and decisions
- REST API alongside the web UI

---

## Demo

### Browsing hearings and reading AI summaries
<!-- GIF: hearing list → click into a hearing → summary panel -->
<img src="docs/gifs/hearing-summary.gif" width="660" alt="Hearing summary demo" />

### Submitting a public comment
<!-- GIF: login → hearing detail → submit comment form -->
<img src="docs/gifs/comment-submission.gif" width="660" alt="Comment submission demo" />

### Comment clustering and accountability score
<!-- GIF: admin triggers clustering → cluster view → accountability panel -->
<img src="docs/gifs/clustering-accountability.gif" width="660" alt="Clustering and accountability demo" />

---

## Getting Started

> These instructions work locally if you supply your own API keys. Without a `GROQ_API_KEY`, the AI features (summaries, clustering, accountability scoring) will error. The app runs on SQLite locally — no database setup required.

**Prerequisites:**
- Python 3.10+
- A [Groq API key](https://console.groq.com) (free tier available)
- Optional: A [YouTube Data API v3 key](https://console.cloud.google.com) for transcript ingestion

**Installation:**

```bash
python3 -m venv .venv && source .venv/bin/activate
make install
```

**Configuration:**

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session secret — any random string |
| `GROQ_API_KEY` | Yes | Powers AI summaries, clustering, accountability |
| `DATABASE_URL` | No | Defaults to `sqlite:///hearings.db` |
| `YOUTUBE_API_KEY` | No | Only needed for YouTube channel sync |

---

## Running the Project

```bash
make run       # starts Flask on http://localhost:5001
make test      # runs the pytest suite
make clean     # removes __pycache__ and the local SQLite db
```

On first run, `make seed` creates the SQLite database and an admin account:

```bash
make seed
```

| Field | Value |
|---|---|
| Email | `admin@admin.com` |
| Password | `admin123` |

Log in at `/login` to access the admin panel, create hearings, and manage comments.

---

## Project Structure

```
app/
  models/        # SQLAlchemy models (Hearing, PublicComment, CommentCluster, …)
  routes/
    web.py       # Server-rendered Flask routes
    api.py       # REST API endpoints
  services/
    summarization_service.py   # Groq-powered hearing summaries
    clustering_service.py      # Groq-powered comment clustering
    accountability_service.py  # Decision vs. cluster alignment scoring
    youtube_sync.py            # YouTube Data API ingestion
    comment_service.py
    hearing_service.py
  templates/     # Jinja2 HTML templates
  static/        # CSS, JS, assets
migrations/      # Alembic migration files
tests/           # pytest test suite
config.py        # Environment-based Flask config
run.py           # App entry point
```

---

## Credits

Built at Frontera Devs' Hackathon 2026 by Luis Garcia, Gabriel Quiroga, Emiliano Prado, & Ryan Martinez.

---

## License

[MIT](LICENSE)
