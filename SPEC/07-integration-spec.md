# Arc Reactor - Integration Specification

## Overview

The platform integrates with several external systems:

1. **Benchling**: Sample and sequencing data (LIMS)
2. **GCP Batch**: Pipeline execution
3. **Google Cloud Storage**: File storage
4. **Cloud SQL (PostgreSQL)**: Application database (runs, users, checkpoints)
5. **Google Gemini API**: AI model (Gemini 3 Flash)
6. **GCP IAP**: Authentication

## Benchling Integration

### Connection Method

The platform connects to Benchling via `benchling-py`'s `BenchlingSession`, which
wraps both the Benchling API client and the Benchling data warehouse (PostgreSQL).
All access is read-only in Arc Reactor.

```
┌─────────────────┐         ┌──────────────────────┐
│  Arc Nextflow   │         │  Benchling           │
│  Platform       │ ──API──▶│  API + Data Warehouse│
│                 │ ──SQL──▶│  (PostgreSQL)        │
└─────────────────┘         └──────────────────────┘
```

### Configuration

Benchling credentials are provided through `benchling-py`'s Dynaconf settings.
The `DYNACONF` environment variable selects the tenant.

| Environment | Required Variables |
|-------------|-------------------|
| `DYNACONF=prod` | `BENCHLING_PROD_API_KEY`, `BENCHLING_PROD_DATABASE_URI`, `BENCHLING_PROD_APP_CLIENT_ID`, `BENCHLING_PROD_APP_CLIENT_SECRET` |
| `DYNACONF=test` | `BENCHLING_TEST_API_KEY`, `BENCHLING_TEST_DATABASE_URI`, `BENCHLING_TEST_APP_CLIENT_ID`, `BENCHLING_TEST_APP_CLIENT_SECRET` |
| `DYNACONF=dev` | Same as `test` |

### Connection Pool

Benchling-py manages connection pooling internally via SQLAlchemy engine reuse.
Pool size and timeouts are configured in benchling-py's settings.

### Query Patterns

**Caching Strategy:**
| Query Type | Cache Duration | Cache Key |
|------------|----------------|-----------|
| Metadata lookups (instruments, projects) | 5 minutes | Static key |
| Recent runs list | No cache | - |
| Sample details | No cache | - |

**Error Handling:**
| Error | Response | Recovery |
|-------|----------|----------|
| Connection timeout | Retry 3x with backoff | Fall back to cached data if available |
| Query timeout | Return partial results | Suggest narrower filters |
| Access denied | Log and alert | Requires DBA intervention |

### Security

- Read-only database user
- IP allowlist for Cloud Run egress
- All queries parameterized (no SQL injection)
- Credentials stored in Secret Manager

## GCP Batch Integration

### Architecture

```
┌─────────────────┐    Create Job     ┌─────────────────┐
│  Arc Nextflow   │ ───────────────▶  │  GCP Batch      │
│  Platform       │                   │                 │
│                 │ ◀───────────────  │  Orchestrator   │
│                 │   Job Status      │  Job            │
└─────────────────┘                   └────────┬────────┘
                                               │
                                      ┌────────▼────────┐
                                      │  Nextflow       │
                                      │  Task Jobs      │
                                      └─────────────────┘
```

### API Operations

#### Job Submission

```python
from google.cloud import batch_v1

def submit_orchestrator_job(run_id: str, config: dict) -> str:
    """Submit Nextflow orchestrator job to GCP Batch."""
    client = batch_v1.BatchServiceClient()
    
    job = batch_v1.Job(
        task_groups=[task_group],
        allocation_policy=allocation_policy,
        logs_policy=logs_policy,
        labels={"run-id": run_id},
    )
    
    request = batch_v1.CreateJobRequest(
        parent=f"projects/{PROJECT}/locations/{REGION}",
        job_id=f"nf-{run_id}",
        job=job,
    )
    
    operation = client.create_job(request)
    return operation.name
```

#### Status Monitoring

```python
def get_job_status(job_name: str) -> dict:
    """Get current job status from Batch API."""
    client = batch_v1.BatchServiceClient()
    
    request = batch_v1.GetJobRequest(name=job_name)
    job = client.get_job(request)
    
    return {
        "state": job.status.state.name,
        "status_events": [
            {"type": e.type_, "description": e.description}
            for e in job.status.status_events
        ],
    }
```

