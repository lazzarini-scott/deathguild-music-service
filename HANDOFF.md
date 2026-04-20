# Deathguild Music Service — Handoff Summary

## Project Overview
A Producer-Consumer architecture that scrapes Death Guild (SF goth/industrial club) playlist pages,
stores the data in PostgreSQL, pushes playlists to Spotify, and serves the data via a read-only FastAPI.
Includes a React UI for browsing and searching playlists.

## Tech Stack
- Python 3.13, fully async
- PostgreSQL via SQLModel (SQLAlchemy + Pydantic)
- httpx for async HTTP
- arq + Redis for async task queuing
- tenacity for Spotify retry logic with 429/Retry-After handling
- FastAPI for the read-only API
- React 19 + Vite 8 + Tailwind CSS v4 for the UI
- Alembic for DB migrations
- pydantic-settings for config from .env

## Architecture
1. **Scraper** — httpx async, fetches Death Guild playlist pages, stores to Postgres. Idempotent via `scraped_at`.
2. **Orchestrator** — finds all playlists where `pushed_at IS NULL`, enqueues an arq task per playlist
3. **Worker** — arq async worker, calls Spotify API with per-song tracking and 429 handling via tenacity
4. **FastAPI** — read-only GET endpoints serving playlist/song data with YouTube and Spotify links. CORS enabled for Vite dev server.
5. **UI** — React + Vite + Tailwind v4, lives in `ui/` within the same repo. Dark graveyard/fog theme.

## Project Structure
```
/deathguild-music-service
├── .amazonq/rules/project_rules.md   # Project rules, auto-included in every chat
├── alembic/                          # Alembic migration scripts
│   └── versions/                     # Migration files
├── api/
│   ├── main.py                       # FastAPI app + lifespan + CORS + router registration
│   ├── models.py                     # Pydantic response models (SongResponse, SongSearchResponse, SongPlaylistAppearance, etc.)
│   └── v1/
│       ├── playlists.py              # GET /playlists/years, GET /playlists, GET /playlists/{date}
│       └── songs.py                  # GET /songs?q=, GET /songs/{id}/playlists
├── core/
│   ├── config.py                     # pydantic-settings, loads from .env
│   ├── database.py                   # Async engine, AsyncSessionLocal, get_session()
│   └── models.py                     # SQLModel table models: Song, Playlist, PlaylistSong
├── orchestrator/
│   └── __main__.py                   # Runnable: finds unpushed playlists, enqueues arq tasks
├── repository/
│   ├── playlist_repo.py              # PlaylistRepository + PlaylistSongRepository
│   └── song_repo.py                  # SongRepository
├── scraper/
│   ├── __main__.py                   # Runnable entrypoint (asyncio.run)
│   ├── client.py                     # ScraperClient — httpx async, semaphore concurrency
│   └── parser.py                     # Pure parsing functions, no DB/network deps
├── spotify/
│   └── client.py                     # SpotifyClient — token refresh, search, create playlist, add tracks
├── ui/                               # React frontend (Vite + Tailwind v4)
│   ├── src/
│   ├── api/client.ts             # Typed API client for FastAPI backend
│   │   ├── components/               # Header, SearchBar, YearSelector, PlaylistCard, SongRow, SearchResults
│   │   ├── pages/
│   │   │   ├── Home.tsx              # Main page — year browsing, search, URL state sync
│   │   │   └── PlaylistPage.tsx      # Playlist detail view (linked from search results)
│   │   ├── App.tsx                   # Router (/, /playlist/:date)
│   │   ├── main.tsx                  # Entry point
│   │   ├── index.css                 # Dark graveyard/fog theme
│   │   └── vite-env.d.ts            # TypeScript declarations for CSS imports
│   ├── package.json
│   └── vite.config.js                # Proxies /v1 to FastAPI on port 8000
├── worker/
│   ├── celery_app.py                 # Unused — replaced by arq
│   └── tasks.py                      # push_playlist arq task + WorkerSettings
├── .env                              # Credentials — never commit
├── alembic.ini                       # Alembic config — DB URL set programmatically from .env
├── requirements.txt
├── spotify_auth.py                   # One-time OAuth script to get Spotify refresh token
└── README.md
```

