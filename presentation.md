# CivicLens — Feature List

## Authentication & User Management
- User registration (name, email, password)
- Email-based login with session management
- Logout and session cleanup
- Three-tier role system: **Admin**, **Citizen**, **Guest**
- Admin: create/delete hearings, delete comments, run AI operations
- Citizen: submit and view comments
- Guest: read-only public access without an account
- Password hashing with salted werkzeug security
- CLI command to seed the initial admin account (`seed-admin`)
- Current user context injected into all templates

## Hearing Management
- Create hearings with title, date, transcript, and agenda (admin-only)
- Browse all hearings ordered by most recent
- Hearing cards showing comment count, cluster count, and AI-generated issue description
- View full hearing detail: summary, transcript, agenda, comments, clusters, decision, accountability
- Delete a hearing with full cascading cleanup of all related data (admin-only)

## YouTube Integration
- Sync hearings directly from the Hidalgo County YouTube channel
- Auto-fetch video metadata and publishing dates
- Auto-extract transcripts via YouTube Transcript API
- Support for both English and Spanish captions
- Display YouTube thumbnail on hearing cards

## AI-Powered Hearing Summaries (Groq / LLaMA 3.3 70B)
- Automatic summary generated on hearing creation
- Background daemon summarizes any unsummarized hearings on startup
- Summary broken into four structured sections:
  - **Issue Description** — concise 1–3 sentence problem statement
  - **Stakeholders** — key individuals and organizations involved
  - **Key Arguments** — main arguments presented
  - **Community Impact** — expected effects on the broader community
- Admin can manually trigger re-summarization at any time

## Public Comments
- Authenticated citizens can submit comments on any hearing
- Support for fully anonymous submissions
- Comments displayed chronologically with author name and timestamp
- Admin can delete any comment
- Comments are automatically linked to AI-generated thematic clusters

## Intelligent Comment Clustering
- AI groups submitted comments into meaningful themes (e.g., Affordability, Safety, Traffic)
- Each cluster has a name, a 1–2 sentence description, and a list of associated comments
- Admin can re-run clustering on demand
- Clusters update comment associations cleanly with cascading nullification

## Interactive Comment Visualization
- 3D brain-map style graph rendered with Cytoscape.js
- Cluster nodes sized proportionally by comment count and color-coded by theme
- Individual comment nodes connected to their cluster
- Hover to dim unrelated elements and highlight connections
- Click a cluster node to open a side panel with full cluster details and all its comments
- Zoom, pan, and fit-to-view controls
- Tooltip shows full comment text on hover
- Keyboard (`Escape`) and button to close the detail panel

## Government Decision Tracking
- Admin form to record the official government decision for a hearing
- Optional decision date field
- AI-powered extraction of the decision directly from the hearing transcript
- One decision stored per hearing with creation timestamp

## Accountability Analysis
- AI compares the government decision against dominant public comment themes
- Produces a three-tier alignment score:
  - **Aligned** — decision addresses major public concerns
  - **Partial** — decision addresses some concerns but ignores others
  - **Diverged** — decision contradicts or ignores dominant public opinion
- AI-generated reasoning citing specific cluster themes
- Results stored persistently and displayed on the hearing detail page

## RESTful API
- `GET /api/hearings` — list all hearings
- `POST /api/hearings` — create hearing (admin)
- `GET /api/hearings/<id>` — hearing detail
- `DELETE /api/hearings/<id>` — delete hearing (admin)
- `POST /api/hearings/<id>/comments` — submit comment (authenticated)
- `DELETE /api/hearings/<id>/comments/<cid>` — delete comment (admin)
- `POST /api/hearings/<id>/summarize` — regenerate summary
- `POST /api/hearings/<id>/cluster` — run clustering
- `POST /api/hearings/<id>/extract-decision` — extract decision from transcript
- `POST /api/hearings/<id>/decision` — save decision
- `GET /api/hearings/<id>/decision` — retrieve decision
- `GET /api/hearings/<id>/clusters` — list clusters
- `POST /api/hearings/<id>/accountability` — run accountability analysis
- `GET /api/hearings/<id>/accountability` — retrieve accountability results

## Web Pages
- **Home** — hero slider (4 slides, auto-rotate + manual controls), feature cards, call-to-action
- **Hearings List** — responsive grid of hearing cards with badges for date, comments, and clusters
- **Hearing Detail** — full summary, transcript, agenda, comments form, cluster visualization, decision, accountability
- **New Hearing** — admin-only form with validation
- **Login** — credentials form, guest access option, branding/mission messaging
- **Signup** — full name, email, password; duplicate account detection
- **About** — team bios (Gabriel Quiroga, Luis Garcia, Ryan Martinez, Emiliano Prado), mission statement, feature overview

## Security
- `@login_required` and `@admin_required` decorators on all protected routes
- Session-based authorization with role checks
- Password hashing with salting
- Admin-gated operations enforced at both decorator and database levels
- Cascading deletes prevent orphaned data

## Background Processes
- Daemon thread starts on app launch and summarizes any unsummarized hearings automatically
- Skipped in test mode to avoid interference with test suite

## Database Models
- **User** — email, hashed password, name, role, timestamp
- **Hearing** — title, date, transcript, agenda, YouTube video ID, timestamp
- **HearingSummary** — issue description, stakeholders, key arguments, community impact
- **PublicComment** — body, author (user or anonymous), timestamp, cluster association
- **CommentCluster** — name, description, associated comments, timestamps
- **GovernmentDecision** — decision text, decision date, timestamp
- **AccountabilitySummary** — alignment status, reasoning, timestamps

## Tech Stack & Deployment
- **Backend**: Flask 3.1.3, SQLAlchemy 2.0, Flask-Migrate (Alembic)
- **Database**: PostgreSQL (production), SQLite (development)
- **AI**: Groq API with LLaMA 3.3 70B Versatile — JSON-structured responses
- **Visualization**: Cytoscape.js
- **Deployment**: Gunicorn + Railway
- **Testing**: pytest, pytest-flask, Flask test client
- **Make commands**: `install`, `run`, `test`, `clean`

## External Integrations
- **Groq API** — summarization, clustering, decision extraction, accountability analysis
- **YouTube Data API** — channel sync, video metadata
- **YouTube Transcript API** — automatic transcript extraction (English + Spanish)