#### Job Cancellation

```python
def cancel_job(job_name: str) -> bool:
    """Cancel a running job."""
    client = batch_v1.BatchServiceClient()
    
    request = batch_v1.DeleteJobRequest(name=job_name)
    operation = client.delete_job(request)
    
    return True
```

### Job Configuration

**Orchestrator Job Spec:**
```yaml
task_spec:
  compute_resource:
    cpu_milli: 2000        # 2 vCPU
    memory_mib: 4096       # 4 GB RAM
  max_run_duration: "604800s"  # 7 days
  max_retry_count: 2

allocation_policy:
  instances:
    - policy:
        machine_type: "e2-standard-2"
        provisioning_model: SPOT
  service_account: "nextflow-orchestrator@project.iam.gserviceaccount.com"

logs_policy:
  destination: CLOUD_LOGGING
```

**Environment Variables Passed to Orchestrator:**
| Variable | Description |
|----------|-------------|
| `RUN_ID` | Unique run identifier |
| `PIPELINE` | Pipeline name |
| `PIPELINE_VERSION` | Pipeline version |
| `CONFIG_GCS_PATH` | GCS path to config file |
| `PARAMS_GCS_PATH` | GCS path to params file |
| `WORK_DIR` | GCS work directory (original for recovery) |
| `DATABASE_URL` | Cloud SQL connection string for run status updates (Batch must use Private IP) |

### Run Status Updates (Orchestrator)

The orchestrator container is responsible for updating the `runs` table in
PostgreSQL via a lightweight script invoked by Nextflow hooks.

**Script:** `orchestrator/update_status.py`

**Typical flow:**
1. Backend creates run with status `pending`
2. Backend submits Batch job and sets status `submitted`
3. Orchestrator starts Nextflow and sets status `running`
4. Nextflow hooks set terminal status (`completed` or `failed`) and write metrics

**Hook usage (example):**
```groovy
workflow.onStart {
  "python3 /update_status.py ${params.run_id} running --started_at '${new Date().toInstant().toString()}'".execute()
}
```

### Nextflow → Batch Task Submission

Nextflow uses its native GCP Batch executor to submit individual pipeline tasks.

**Nextflow Configuration:**
```groovy
process {
    executor = "google-batch"
    errorStrategy = "retry"
    maxRetries = 3
    scratch = true
    resourceLimits = [cpus: 36, memory: 500.GB, time: 48.h]
}

google {
    project = "arc-genomics02"
    location = "us-west1"
    batch {
        serviceAccountEmail = "nextflow-tasks@project.iam.gserviceaccount.com"
        spot = true
        maxSpotAttempts = 3
        bootDiskSize = 100.GB
    }
}
```

### Run Recovery (`-resume`)

Recovery submissions reuse the original work directory and add `-resume`.
See `SPEC/12-recovery-spec.md` for eligibility and workflow details.

## Cloud Logging Integration

Nextflow task stdout/stderr and Batch job logs are available in Cloud Logging for
per-task debugging and infrastructure diagnostics.

### Query Patterns

| Query | Filter |
|-------|--------|
| All task logs for a run | `labels.run_id="RUN_ID"` |
| Specific task | `labels.task_name="STAR (1)"` |
| Errors only | `severity>=ERROR` |

### Required Labels on Batch Jobs

- `run_id`: Arc Reactor run identifier
- `task_name`: Nextflow task name
- `process`: Nextflow process name
- `stream`: `stdout` or `stderr`

## Google Cloud Storage Integration

### Bucket Configuration

| Bucket | Purpose | Access |
|--------|---------|--------|
| `arc-reactor-runs` | Run inputs, outputs, logs (from `settings.nextflow_bucket`) | Platform + Nextflow |
| `arc-ngs-data` | Raw sequencing data | Read-only |

### Operations

**File Upload:**
```python
from google.cloud import storage

def upload_run_files(run_id: str, files: dict[str, str]) -> list[str]:
    """Upload input files for a run."""
    client = storage.Client()
    bucket = client.bucket(settings.nextflow_bucket)
    
    paths = []
    for filename, content in files.items():
        blob = bucket.blob(f"runs/{run_id}/inputs/{filename}")
        blob.upload_from_string(content)
        paths.append(f"gs://{settings.nextflow_bucket}/runs/{run_id}/inputs/{filename}")
    
    return paths
```

