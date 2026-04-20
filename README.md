# Deathguild Music Service

Scrapes Death Guild (SF goth/industrial club) playlist pages, stores data in PostgreSQL, pushes playlists to Spotify, and serves the data via a read-only FastAPI. Includes a React frontend for browsing and searching 20+ years of setlist history.

## Requirements

- Python 3.12+
- PostgreSQL
- Redis (only needed for Spotify push worker)
- Node.js 20+ (for the UI)

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```
DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/deathguild
REDIS_URL=redis://localhost:6379/0
SPOTIFY_CLIENT_ID=<spotify_client_id>
SPOTIFY_CLIENT_SECRET=<spotify_client_secret>
SPOTIFY_REDIRECT_URI=http://localhost:8000/callback
```

### 4. Create the database

The `deathguild` database and user must exist before running anything:

```sql
CREATE USER dg WITH PASSWORD '<password>';
CREATE DATABASE deathguild OWNER dg;
```

### 5. Run database migrations

```bash
alembic upgrade head
```

## Running

All commands should be run from the project root with the virtual environment active.

### Scraper

Fetches all Death Guild playlist pages and stores songs/playlists to the database. Idempotent — already-scraped playlists are skipped.

```bash
python -m scraper
```

### Worker (arq)

Processes Spotify push tasks from the Redis queue. Run this before or alongside the orchestrator.

```bash
python -m arq worker.tasks.WorkerSettings
```

### Orchestrator

Finds all scraped playlists not yet pushed to Spotify and enqueues a task for each.

```bash
python -m orchestrator
```

### Song Resolver

Resolves Spotify IDs for songs independently from playlist creation. This runs as a separate step because searching ~13k unique songs once is far more efficient than re-searching every time a song appears in a playlist (~108k playlist_song links). Songs not found on Spotify are marked with a `spotify_searched_at` timestamp so they aren't re-searched on subsequent runs — but can be explicitly retried later in case they've since been added to Spotify's catalog.

```bash
# Resolve all songs that haven't been searched yet
python -m resolve_songs

# Retry songs that were previously searched but not found
python -m resolve_songs --retry
```

### API

Read-only FastAPI serving playlist and song data. CORS is enabled for the Vite dev server on port 5173.

```bash
uvicorn api.main:app --reload
```

#### Endpoints

- `GET /v1/playlists/years` — list of years that have scraped playlists
- `GET /v1/playlists?year=&offset=&limit=` — paginated playlists, optionally filtered by year
- `GET /v1/playlists/{date}` — full playlist detail with ordered song list
- `GET /v1/songs?q=&offset=&limit=` — search songs by artist or title, returns occurrence counts
- `GET /v1/songs/{id}/playlists?offset=&limit=` — playlists a specific song appears in

Song search results are sorted by occurrence count (most-played first) because the primary use case is discovering how frequently a song has been played across Death Guild's history. Each result includes the total number of playlist appearances so users don't have to count manually.

The song-to-playlist drill-down (`/songs/{id}/playlists`) exists as a separate endpoint rather than being embedded in the search response to keep payloads small. A song like "Bela Lugosi's Dead" might appear in 800+ playlists — embedding all of those in every search result would bloat the response for the common case where the user only wants to drill into one or two songs.

All song responses include computed YouTube and Spotify URLs. YouTube links are always present (constructed from artist + title search queries). Spotify links are only present when a `spotify_id` has been resolved.

#### Response models

API response shapes are separate Pydantic models, intentionally decoupled from the SQLModel table models. This means database schema changes (adding columns, renaming fields) don't accidentally break the API contract for frontend consumers.

### UI

React + TypeScript + Vite + Tailwind CSS v4. Lives in `ui/` within the same repo so it shares workspace context with the backend.

```bash
cd ui && npm install && npm run dev
```

The UI is designed around exploring Death Guild's playlist archive — dark themed to match the club's goth/industrial aesthetic.

Playlists are organized by year rather than showing all ~1500 at once, because a flat list of that size is unusable. Clicking a year loads playlists for that year as collapsed cards showing just the date and song count. Expanding a card lazy-loads the full setlist from the API to avoid fetching detail data the user may never look at.

Search takes a hybrid approach: results show matching songs with their total occurrence count across all playlists, and each song expands to reveal every playlist it appeared in. Playlist dates in the expanded view link to a dedicated playlist detail page. This two-tier design keeps the initial search response fast while still letting users drill into the full context.

Search state is synced to URL query parameters (`/?q=bauhaus`) so that navigating to a playlist detail page and pressing back restores the search results, search bar text, and scroll position. Without this, every drill-down would force the user to re-type their search.

The Vite dev server proxies `/v1` requests to the FastAPI backend on port 8000, so no CORS issues during development and no hardcoded API URLs in the frontend code.
