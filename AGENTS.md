# Repository Guidelines

## Project Structure & Module Organization
- Root: Dockerfile, env files, shared docs.
- `SPEC/`: Specification documents.
- `backend/`: FastAPI app (`main.py`), agents (`agents/`), routes (`api/`), tools (`tools/`), services (`services/`), settings (`settings.yml`).
- `frontend/`: Next.js (App Router) with `app/`, `components/`, `hooks/`, `stores/`, `lib/`.

## Build, Test, and Development Commands
- Backend install (dev): `uv pip install -e 'backend/.[dev]'`
- Run backend (dev): `uvicorn backend.main:app --reload --port 8000`
- Frontend dev: `cd frontend && npm install && npm run dev`
- Backend tests: `cd backend && pytest`
- Frontend tests: `cd frontend && npm test`

## Coding Style & Naming Conventions
- Python: Black (line length 100), Ruff for lint. Use `snake_case` for functions/vars, `PascalCase` for classes, module names in `snake_case`.
- TypeScript/React: ESLint + Prettier (Tailwind plugin enabled). Use `PascalCase` for components, `camelCase` for hooks/variables, files in `app/components` typically `PascalCase.tsx`.
- Imports: prefer absolute within each package’s root; avoid deep relative chains.

## Testing Guidelines
- Backend: `uv run pytest` (async supported). Place tests under `backend/tests/` using `test_*.py`. Use fixtures for HTTP clients and mock external services (Weaviate, Asana, Benchling, Notion).
- Frontend: Jest + `jest-environment-jsdom`. Co-locate as `*.test.ts(x)` or under `frontend/__tests__/`.
- Add tests for new logic and bug fixes; include minimal coverage for agents, tools, and API routes.
- Be sure to activate the uv virtual environment before running tests: `source .venv/bin/activate`

## Commit & Pull Request Guidelines
- Messages: imperative, concise, present tense. Optional scope prefix: `backend:`, `frontend:`, `docs:`, `ci:` (e.g., `backend: add Benchling query tool`).
- PRs: clear description, linked issues, reproduction steps, and screenshots/GIFs for UI changes. Note environment or migration impacts. Include test updates and manual QA notes.

## Security & Configuration Tips
- Do not commit secrets. Use `backend/.env` and `frontend/.env.local`; keep keys in your local environment/secret store. Copy templates if provided.