**Signed URL Generation:**
```python
def get_signed_url(gcs_path: str, expiration_minutes: int = 60) -> str:
    """Generate a signed URL for file download."""
    bucket_name, blob_name = parse_gcs_path(gcs_path)
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
    )
```

**File Existence Check:**
```python
def check_files_exist(gcs_paths: list[str]) -> dict[str, bool]:
    """Check if multiple GCS files exist."""
    client = storage.Client()
    results = {}
    
    for path in gcs_paths:
        bucket_name, blob_name = parse_gcs_path(path)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        results[path] = blob.exists()
    
    return results
```

### Lifecycle Policies

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 30,
          "matchesPrefix": ["runs/*/work/"]
        }
      }
    ]
  }
}
```

## Cloud SQL (PostgreSQL) Integration

### Connection Configuration

**Cloud Run (Unix socket):**
```python
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = (
    "postgresql+asyncpg://{user}:{password}@/{db}"
    "?host=/cloudsql/{connection_name}"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
```

**GCP Batch (Private IP):**
```python
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = (
    "postgresql+asyncpg://{user}:{password}@{private_ip}:5432/{db}"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
```

### Run Status Queries

```python
async def get_run_status(run_id: str) -> dict:
    query = text(
        "SELECT status, updated_at, metrics FROM runs WHERE run_id = :run_id"
    )
    async with engine.begin() as conn:
        row = (await conn.execute(query, {"run_id": run_id})).one()
    return dict(row._mapping)
```

### SSE Integration

The backend exposes `GET /api/runs/{id}/events` and polls PostgreSQL for status
changes. The frontend uses EventSource for automatic reconnection.

## User Data Integration

User profiles and preferences are stored in the Cloud SQL PostgreSQL `users` table
(see `06-data-model-spec.md`). This consolidates all application state in a single
database, simplifying infrastructure and local development.

## Google Gemini API Integration

### Configuration

Model configuration values are defined in `SPEC/11-conf-spec.md` and must be
referenced from there to avoid drift. See the backend settings guidance in
`SPEC/03-backend-spec.md`.

### Authentication

The platform uses the Gemini Developer API for authentication:

1. **Gemini Developer API**:
   - Set `GOOGLE_API_KEY` environment variable
   - Simpler setup, no GCP project required

### LangChain Integration

```python
from langchain.chat_models import init_chat_model

# Standard initialization (Gemini Developer API)
model = init_chat_model(
    "google_genai:gemini-3-flash-preview",
    temperature=1.0,
    thinking_level="low",
)

```

### Streaming

All AI responses are streamed token-by-token using the Vercel AI SDK protocol.

```python
async def stream_response(messages: list) -> AsyncIterator[str]:
    """Stream AI response in AI SDK format."""
    async for event in agent.astream_events(
        {"messages": messages},
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            yield f'0:{json.dumps(content)}\n'
```

### Thinking Output

Gemini 3 Flash supports exposing reasoning steps via the `thinking_level` parameter.
However, **reasoning blocks are not displayed to users** and should be filtered during
stream processing. Only `text` content blocks are forwarded to the frontend.

```python
async for chunk in model.astream(messages):
    for block in chunk.content_blocks:
        if block["type"] == "reasoning":
            # Filter out reasoning blocks - not shown to users
            # Optionally log for debugging:
            # logger.debug(f"Reasoning: {block.get('reasoning', '')}")
            continue
        elif block["type"] == "text":
            # Stream text content to frontend
            yield format_ai_sdk_chunk(block["text"])
```

**Design Decision:** Reasoning blocks are internal model reasoning that improves response
quality but adds no value to the user experience. Showing raw Chain-of-Thought output
would clutter the interface. Tool calls, however, ARE shown to users in collapsed
accordion blocks (see `04-frontend-spec.md` ChatPanel section).

### Error Handling

| Error | Response |
|-------|----------|
| Rate limit (429) | Retry with exponential backoff |
| Context length exceeded | Summarize history and retry |
| API error (5xx) | Retry 3x, then fail gracefully |
| Invalid thinking_level | Fall back to "low" |

## GCP IAP Integration

### Authentication Flow

```
User Request → Load Balancer → IAP → Cloud Run
                                ↓
                        JWT Validation
                                ↓
                        X-Goog-IAP-JWT-Assertion header
```

### JWT Verification

```python
from google.auth import jwt
from google.auth.transport import requests

def verify_iap_jwt(token: str) -> dict:
    """Verify IAP JWT and extract claims."""
    request = requests.Request()
    
    claims = jwt.decode(
        token,
        request=request,
        audience=f"/projects/{PROJECT_NUMBER}/apps/{PROJECT_ID}",
    )
    
    return {
        "email": claims["email"],
        "name": claims.get("name", claims["email"]),
    }
```

### User Context

```python
async def get_current_user(request: Request) -> User:
    """Extract current user from IAP headers."""
    jwt_token = request.headers.get("X-Goog-IAP-JWT-Assertion")
    
    if not jwt_token:
        # Development mode - allow bypass
        if settings.debug:
            return User(email="dev@example.com", name="Developer")
        raise HTTPException(401, "Authentication required")
    
    claims = verify_iap_jwt(jwt_token)
    return User(**claims)
```

## Integration Health Checks

## Circuit Breakers

External services must be wrapped with circuit breakers to prevent cascading failures
and runaway retry storms when upstream dependencies are degraded.

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
async def query_benchling(query: str):
    # Benchling query logic
    pass

@circuit(failure_threshold=3, recovery_timeout=60)
async def call_gemini(messages: list):
    # Gemini API call
    pass
```

Circuit breaker thresholds are configurable via settings, and all external service
clients should expose whether the breaker is open for readiness reporting.

### Readiness Check

```python
@router.get("/ready")
async def readiness_check():
    """Check integration health with degraded mode support."""
    checks = {
        "benchling": await check_benchling_connection(),
        "postgres": await check_postgres_connection(),
        "gcs": await check_gcs_connection(),
        "batch": await check_batch_api(),
        "gemini": await check_gemini_api(),
    }
    
    critical = ["postgres", "gcs", "batch"]
    critical_healthy = all(checks[name] for name in critical)
    degraded = not all(checks.values())
    
    return JSONResponse(
        status_code=200 if critical_healthy else 503,
        content={
            "healthy": critical_healthy,
            "degraded": degraded,
            "checks": checks,
        },
    )
```

### Individual Checks

```python
async def check_benchling_connection() -> bool:
    """Check Benchling warehouse connectivity."""
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

async def check_postgres_connection() -> bool:
    """Check Cloud SQL PostgreSQL connectivity."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

async def check_gcs_connection() -> bool:
    """Check GCS connectivity."""
    try:
        client = storage.Client()
        bucket = client.bucket(settings.nextflow_bucket)
        bucket.exists()
        return True
    except Exception:
        return False
```

## Rate Limits and Quotas

### External Service Limits

| Service | Limit | Notes |
|---------|-------|-------|
| Benchling warehouse | 100 concurrent connections | Pool size = 5 |
| Gemini API | 60 requests/minute | Per API key |
| GCP Batch | 100 concurrent jobs | Per project |
| Cloud SQL | Connection limits | Pool size = 5 |

### Internal Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /api/runs | 10 | 1 minute |
| POST /api/chat | 60 | 1 minute |
| GET /api/* | 300 | 1 minute |

## Error Handling Matrix

| Integration | Error | User Message | Recovery |
|-------------|-------|--------------|----------|
| Benchling | Connection timeout | "Unable to access sample data" | Retry, use cache |
| Benchling | Query timeout | "Search taking too long" | Suggest filters |
| GCP Batch | Quota exceeded | "System busy, try later" | Queue request |
| GCP Batch | Job creation failed | "Unable to start pipeline" | Retry |
| GCS | Access denied | "Storage access error" | Alert admin |
| GCS | Object not found | "File not found" | Show file path |
| Cloud SQL | Write failed | "Unable to save" | Retry |
| Gemini | Rate limit | Automatic retry | Backoff |
| Gemini | Context exceeded | "Conversation too long" | Summarize |
