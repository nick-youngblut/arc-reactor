# Arc Reactor - Backend Specification

## Overview

The backend is a FastAPI application that serves three primary functions:

1. **API Server**: REST endpoints for run management, pipeline configuration, and data queries
2. **WebSocket Server**: Real-time chat interface for the AI agent
3. **Internal Event Processor**: OIDC-protected endpoints for Pub/Sub weblog events and scheduler reconciliation

The backend follows Arc Institute's established patterns for internal applications, using Dynaconf for configuration, Pydantic for validation, and async throughout. The frontend is deployed as a separate Cloud Run service behind the same load balancer.

## Project Structure

```
backend/
├── __init__.py
├── main.py                 # Application factory, lifespan, CORS, routing
├── config.py               # Dynaconf settings
├── settings.yaml           # Environment configuration
├── dependencies.py         # FastAPI dependency injection
├── context.py              # Shared context for agents
│
├── api/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── chat.py         # WebSocket chat endpoint
│       ├── runs.py         # Run CRUD operations
│       ├── tasks.py        # Task-level queries
│       ├── logs.py         # Log streaming and task log endpoints
│       ├── pipelines.py    # Pipeline registry endpoints
│       ├── health.py       # Health check endpoints
│       └── internal/       # OIDC-protected internal endpoints
│           ├── __init__.py
│           ├── weblog.py   # Pub/Sub weblog event processor
│           └── reconcile.py# Stale run reconciliation
│
├── models/
│   ├── __init__.py
│   ├── runs.py             # Run request/response models
│   ├── tasks.py            # Task models
│   ├── weblog_event_log.py # Weblog deduplication model
│   ├── pipelines.py        # Pipeline configuration models
│   ├── chat.py             # Chat message models
│   └── benchling.py        # Benchling data models
│
├── services/
│   ├── __init__.py
│   ├── benchling.py        # Benchling data warehouse queries
│   ├── batch.py            # GCP Batch job management
│   ├── runs.py             # Run persistence (Cloud SQL PostgreSQL)
│   ├── run_events.py       # SSE streaming for run status
│   ├── logs.py             # Log access + streaming
│   ├── storage.py          # GCS file operations
│   └── pipelines.py        # Pipeline registry and templates
│
├── agents/
│   ├── __init__.py
│   ├── pipeline_agent.py   # Main DeepAgent orchestrator
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── benchling_tools.py    # Sample search tools
│   │   ├── generation_tools.py   # File generation tools
│   │   ├── validation_tools.py   # Input validation tools
│   │   └── submission_tools.py   # Run submission tools
│   └── subagents/
│       ├── __init__.py
│       ├── benchling_expert.py   # Complex sample queries
│       └── config_expert.py      # Pipeline configuration help
│
└── utils/
    ├── __init__.py
    ├── auth.py             # IAP authentication utilities
    ├── logging.py          # Structured logging
    └── errors.py           # Custom exception handlers
```

## Configuration

### Settings Management

Configuration uses Dynaconf with environment-based overrides.

#### Shared Configuration Source

Canonical AI configuration values (model ID, temperature, max tokens) are defined
in `SPEC/11-conf-spec.md`. Backend settings and examples must reference those
values to avoid drift across specifications.

