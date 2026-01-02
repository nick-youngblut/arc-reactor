# Arc Reactor

## Local Development

### Environment Variables
Set the following variables in your local shell or `.env` files:
- `DYNACONF=test` (or `dev`; `prod` is reserved for production)
- `BENCHLING_TEST_API_KEY`
- `BENCHLING_TEST_DATABASE_URI`
- `BENCHLING_TEST_APP_CLIENT_ID`
- `BENCHLING_TEST_APP_CLIENT_SECRET`
- `GOOGLE_API_KEY` (Gemini auth)
- `DATABASE_URL` (preferred) or `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`
- `ARC_REACTOR_NEXTFLOW_BUCKET` (override for GCS testing)

For production, set the `BENCHLING_PROD_*` equivalents instead of the test keys.

See `docs/benchling-py-usage.md` for query examples and `docs/benchling-local-migration.md`
for upgrading local dev setup.

### Docker Compose
```bash
docker compose up --build
```
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Postgres: `localhost:5432`

### Offline Development / Mocking
- For external services (Benchling, GCS, Gemini), keep credentials unset and run tests without the `integration` marker.
- Integration tests are skipped automatically unless the required environment variables are present.

## Tests
```bash
cd backend && pytest
cd frontend && npm test
```

## Smoke Test
```bash
python scripts/smoke_test.py --base-url http://localhost:8000
```
