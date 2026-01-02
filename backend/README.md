# Arc Reactor Backend

FastAPI service for Arc Reactor. Provides REST APIs, WebSocket chat, and serves the static Next.js build.

## Structure
- `api/routes/`: FastAPI route handlers
- `models/`: SQLAlchemy models + Pydantic schemas
- `services/`: Database, storage, Benchling, pipelines, logs
- `utils/`: Auth, errors, circuit breakers
- `migrations/`: Alembic migrations

## Development
```bash
# install
uv pip install -e 'backend/.[dev]'

# run
uvicorn backend.main:app --reload --port 8000
```

## Tests
```bash
# activate venv if needed
source .venv/bin/activate
cd backend
pytest
```

## Configuration
Settings are managed via `backend/settings.yaml` and env vars. Key env vars:
- `DYNACONF` (dev/prod)
- `DATABASE_URL` or DB_* settings
- `BENCHLING_WAREHOUSE_PASSWORD`
- `IAP_PROJECT_NUMBER`, `IAP_PROJECT_ID` (IAP JWT audience)
- `IAP_ALLOWED_DOMAIN` (optional)

## Migrations
```bash
cd backend
alembic upgrade head
```
