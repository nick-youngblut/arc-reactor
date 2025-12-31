# Backend Guidelines

## Project Structure
- FastAPI app lives in `backend/`.
- Core files: `main.py`, `config.py`, `settings.yaml`, `dependencies.py`, `context.py`.
- API routes live under `backend/api/routes/`.
- Business logic lives under `backend/services/`.
- Agent code lives under `backend/agents/`.

## Development Commands
- Install (dev): `uv pip install -e 'backend/.[dev]'`
- Run (dev): `uvicorn backend.main:app --reload --port 8000`
- Tests: `cd backend && pytest`

## Coding Style
- Black line length 100.
- Ruff with `E`, `F`, `I` rules.
- Use `snake_case` for functions/vars and `PascalCase` for classes.

## Testing
- Put tests in `backend/tests/` with `test_*.py`.
- Prefer async tests with `pytest-asyncio` when applicable.
