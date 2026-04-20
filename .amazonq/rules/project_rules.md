# Deathguild Music Service — Project Rules

## Language & Runtime
- Python 3.12+, fully async where applicable

## Database
- PostgreSQL via SQLModel (SQLAlchemy + Pydantic)
- Always use ON CONFLICT DO NOTHING or upsert logic in the scraper to prevent duplicate entries
- Strictly use SQLModel/SQLAlchemy expression language for all queries — never use f-strings or raw string formatting to build SQL
- All DB access goes through the repository layer only
- After every `alembic revision --autogenerate`, replace any `sqlmodel.sql.sqltypes.AutoString()` in the generated file with `sa.String()` before running `alembic upgrade head`

## API
- FastAPI, read-only: only GET endpoints are permitted
- API response shapes must be separate Pydantic models, distinct from SQLModel table models — DB schema changes must not automatically affect the API contract
- No raw dicts returned from endpoints

## Scraper
- Use httpx (async) for all network calls, including the index page URL fetch — do not mix in requests or any sync HTTP library
- Scraping logic (parser.py) must be pure functions with no DB or network dependencies
- Network logic (client.py) must have no parsing or DB dependencies
- Idempotency: check scraped_at IS NOT NULL before re-scraping a playlist
- Parser error handling: on a malformed or unparseable playlist page, log the error and skip to the next URL — do not halt the run

## Spotify / Worker
- All Spotify API calls must handle 429 responses by reading the Retry-After header
- Use tenacity for retry logic with exponential backoff
- Celery + Redis for task queuing

## Documentation
- The README must always be kept up to date with: all dependencies, how to install them, how to configure `.env`, and how to run each module (scraper, worker, API)
- Any new runnable module or setup step must be added to the README before or alongside the code
- HANDOFF.md must be updated whenever a major design change is made — this is the primary recovery document if chat context is lost

## Collaboration
- Before implementing any design decision that is ambiguous or has multiple valid approaches, stop and flag it explicitly. Describe the options and tradeoffs, and wait for a decision before writing code.

## Architecture
- Repository pattern: scraper and API never touch the DB directly, only via repository classes
- Repositories are class-based: session is injected at construction (e.g. PlaylistRepository(session))
- Prefer class and object-based design throughout — avoid standalone functions where a class provides better encapsulation
- Keep scraper, worker, and API as independently runnable modules
- All credentials and config via pydantic-settings from .env — no hardcoded values anywhere