```yaml
# settings.yaml
default:
  app_name: "Arc Reactor"
  debug: false
  
  # GCP Configuration
  gcp_project: "arc-genomics02"
  gcp_region: "us-west1"
  
  # Service Configuration
  nextflow_bucket: "arc-reactor-runs"
  nextflow_service_account: "nextflow-orchestrator@arc-genomics02.iam.gserviceaccount.com"
  orchestrator_image: "us-docker.pkg.dev/arc-genomics02/arc-reactor/nextflow-orchestrator:latest"
  
  # Benchling Configuration
  # Benchling settings are sourced via benchling-py Dynaconf (DYNACONF env var)
  
  # AI Configuration (Google Gemini)
  gemini_model: "gemini-3-flash-preview"
  gemini_thinking_level: "low"  # minimal, low, medium, high

  # Legacy Anthropic (for fallback/comparison)
  # anthropic_model: "claude-sonnet-4-5-20250929"

  # Circuit Breakers
  benchling_cb_failure_threshold: 5
  benchling_cb_recovery_timeout: 30
  gemini_cb_failure_threshold: 3
  gemini_cb_recovery_timeout: 60
  
  # Frontend
  frontend_out_dir: "/app/frontend/out"
  cors_allowed_origins:
    - "https://arc-reactor.arcinstitute.org"
    - "http://localhost:3000"

dev:
  debug: true
  nextflow_bucket: "arc-reactor-runs-dev"

prod:
  debug: false
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DYNACONF` | Benchling config environment (`test`, `dev`, `prod`) | Yes |
| `GOOGLE_API_KEY` | Google AI API key | Yes* |
| `BENCHLING_TEST_API_KEY` | Benchling test API key | Yes (test/dev) |
| `BENCHLING_TEST_DATABASE_URI` | Benchling test DB URI | Yes (test/dev) |
| `BENCHLING_TEST_APP_CLIENT_ID` | Benchling test OAuth client ID | Yes (test/dev) |
| `BENCHLING_TEST_APP_CLIENT_SECRET` | Benchling test OAuth client secret | Yes (test/dev) |
| `BENCHLING_PROD_API_KEY` | Benchling prod API key | Yes (prod) |
| `BENCHLING_PROD_DATABASE_URI` | Benchling prod DB URI | Yes (prod) |
| `BENCHLING_PROD_APP_CLIENT_ID` | Benchling prod OAuth client ID | Yes (prod) |
| `BENCHLING_PROD_APP_CLIENT_SECRET` | Benchling prod OAuth client secret | Yes (prod) |
| `GCP_PROJECT` | GCP project ID (override) | No |

*`GOOGLE_API_KEY` is required to use Gemini.

## CORS Configuration

The backend must allow the frontend origin(s) explicitly to support local
development and production deployments.

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## API Endpoints

### Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/ready` | GET | Readiness check (critical dependencies gate 200 vs 503, non-critical mark degraded) |

### Run Management

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `GET /api/runs` | GET | List runs (with filters) | Required |
| `GET /api/runs/{id}` | GET | Get run details | Required |
| `POST /api/runs` | POST | Submit new run | Required |
| `DELETE /api/runs/{id}` | DELETE | Cancel run | Required |
| `POST /api/runs/{id}/recover` | POST | Recover run using `-resume` | Required |
| `GET /api/runs/{id}/files` | GET | List run files | Required |
| `GET /api/runs/{id}/events` | GET (SSE) | Stream run status updates | Required |

**Run Recovery:** See `SPEC/12-recovery-spec.md` for the `-resume` workflow and
recovery eligibility rules.

### Log Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `GET /api/runs/{id}/logs` | GET | Get workflow log (complete) | Required |
| `GET /api/runs/{id}/logs/stream` | GET (SSE) | Stream logs in real time | Required |
| `GET /api/runs/{id}/tasks` | GET | List tasks with metadata from trace | Required |
| `GET /api/runs/{id}/tasks/{task_id}/logs` | GET | Get task stdout/stderr | Required |
| `GET /api/runs/{id}/logs/download` | GET | Download logs archive | Required |

### Pipeline Management

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `GET /api/pipelines` | GET | List available pipelines | Required |
| `GET /api/pipelines/{name}` | GET | Get pipeline details | Required |
| `GET /api/pipelines/{name}/schema` | GET | Get samplesheet schema | Required |

### Chat

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `POST /api/chat` | POST | Chat with AI (streaming) | Required |
| `WS /ws/chat` | WebSocket | Real-time chat connection | Required |

### Benchling Data

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `GET /api/benchling/runs` | GET | List NGS runs | Required |
| `GET /api/benchling/runs/{name}/samples` | GET | Get samples for run | Required |
| `GET /api/benchling/metadata` | GET | Get metadata options | Required |
| `GET /api/benchling/entities/{entity_id}` | GET | Get entity by ID | Required |
| `GET /api/benchling/entities/{entity_id}/relationships` | GET | Get related entities | Required |
| `GET /api/benchling/entities/{entity_id}/lineage` | GET | Get ancestor lineage | Required |

## Frontend Integration

The backend is responsible for serving the compiled frontend application. Because the frontend uses client-side routing (Next.js App Router with static export), the backend must handle deep links to dynamic routes (e.g., `/runs/abc123`) by serving the entry point.

### Static Asset Serving

The backend mounts the static build output (default: `frontend/out`) to the root path.

1. **Assets**: `/next/`, `/assets/`, and root files (favicon, logo) are served directly.
2. **SPA Fallback**: Any request that does not match an API route (`/api/*`) or a static file must return `index.html`. This allows the client-side router to handle the URL.

