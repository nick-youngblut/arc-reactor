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

## Check server health & readiness

```bash
curl http://localhost:8000/health
```

```bash
curl http://localhost:8000/ready
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
- `DYNACONF` (dev/prod/test)
- `GOOGLE_API_KEY` (Gemini auth)
- `DATABASE_URL` or DB_* settings
- `IAP_PROJECT_NUMBER`, `IAP_PROJECT_ID` (IAP JWT audience)
- `IAP_ALLOWED_DOMAIN` (optional)

Benchling (based on `DYNACONF`):
- `DYNACONF=prod`:
  - `BENCHLING_PROD_API_KEY`
  - `BENCHLING_PROD_DATABASE_URI`
  - `BENCHLING_PROD_APP_CLIENT_ID`
  - `BENCHLING_PROD_APP_CLIENT_SECRET`
- `DYNACONF=dev` or `DYNACONF=test`:
  - `BENCHLING_TEST_API_KEY`
  - `BENCHLING_TEST_DATABASE_URI`
  - `BENCHLING_TEST_APP_CLIENT_ID`
  - `BENCHLING_TEST_APP_CLIENT_SECRET`

## Migrations
```bash
cd backend
alembic upgrade head
```