## Database Schema
- **songs** — id, artist, title, spotify_id, spotify_searched_at. Unique on (artist, title)
- **playlists** — id, date, spotify_id, scraped_at, pushed_at. Unique on date
- **playlist_songs** — id, playlist_id, song_id, position, is_request, spotify_track_id. Unique on (playlist_id, song_id)

## Migrations (in order)
1. `64a8c7dd130f` — initial schema (songs, playlists, playlist_songs)
2. `21c67b0d2bf0` — add spotify_track_id to playlist_songs
3. `860ede019435` — add synced_at to playlists (later renamed)
4. `e36b1a723652` — rename synced_at to pushed_at
5. `7795b47c503c` — add spotify_searched_at to songs

## Locked-In Design Decisions
1. **API models vs table models** — separate Pydantic response models in `api/models.py`. DB schema changes must not automatically affect the API contract.
2. **Repository pattern** — class-based, session injected at construction e.g. `PlaylistRepository(session)`. All DB access goes through repositories only.
3. **Upsert strategy** — `INSERT ... ON CONFLICT DO NOTHING RETURNING id`, fallback `SELECT` on conflict. One round trip in the happy path.
4. **Async throughout** — fully async stack: asyncpg, SQLAlchemy async, httpx, arq. Celery was considered and rejected in favour of arq for native async compatibility.
5. **Scraper idempotency** — `scraped_at IS NOT NULL` check before re-scraping. Concurrency limited to 3 to avoid overwhelming the Death Guild server.
6. **Push idempotency** — `pushed_at` timestamp on Playlist. Per-song tracking via `spotify_track_id` on PlaylistSong enables mid-playlist resume on retry.
7. **Race condition protection** — `SELECT FOR UPDATE` on Playlist row at task start prevents duplicate Spotify playlists under concurrent workers.
8. **YouTube links** — computed at response time from artist+title, always present. No API or storage needed.
9. **Spotify links** — computed at response time from spotify_id, only present when id is set.
11. **Hybrid search with two-tier drill-down** — song search returns occurrence counts per song. Playlist appearances are a separate endpoint (`/songs/{id}/playlists`) to keep search payloads small since high-frequency songs appear in 800+ playlists.
12. **UI search state in URL** — search query synced to URL query params (`/?q=bauhaus`) so browser back button restores search results after drilling into a playlist detail page.
13. **UI TypeScript** — migrated from JSX to TSX early while component count was small. All API responses have typed interfaces.
14. **Song resolution separate from playlist push** — `resolve_songs` module resolves Spotify IDs for all songs in one pass (~13k searches) rather than re-searching per playlist_song link (~108k). Songs not found are marked with `spotify_searched_at` and can be retried independently.

## Key Rules (also in .amazonq/rules/project_rules.md)
- Before implementing any ambiguous design decision, stop, flag it, describe options and tradeoffs, wait for a decision
- Always ON CONFLICT DO NOTHING or upsert — never plain INSERT in the scraper
- Strictly use SQLModel/SQLAlchemy expression language — never f-strings or raw SQL
- All DB access through repository layer only
- All Spotify API calls handle 429 via tenacity with Retry-After header
- All credentials via pydantic-settings from .env — no hardcoded values
- FastAPI: GET endpoints only
- API response shapes are separate Pydantic models, not SQLModel table models
- After every `alembic revision --autogenerate`, replace `sqlmodel.sql.sqltypes.AutoString()` with `sa.String()` before running `alembic upgrade head`

## Current Data State
- ~1530 playlists scraped (includes some future dates filtered at API level)
- ~13,000+ songs
- ~108,000+ playlist_song links
- 0 playlists pushed to Spotify (blocked by Spotify Premium requirement)

