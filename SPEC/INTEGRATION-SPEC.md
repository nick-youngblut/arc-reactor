# Arc Reactor - Integration Specification

## Overview

The platform integrates with several external systems:

1. **Benchling**: Sample and sequencing data (LIMS)
2. **GCP Batch**: Pipeline execution
3. **Google Cloud Storage**: File storage
4. **Firestore**: Application database
5. **Anthropic API**: AI model (Claude)
6. **GCP IAP**: Authentication

## Benchling Integration

### Connection Method

The platform connects to Benchling's data warehouse via a read-only PostgreSQL connection.

```
┌─────────────────┐         ┌─────────────────┐
│  Arc Nextflow   │         │  Benchling      │
│  Platform       │ ──SQL──▶│  Data Warehouse │
│                 │         │  (PostgreSQL)   │
└─────────────────┘         └─────────────────┘
```

### Configuration

| Parameter | Description | Source |
|-----------|-------------|--------|
| Host | Warehouse hostname | Environment variable |
| Port | PostgreSQL port (5432) | Default |
| Database | Database name | Environment variable |
| Username | Read-only user | Secret Manager |
| Password | User password | Secret Manager |
| SSL Mode | `require` | Default |

### Connection Pool

```python
# Async SQLAlchemy with connection pooling
engine = create_async_engine(
    warehouse_url,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections every 30 min
)
```

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
| `WORK_DIR` | GCS work directory |
| `FIRESTORE_PROJECT` | Project for status updates |

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
    project = "arc-ctc-project"
    location = "us-central1"
    batch {
        serviceAccountEmail = "nextflow-tasks@project.iam.gserviceaccount.com"
        spot = true
        maxSpotAttempts = 3
        bootDiskSize = 100.GB
    }
}
```

## Google Cloud Storage Integration

### Bucket Configuration

| Bucket | Purpose | Access |
|--------|---------|--------|
| `arc-nf-pipeline-runs` | Run inputs, outputs, logs | Platform + Nextflow |
| `arc-ngs-data` | Raw sequencing data | Read-only |

### Operations

**File Upload:**
```python
from google.cloud import storage

def upload_run_files(run_id: str, files: dict[str, str]) -> list[str]:
    """Upload input files for a run."""
    client = storage.Client()
    bucket = client.bucket("arc-nf-pipeline-runs")
    
    paths = []
    for filename, content in files.items():
        blob = bucket.blob(f"runs/{run_id}/inputs/{filename}")
        blob.upload_from_string(content)
        paths.append(f"gs://arc-nf-pipeline-runs/runs/{run_id}/inputs/{filename}")
    
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

## Firestore Integration

### Client Configuration

```python
from google.cloud import firestore

db = firestore.Client(project="arc-ctc-project")
```

### Real-time Listeners

**Run Status Subscription:**
```python
async def subscribe_to_run(run_id: str) -> AsyncIterator[dict]:
    """Subscribe to real-time run status updates."""
    doc_ref = db.collection("runs").document(run_id)
    
    async for snapshot in doc_ref.snapshots():
        if snapshot.exists:
            yield snapshot.to_dict()
```

### Batch Operations

```python
def update_run_metrics(run_id: str, metrics: dict) -> None:
    """Update run with completion metrics."""
    batch = db.batch()
    
    run_ref = db.collection("runs").document(run_id)
    batch.update(run_ref, {
        "metrics": metrics,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })
    
    user_ref = db.collection("users").document(user_email)
    batch.update(user_ref, {
        "stats.total_runs": firestore.Increment(1),
        "stats.successful_runs": firestore.Increment(1 if success else 0),
    })
    
    batch.commit()
```

## Anthropic API Integration

### Configuration

Model configuration values are defined in `SPEC/CONFIG-SPEC.md` and must be
referenced from there to avoid drift. See the backend settings guidance in
`SPEC/BACKEND-SPEC.md`.

### LangChain Integration

```python
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "anthropic:claude-sonnet-4-5-20250929",
    temperature=0.1,
    max_tokens=6000,
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

### Error Handling

| Error | Response |
|-------|----------|
| Rate limit (429) | Retry with exponential backoff |
| Context length exceeded | Summarize history and retry |
| API error (5xx) | Retry 3x, then fail gracefully |

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

### Readiness Check

```python
@router.get("/ready")
async def readiness_check():
    """Check all integration health."""
    checks = {
        "benchling": await check_benchling_connection(),
        "firestore": await check_firestore_connection(),
        "gcs": await check_gcs_connection(),
        "batch": await check_batch_api(),
        "anthropic": await check_anthropic_api(),
    }
    
    all_healthy = all(checks.values())
    
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={"healthy": all_healthy, "checks": checks},
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

async def check_firestore_connection() -> bool:
    """Check Firestore connectivity."""
    try:
        db.collection("health").document("check").get()
        return True
    except Exception:
        return False

async def check_gcs_connection() -> bool:
    """Check GCS connectivity."""
    try:
        client = storage.Client()
        bucket = client.bucket("arc-nf-pipeline-runs")
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
| Anthropic API | 60 requests/minute | Per API key |
| GCP Batch | 100 concurrent jobs | Per project |
| Firestore | 10,000 writes/second | Per database |

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
| Firestore | Write failed | "Unable to save" | Retry |
| Anthropic | Rate limit | Automatic retry | Backoff |
| Anthropic | Context exceeded | "Conversation too long" | Summarize |
