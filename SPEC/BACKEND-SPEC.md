# Arc Reactor - Backend Specification

## Overview

The backend is a FastAPI application that serves three primary functions:

1. **API Server**: REST endpoints for run management, pipeline configuration, and data queries
2. **WebSocket Server**: Real-time chat interface for the AI agent
3. **Static File Server**: Serves the compiled Next.js frontend

The backend follows Arc Institute's established patterns for internal applications, using Dynaconf for configuration, Pydantic for validation, and async throughout.

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
│       ├── pipelines.py    # Pipeline registry endpoints
│       └── health.py       # Health check endpoints
│
├── models/
│   ├── __init__.py
│   ├── runs.py             # Run request/response models
│   ├── pipelines.py        # Pipeline configuration models
│   ├── chat.py             # Chat message models
│   └── benchling.py        # Benchling data models
│
├── services/
│   ├── __init__.py
│   ├── benchling.py        # Benchling data warehouse queries
│   ├── batch.py            # GCP Batch job management
│   ├── firestore.py        # Firestore operations
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

```yaml
# settings.yaml
default:
  app_name: "Arc Reactor"
  debug: false
  
  # GCP Configuration
  gcp_project: "arc-ctc-project"
  gcp_region: "us-west1"
  
  # Service Configuration
  nextflow_bucket: "arc-nf-pipeline-runs"
  nextflow_service_account: "nextflow-orchestrator@arc-ctc-project.iam.gserviceaccount.com"
  orchestrator_image: "gcr.io/arc-ctc-project/nextflow-orchestrator:latest"
  
  # Benchling Configuration
  benchling_warehouse_host: "benchling-warehouse.arcinstitute.org"
  benchling_warehouse_db: "benchling"
  
  # AI Configuration
  anthropic_model: "claude-sonnet-4-5-20250929"
  
  # Frontend
  frontend_out_dir: "/app/frontend/out"

development:
  debug: true
  nextflow_bucket: "arc-nf-pipeline-runs-dev"

production:
  debug: false
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DYNACONF` | Environment name (development/production) | Yes |
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `BENCHLING_WAREHOUSE_PASSWORD` | Benchling warehouse credentials | Yes |
| `GCP_PROJECT` | GCP project ID (override) | No |

## API Endpoints

### Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/ready` | GET | Readiness check (includes dependencies) |

### Run Management

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `GET /api/runs` | GET | List runs (with filters) | Required |
| `GET /api/runs/{id}` | GET | Get run details | Required |
| `POST /api/runs` | POST | Submit new run | Required |
| `DELETE /api/runs/{id}` | DELETE | Cancel run | Required |
| `GET /api/runs/{id}/logs` | GET | Get run logs | Required |
| `GET /api/runs/{id}/files` | GET | List run files | Required |

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

class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int
    page: int
    page_size: int
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

Handles all queries to the Benchling data warehouse.

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `get_lib_prep_samples()` | Get all library prep samples with metadata | DataFrame |
| `get_run_paths()` | Get NGS run paths and instruments | DataFrame |
| `get_run_metadata()` | Get detailed metadata for a run | dict |
| `get_recent_runs()` | Get recent NGS runs | DataFrame |
| `get_projects()` | Get distinct projects | list[dict] |
| `get_instruments()` | Get available instruments | list[str] |

**Query Patterns:**

- All queries filter for `archived$ = FALSE`
- Complex queries use CTEs for readability
- Results cached for 5 minutes (metadata lookups)

### BatchService

Manages GCP Batch job submission and monitoring.

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `submit_run()` | Submit a new pipeline run | RunResponse |
| `get_run_status()` | Get current run status | RunStatus |
| `cancel_run()` | Cancel a running job | bool |
| `list_runs()` | List runs with filters | list[RunResponse] |
| `get_run_logs()` | Get Cloud Logging entries | list[LogEntry] |

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

**Bucket Structure:**

```
gs://arc-nf-pipeline-runs/
└── runs/
    └── {run_id}/
        ├── inputs/
        │   ├── samplesheet.csv
        │   ├── nextflow.config
        │   └── params.yaml
        ├── work/                    # Nextflow work dir
        ├── results/                 # Pipeline outputs
        └── logs/
            └── nextflow.log
```

### FirestoreService

Manages Firestore document operations.

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `create_run()` | Create run document | str (run_id) |
| `update_run_status()` | Update run status | bool |
| `get_run()` | Get run document | RunDocument |
| `list_runs()` | Query runs with filters | list[RunDocument] |
| `subscribe_run()` | Real-time run updates | AsyncIterator |

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
| Run status | No cache | Real-time from Firestore |

### Connection Pooling

| Service | Pool Size | Timeout |
|---------|-----------|---------|
| Benchling DB | 5 connections | 30s |
| Firestore | Default (async) | 30s |
| GCS | Default | 60s |

### Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/chat` | 60 requests | 1 minute |
| `/api/runs` (POST) | 10 requests | 1 minute |
| All others | 300 requests | 1 minute |