## What Has Been Built
- [x] Full project structure
- [x] core/config.py, core/models.py, core/database.py
- [x] Alembic configured and all migrations applied
- [x] repository/playlist_repo.py — PlaylistRepository + PlaylistSongRepository
- [x] repository/song_repo.py — SongRepository
- [x] scraper/ — full async scraper, idempotent, concurrency-limited
- [x] spotify/client.py — SpotifyClient with token refresh, search, playlist creation, track adding
- [x] spotify_auth.py — one-time OAuth flow to get refresh token
- [x] worker/tasks.py — push_playlist arq task with retry, per-song tracking, race condition protection
- [x] orchestrator/ — enqueues unpushed playlists to arq/Redis
- [x] api/main.py — FastAPI app
- [x] api/models.py — SongResponse, PlaylistSummaryResponse, PlaylistDetailResponse with computed YouTube/Spotify URLs
- [x] api/v1/playlists.py — GET /v1/playlists (paginated), GET /v1/playlists/{date}
- [x] api/v1/songs.py — GET /v1/songs?q= (search by artist or title)
- [x] api/v1/songs.py — GET /v1/songs?q= with occurrence counts, GET /v1/songs/{id}/playlists
- [x] api/models.py — SongSearchResponse (with occurrence_count), SongPlaylistAppearance
- [x] README.md — full setup and run instructions with design rationale
- [x] ui/ — React + TypeScript + Vite + Tailwind v4 with dark graveyard/fog theme
- [x] ui: hybrid search — song results with occurrence counts, expandable playlist appearances
- [x] ui: playlist detail page — linked from search result drill-down, with browser-back support
- [x] ui: URL state sync — search query and year preserved in URL params
- [x] resolve_songs/ — standalone module to resolve Spotify IDs for songs (initial + retry modes)
- [x] CORS middleware on FastAPI for Vite dev server

## UI Design
- Dark graveyard/fog-machine aesthetic
- Centered Death Guild logo (placeholder for now) in header
- Horizontal year pill selector below header — playlists grouped by year to avoid a flat list of ~1500 items
- Search bar above playlist cards — searches by artist, song, date
- Playlist cards: collapsed by default (date + song count), expand on click to lazy-load full setlist
- Song rows: position, artist, title, Spotify link (if exists), YouTube link (always)
- Hybrid search: song-centric results sorted by occurrence count, expandable to show every playlist appearance
- Playlist dates in search results link to a dedicated detail page with full setlist
- Search and year browsing are mutually exclusive — searching clears the year filter to avoid confusing mixed results
- Search state preserved in URL params so browser back/forward restores results after drill-down
- Custom Tailwind color palette: crypt, fog, tombstone, bone, ghost, blood, spotify-green, youtube-red

## What Is Next
- [ ] Run resolve_songs to populate spotify_id on songs
- [ ] Update playlist push worker to use pre-resolved spotify_ids instead of searching per song
- [ ] Spotify Premium — run `python spotify_auth.py`, then resolve_songs, then orchestrator + worker
- [ ] Deployment — Cloudflare Pages (static UI) + Fly.io (API) + Neon (Postgres), all free tier
- [ ] Caching — add Redis cache to API endpoints once traffic patterns are known

## Known Issues / Notes
- Spotify February 2026 API changes: `/playlists/{id}/tracks` deprecated, now `/playlists/{id}/items`. Already updated in spotify/client.py.
- Spotify Premium required for playlist creation in dev mode apps — this is a Spotify policy change from early 2026.
- `worker/celery_app.py` exists but is unused — left as a placeholder comment. Can be deleted.
- SQLModel 0.0.37 + Pydantic 2.12 incompatibility with forward-referenced Relationship fields — resolved by removing Relationship fields from models entirely. ORM relationships are not used anywhere in the codebase.

## Running the Project

### Scraper
```bash
python -m scraper
```

### Worker
```bash
python -m arq worker.tasks.WorkerSettings
```

### Orchestrator (run after worker is started)
```bash
python -m orchestrator
```

### API
```bash
uvicorn api.main:app --reload
```

### UI (from project root)
```bash
cd ui && npm run dev
```

### One-time Spotify auth
```bash
python spotify_auth.py
```

## .env Template
```
DATABASE_URL=postgresql+asyncpg://dg:<password>@localhost:5432/deathguild
REDIS_URL=redis://localhost:6379/0
SPOTIFY_CLIENT_ID=<spotify_client_id>
SPOTIFY_CLIENT_SECRET=<spotify_client_secret>
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback
SPOTIFY_REFRESH_TOKEN=<from spotify_auth.py>
```