```python
# Backend implementation pattern for SPA Routing
from fastapi.staticfiles import StaticFiles

# 1. Mount static assets (exclude root to avoid capturing everything)
app.mount("/_next", StaticFiles(directory=f"{dist_dir}/_next"), name="next")

# 2. Catch-all route for SPA fallback
@app.get("/{full_path:path}")
async def serve_spa_app(full_path: str):
    # Check if file exists in static dir
    file_path = dist_dir / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    
    # Otherwise serve index.html for client-side routing
    return FileResponse(dist_dir / "index.html")
```

## Request/Response Models

### Run Models

```python
class RunStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RunCreateRequest(BaseModel):
    pipeline: str                    # e.g., "nf-core/scrnaseq"
    pipeline_version: str            # e.g., "2.7.1"
    samplesheet_csv: str             # CSV content
    config_content: str              # Nextflow config content
    params: dict[str, Any]           # Pipeline parameters

class RunResponse(BaseModel):
    run_id: str
    pipeline: str
    pipeline_version: str
    status: RunStatus
    user_email: str
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    gcs_path: str
    sample_count: int
    params: dict[str, Any]
    parent_run_id: str | None
    is_recovery: bool
    recovery_notes: str | None
    reused_work_dir: str | None

class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int
    page: int
    page_size: int

class LogEntry(BaseModel):
    timestamp: datetime
    source: Literal["nextflow", "task", "batch"]
    message: str
    task_name: str | None = None
    stream: Literal["stdout", "stderr"] | None = None

class TaskInfo(BaseModel):
    task_id: str
    name: str
    process: str
    status: str
    exit_code: int | None
    duration: str | None
    cpu_percent: str | None
    memory_peak: str | None
    start_time: str | None
    end_time: str | None
    work_dir: str | None
    has_logs: bool

class TaskLogs(BaseModel):
    task_id: str
    stdout: str
    stderr: str
```

### Pipeline Models

```python
class PipelineParam(BaseModel):
    name: str
    type: str                        # string, integer, boolean, enum
    description: str
    required: bool
    default: Any | None
    options: list[str] | None        # For enum types

class SamplesheetColumn(BaseModel):
    name: str
    description: str
    required: bool
    type: str                        # string, integer, path

class PipelineSchema(BaseModel):
    name: str
    display_name: str
    description: str
    repository: str
    versions: list[str]
    default_version: str
    samplesheet_columns: list[SamplesheetColumn]
    required_params: list[PipelineParam]
    optional_params: list[PipelineParam]
```

### Chat Models

```python
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    tool_calls: list[ToolCall] | None

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    thread_id: str | None

class GeneratedFile(BaseModel):
    type: Literal["samplesheet", "config"]
    content: str
    metadata: dict[str, Any]         # sample_count, columns, etc.
```

## Services

### BenchlingService

Handles read-only Benchling access via `benchling-py`'s `BenchlingSession`.
All synchronous calls are wrapped in `asyncio.to_thread()` for FastAPI compatibility.

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `query()` | Execute SQL in Benchling warehouse (return_format selectable) | list[dict] / DataFrame / str |
| `get_entity()` | Fetch entity via Benchling API (read-only) | dict |
| `convert_fields_to_api_format()` | Convert system field names to API display names | dict |
| `get_ancestors()` | Traverse lineage via relationship fields | DataFrame / dict |
| `get_descendants()` | Traverse descendant relationships | DataFrame / dict |
| `get_related_entities()` | Resolve entity_link relationships | dict |
| `health_check()` | Validate warehouse connectivity | bool |

**Query Patterns:**

- All queries filter for `archived$ = FALSE`
- Complex queries use CTEs for readability
- Results cached for 5 minutes (metadata lookups)
- API routes should use `return_format="dict"`; agent tools should use `return_format="toon"`

### BatchService

Manages GCP Batch job submission and monitoring.

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `submit_run()` | Submit a new pipeline run | RunResponse |
| `get_run_status()` | Get current run status | RunStatus |
| `cancel_run()` | Cancel a running job | bool |
| `recover_run()` | Submit recovery run with `-resume` | RunResponse |
| `list_runs()` | List runs with filters | list[RunResponse] |
| `get_run_logs()` | Get Batch job log entries | list[LogEntry] |

