# Arc Reactor

A conversational AI platform that enables wet lab scientists at Arc Institute to run Nextflow bioinformatics pipelines on Google Cloud Platform without requiring command-line expertise.

## Overview

Arc Reactor bridges the gap between sample data in Benchling LIMS and computational analysis pipelines. Scientists describe their data in natural language, and an AI assistant handles the translation to technical configuration—searching Benchling for samples, generating samplesheets, configuring pipeline parameters, and submitting jobs to GCP Batch.

### Key Features

- **Conversational Interface**: Natural language interaction for pipeline configuration ("Run scRNA-seq on my NovaSeq samples from last week")
- **Sample Discovery**: AI-powered search across Benchling data warehouse to find NGS runs, samples, and FASTQ paths
- **Automated File Generation**: Samplesheets and Nextflow configs generated from discovered data
- **Human-in-the-Loop Editing**: Review and modify generated files before submission via spreadsheet and code editors
- **Pipeline Execution**: Submit jobs to GCP Batch with real-time status monitoring
- **Run History**: Track all pipeline runs with filtering, logs, and output file access

### Target Users

- **Wet Lab Scientists**: Primary users who run standard analysis pipelines on their sequencing data
- **Computational Biologists**: Configure new pipelines and troubleshoot complex failures

## Architecture

Arc Reactor is deployed as three Cloud Run services behind a global load balancer with IAP authentication:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Global Load Balancer (IAP)                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend    │     │     Backend     │     │ Weblog Receiver │
│  (Next.js)    │     │    (FastAPI)    │     │   (FastAPI)     │
│  Static SPA   │     │  REST/WS/SSE    │     │  Pub/Sub ingest │
└───────────────┘     └────────┬────────┘     └─────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
      ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
      │  Cloud SQL  │  │     GCS     │  │  GCP Batch  │
      │ (PostgreSQL)│  │  (Storage)  │  │  (Compute)  │
      └─────────────┘  └─────────────┘  └─────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 (App Router, static export), Tailwind CSS, Zustand |
| Backend | FastAPI, Dynaconf, SQLAlchemy (async), Alembic |
| AI/Agent | LangChain v1, DeepAgents, Google Gemini |
| Database | PostgreSQL (Cloud SQL) |
| Storage | Google Cloud Storage |
| Compute | GCP Batch, Nextflow |
| Auth | Google IAP, OIDC |
| External | Benchling Data Warehouse (via benchling-py) |

## Project Structure

```
arc-reactor/
├── backend/
│   ├── agents/           # AI agent, tools, subagents, prompts
│   │   ├── tools/        # Benchling discovery, file generation, submission
│   │   └── subagents/    # benchling_expert, config_expert
│   ├── api/
│   │   └── routes/       # REST endpoints (health, runs, users, chat)
│   ├── models/           # SQLAlchemy models (runs, users, tasks, checkpoints)
│   ├── services/         # External service integrations
│   │   ├── benchling.py  # Benchling data warehouse queries
│   │   ├── database.py   # PostgreSQL connection management
│   │   ├── storage.py    # GCS file operations
│   │   └── gemini.py     # LLM client
│   ├── migrations/       # Alembic database migrations
│   ├── config.py         # Dynaconf settings loader
│   ├── settings.yaml     # Environment configuration
│   └── main.py           # FastAPI application factory
│
├── frontend/
│   ├── app/              # Next.js App Router pages
│   │   ├── workspace/    # Main pipeline workspace
│   │   └── runs/         # Run history and details
│   ├── components/       # React components
│   │   ├── workspace/    # Chat panel, file editors, submit panel
│   │   ├── runs/         # Run list, status, logs
│   │   └── layout/       # Header, sidebar, footer
│   ├── hooks/            # Custom React hooks
│   ├── stores/           # Zustand state stores
│   └── lib/              # API client, utilities
│
├── orchestrator/         # Nextflow orchestrator container
├── terraform/            # Infrastructure as code
├── SPEC/                 # Architecture and feature specifications
├── plan/                 # Sprint planning documents
└── docs/                 # Additional documentation
```

## Local Development

### Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.10+** with virtual environment (for running backend outside Docker)
- **Node.js 20+** (for running frontend outside Docker)

### Quick Start

1. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

2. **Start all services**:
   ```bash
   export BENCHLING_TEST_DATABASE_URI='postgresql://...'   # provide full URL; need to deal with $
   docker compose up --build
   ```

3. **Run database migrations** (first time only):
   ```bash
   docker compose exec backend alembic upgrade head
   ```

**Services:**
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api |
| Backend Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### Environment Variables

Create a `.env` file in the project root:

| Variable | Required | Description |
|----------|----------|-------------|
| `DYNACONF` | Yes | Environment: `test`, `dev`, or `prod` |
| `GOOGLE_API_KEY` | Yes* | Gemini API key for AI features |
| `BENCHLING_TEST_API_KEY` | Yes* | Benchling API key |
| `BENCHLING_TEST_DATABASE_URI` | Yes* | Benchling data warehouse URI |
| `BENCHLING_TEST_APP_CLIENT_ID` | Yes* | Benchling app client ID |
| `BENCHLING_TEST_APP_CLIENT_SECRET` | Yes* | Benchling app client secret |
| `ARC_REACTOR_NEXTFLOW_BUCKET` | No | Override GCS bucket for testing |

*Required for full functionality. The app starts without these but certain features will be unavailable.

For production, use `BENCHLING_PROD_*` equivalents.

### Development with Hot-Reloading

For faster iteration, run frontend and backend natively while using Docker for PostgreSQL:

1. **Start PostgreSQL only**:
   ```bash
   docker compose up postgres -d
   ```

2. **Set database URL**:
   ```bash
   export DATABASE_URL="postgresql://arc_reactor:arc_reactor@localhost:5432/arc_reactor"
   ```

3. **Run migrations**:
   ```bash
   cd backend && alembic upgrade head && cd ..
   ```

4. **Start backend** (terminal 1):
   ```bash
   source .venv/bin/activate
   uvicorn backend.main:app --reload --port 8000
   ```

5. **Start frontend** (terminal 2):
   ```bash
   cp frontend/.env.example frontend/.env.local  # first time only
   cd frontend && npm install && npm run dev
   ```

### Troubleshooting

**Frontend WebSocket connection fails**

Ensure `frontend/.env.local` exists:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

**Database connection issues**
```bash
# Check PostgreSQL is running
docker compose ps

# Reset database if needed
docker compose down -v
docker compose up postgres -d
```

## Testing

```bash
# Backend tests
cd backend && pytest

# Skip integration tests (no external services)
cd backend && pytest -m "not integration"

# Frontend tests
cd frontend && npm test
```

## Smoke Test

Verify a deployment:
```bash
python scripts/smoke_test.py --base-url http://localhost:8000
```

## Documentation

| Document | Description |
|----------|-------------|
| `SPEC/01-project-overview.md` | Project goals and capabilities |
| `SPEC/02-architecture-overview.md` | System architecture details |
| `SPEC/05-agentic-features-spec.md` | AI agent design and tools |
| `SPEC/06-data-model-spec.md` | Database schema |
| `docs/benchling-py-usage.md` | Benchling query examples |
| `plan/` | Sprint planning and implementation status |