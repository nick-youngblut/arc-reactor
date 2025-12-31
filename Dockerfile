# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

COPY frontend ./
RUN rm -f .env .env.* || true
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend /app/backend

RUN --mount=type=secret,id=GITHUB_TOKEN \
    GITHUB_TOKEN=$(cat /run/secrets/GITHUB_TOKEN) \
    pip install --no-cache-dir -e ./backend

COPY --from=frontend-build /app/frontend/out /app/frontend/out

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    FRONTEND_OUT_DIR=/app/frontend/out \
    ARC_REACTOR_FRONTEND_OUT_DIR=/app/frontend/out

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