**Job Configuration:**

- Orchestrator jobs use spot instances with retry
- Machine type: e2-standard-2 (sufficient for Nextflow orchestration)
- Max duration: 7 days
- Auto-delete on completion (logs preserved)

### StorageService

Manages GCS file operations.

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `upload_run_files()` | Upload samplesheet, config, params | list[str] |
| `get_run_files()` | List files for a run | list[FileInfo] |
| `get_file_content()` | Download file content | str |
| `generate_signed_url()` | Create signed URL for download | str |

**Bucket Structure (from `settings.nextflow_bucket`):**

```
gs://{settings.nextflow_bucket}/
└── runs/
    └── {run_id}/
        ├── inputs/
        │   ├── samplesheet.csv
        │   ├── nextflow.config
        │   └── params.yaml
        ├── work/                    # Nextflow work dir
        ├── results/                 # Pipeline outputs
        └── logs/
            ├── nextflow.log
            ├── trace.txt
            ├── timeline.html
            └── report.html
```

### RunStoreService (PostgreSQL)

Manages run persistence in Cloud SQL PostgreSQL.

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `create_run()` | Create run record | str (run_id) |
| `update_run_status()` | Update run status | bool |
| `get_run()` | Get run record | RunRecord |
| `list_runs()` | Query runs with filters | list[RunRecord] |
| `create_recovery_run()` | Create run record linked to parent | str (run_id) |

### RunEventService

Streams run status updates over SSE by polling PostgreSQL.

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `stream_run_events()` | Yield status changes | AsyncIterator[RunEvent] |

### LogService

Provides workflow and task log access across GCS and Cloud Logging.

**Log Sources and Access Patterns:**

| Log Source | Location | Access Method | Use Case |
|------------|----------|---------------|----------|
| Nextflow main log | GCS `logs/nextflow.log` | GCS API | Workflow progress |
| Nextflow trace | GCS `logs/trace.txt` | GCS API | Task metadata |
| Task stdout/stderr | Cloud Logging | Logging API | Per-task debugging |
| Batch job logs | Cloud Logging | Logging API | Infrastructure issues |

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `get_workflow_log()` | Fetch full `nextflow.log` from GCS | list[LogEntry] |
| `stream_workflow_log()` | Stream `nextflow.log` via polling | AsyncIterator[LogEntry] |
| `list_tasks()` | Parse `trace.txt` and return task metadata | list[TaskInfo] |
| `get_task_logs()` | Fetch stdout/stderr for a task | TaskLogs |
| `stream_task_logs()` | Stream task logs from Cloud Logging | AsyncIterator[LogEntry] |
| `create_log_archive()` | Build zip/tar archive for download | Path |

### PipelineRegistry

Manages pipeline configurations and templates.

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `list_pipelines()` | List all available pipelines | list[PipelineInfo] |
| `get_pipeline()` | Get pipeline configuration | PipelineConfig |
| `get_samplesheet_schema()` | Get column definitions | list[Column] |
| `render_config()` | Generate config from template | str |
| `validate_params()` | Validate pipeline parameters | ValidationResult |

**Initial Pipeline: nf-core/scrnaseq**

```python
SCRNASEQ_CONFIG = PipelineConfig(
    name="nf-core/scrnaseq",
    display_name="Single-cell RNA-seq",
    description="nf-core pipeline for single-cell RNA sequencing data analysis",
    repository="https://github.com/nf-core/scrnaseq",
    versions=["2.7.1", "2.6.0", "2.5.1"],
    default_version="2.7.1",
    samplesheet_columns=[
        Column("sample", "Sample identifier", required=True),
        Column("fastq_1", "Path to R1 FASTQ", required=True),
        Column("fastq_2", "Path to R2 FASTQ", required=True),
        Column("expected_cells", "Expected cell count", required=False),
    ],
    required_params=[
        Param("genome", "Reference genome", type="enum", 
              options=["GRCh38", "GRCm39"]),
        Param("protocol", "10x protocol version", type="enum",
              options=["10XV2", "10XV3", "10XV4"]),
    ],
    optional_params=[
        Param("aligner", "Alignment tool", type="enum",
              options=["simpleaf", "star", "kallisto", "cellranger"],
              default="simpleaf"),
        Param("expected_cells", "Default expected cells", type="integer",
              default=10000),
    ],
)
```

## WebSocket Chat Protocol

### Connection Flow

```
1. Client connects to /ws/chat
2. Server validates IAP token
3. Server sends connection acknowledgment
4. Client sends chat messages
5. Server streams AI responses
6. Either side can close connection
```

## Chat State Persistence

Conversation state is persisted in Cloud SQL PostgreSQL so reconnects can resume
the same thread.

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

DATABASE_URL = (
    "postgresql+asyncpg://{user}:{password}@/{db}"
    "?host=/cloudsql/{connection_name}"
)

async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
    agent = create_deep_agent(
        model=model,
        tools=tools,
        checkpointer=checkpointer,
    )
```

### Message Format (AI SDK Compatible)

**Client → Server:**
```json
{
  "type": "message",
  "content": "Find my samples from last week",
  "thread_id": "optional-thread-id"
}
```

**Server → Client (Streaming):**
```
0:"Hello"                              # Text chunk
0:", I'll search"                       # More text
9:{"toolCallId":"x","toolName":"search_ngs_runs","args":{}}  # Tool start
a:{"toolCallId":"x","result":"Found 3 runs..."}              # Tool result
0:" for your samples."                  # More text
d:{"finishReason":"stop"}              # Stream end
```

### Stream Format Codes

| Code | Meaning | Example |
|------|---------|---------|
| `0` | Text content | `0:"Hello world"` |
| `9` | Tool call start | `9:{"toolCallId":"...","toolName":"...","args":{}}` |
| `a` | Tool call result | `a:{"toolCallId":"...","result":"..."}` |
| `d` | Finish | `d:{"finishReason":"stop"}` |
| `3` | Error | `3:"Error message"` |

## Authentication & Authorization

### IAP Integration

All requests pass through GCP Identity-Aware Proxy.

**Header Extraction:**
```python
async def get_current_user(request: Request) -> User:
    jwt_assertion = request.headers.get("X-Goog-IAP-JWT-Assertion")
    if not jwt_assertion:
        raise HTTPException(401, "Missing IAP token")
    
    # Verify and decode JWT
    claims = verify_iap_jwt(jwt_assertion)
    
    return User(
        email=claims["email"],
        name=claims.get("name", claims["email"]),
    )
```

### Service-to-Service (OIDC) Integration

Internal endpoints under `/api/internal/*` accept OIDC Bearer tokens from specific service accounts (Pub/Sub push subscription and Cloud Scheduler). These endpoints are mounted separately from user-facing routes to ensure IAP and OIDC auth can be enforced independently.

### Authorization Rules

| Resource | Rule |
|----------|------|
| Own runs | Full access |
| Others' runs | Read-only (list, view) |
| Pipelines | Read-only |
| Benchling data | Read-only |

## Error Handling

### Standard Error Response

```python
class ErrorResponse(BaseModel):
    error: str
    detail: str | None
    code: str | None

# Example
{
  "error": "Run not found",
  "detail": "No run exists with ID abc123",
  "code": "RUN_NOT_FOUND"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `AUTH_REQUIRED` | 401 | Missing authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `BENCHLING_ERROR` | 502 | Benchling query failed |
| `BATCH_ERROR` | 502 | GCP Batch operation failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## Logging

### Structured Logging

All logs use structured JSON format for Cloud Logging.

```python
logger.info(
    "Run submitted",
    extra={
        "run_id": run_id,
        "pipeline": pipeline,
        "user_email": user.email,
        "sample_count": sample_count,
    }
)
```

### Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed diagnostic info |
| INFO | Normal operations (run submitted, completed) |
| WARNING | Recoverable issues (retry, degraded service) |
| ERROR | Failures (job failed, service unavailable) |

## Performance Considerations

### Caching Strategy

| Data | Cache Duration | Cache Location |
|------|----------------|----------------|
| Pipeline configs | Permanent | In-memory |
| Benchling metadata (projects, instruments) | 5 minutes | In-memory |
| User preferences | 1 minute | In-memory |
| Run status | No cache | SSE or polling from PostgreSQL |

### Connection Pooling

| Service | Pool Size | Timeout |
|---------|-----------|---------|
| Benchling DB | 5 connections | 30s |
| Cloud SQL (PostgreSQL) | 5 connections | 30s |
| GCS | Default | 60s |

### Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/chat` | 60 requests | 1 minute |
| `/api/runs` (POST) | 10 requests | 1 minute |
| All others | 300 requests | 1 minute |
