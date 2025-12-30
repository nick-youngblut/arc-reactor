# Arc Reactor - Architecture Overview

## System Architecture

The Arc Reactor follows a modern cloud-native architecture with clear separation between the web application layer, AI/agent layer, and compute layer. The system is designed to be serverless where possible, leveraging GCP managed services for scalability and reliability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   USERS                                         │
│                        (Authenticated via GCP IAP)                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLOUD RUN SERVICE                                  │
│                           (Single Container Deployment)                         │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         FASTAPI BACKEND                                   │  │
│  │                                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │  REST API   │  │  WebSocket  │  │  Static     │  │  Health     │       │  │
│  │  │  Routes     │  │  Handler    │  │  File       │  │  Checks     │       │  │
│  │  │             │  │             │  │  Server     │  │             │       │  │
│  │  │ /api/runs   │  │ /ws/chat    │  │ /*          │  │ /health     │       │  │
│  │  │ /api/pipes  │  │             │  │             │  │ /ready      │       │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  │         │                │                                                │  │
│  │         ▼                ▼                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐      │  │
│  │  │                     SERVICE LAYER                               │      │  │
│  │  │                                                                 │      │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │      │  │
│  │  │  │  Benchling   │  │  Batch       │  │  Pipeline    │           │      │  │
│  │  │  │  Service     │  │  Service     │  │  Registry    │           │      │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘           │      │  │
│  │  └─────────────────────────────────────────────────────────────────┘      │  │
│  │         │                │                                                │  │
│  │         ▼                ▼                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐      │  │
│  │  │                     AGENT LAYER                                 │      │  │
│  │  │                                                                 │      │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐   │      │  │
│  │  │  │              DEEPAGENT ORCHESTRATOR                      │   │      │  │
│  │  │  │                                                          │   │      │  │
│  │  │  │   Tools:                    Subagents:                   │   │      │  │
│  │  │  │   • search_ngs_runs         • benchling_expert           │   │      │  │
│  │  │  │   • get_run_samples         • config_expert              │   │      │  │
│  │  │  │   • generate_samplesheet                                 │   │      │  │
│  │  │  │   • generate_config                                      │   │      │  │
│  │  │  │   • validate_inputs                                      │   │      │  │
│  │  │  │   • submit_run                                           │   │      │  │
│  │  │  └──────────────────────────────────────────────────────────┘   │      │  │
│  │  └─────────────────────────────────────────────────────────────────┘      │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                      NEXT.JS FRONTEND (Static)                            │  │
│  │                                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │  Pipeline   │  │  Chat       │  │  File       │  │  Run        │       │  │
│  │  │  Workspace  │  │  Panel      │  │  Editors    │  │  History    │       │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
          │              │                    │                    │
          │              │                    │                    │
          ▼              ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Benchling   │  │  Cloud SQL   │  │  Firestore  │  │     GCS      │  │  GCP Batch   │
│  Warehouse   │  │ (PostgreSQL) │  │              │  │              │  │              │
│              │  │  • runs      │  │  • users     │  │  • inputs    │  │  • orchestr. │
│  • samples   │  │  • checkpoints│  │  • prefs     │  │  • work      │  │  • tasks     │
│  • runs      │  │              │  │              │  │  • results   │  │              │
│  • metadata  │  │              │  │              │  │  • logs      │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
                                           │                    │
                                           │                    │
                                           ▼                    ▼
                                    ┌──────────────────────────────┐
                                    │     NEXTFLOW EXECUTION       │
                                    │                              │
                                    │  Orchestrator Job            │
                                    │  (runs `nextflow run`)       │
                                    │         │                    │
                                    │         ▼                    │
                                    │  ┌────┐ ┌────┐ ┌────┐        │
                                    │  │Task│ │Task│ │Task│ ...    │
                                    │  └────┘ └────┘ └────┘        │
                                    │  (pipeline process jobs)     │
                                    └──────────────────────────────┘
```

## Component Overview

### Web Application Layer

#### Cloud Run Service

The entire application is deployed as a single Cloud Run service, following Arc's established patterns for internal applications.

| Aspect | Details |
|--------|---------|
| **Container** | Single Docker image containing FastAPI + static Next.js |
| **Scaling** | Auto-scales 0-10 instances based on traffic |
| **Timeout** | 60 minutes (for long-polling/WebSocket connections) |
| **Memory** | 2GB per instance |
| **CPU** | 2 vCPUs per instance |

#### FastAPI Backend

Handles all API requests, WebSocket connections, and serves the static frontend.

| Responsibility | Implementation |
|----------------|----------------|
| **REST API** | Pydantic models, automatic OpenAPI docs |
| **WebSocket** | Chat streaming via AI SDK-compatible format |
| **Static files** | Serves Next.js build output |
| **Resilience** | Circuit breakers for external services, readiness supports degraded mode |
| **Auth context** | Extracts user identity from IAP headers |

#### Next.js Frontend

Static export served by FastAPI, providing the user interface.

| Aspect | Details |
|--------|---------|
| **Rendering** | Static export (no SSR) |
| **Routing** | App Router with client-side navigation |
| **State** | TanStack Query + Zustand |
| **Styling** | Tailwind CSS + HeroUI |

### AI/Agent Layer

#### DeepAgent Orchestrator

The core AI component that powers the conversational interface.

| Aspect | Details |
|--------|---------|
| **Framework** | LangChain v1 + DeepAgents |
| **Model** | Claude Sonnet 4.5 (claude-sonnet-4-5-20250929; see `SPEC/CONFIG-SPEC.md`) |
| **State** | PostgreSQL checkpointer (AsyncPostgresSaver) |
| **Streaming** | Full token + tool streaming |

#### Tool Suite

Custom tools that give the agent access to platform capabilities.

| Tool | Purpose | Data Source |
|------|---------|-------------|
| `search_ngs_runs` | Find NGS runs by date/project/instrument | Benchling |
| `get_run_samples` | Get sample details for a run | Benchling |
| `get_sample_metadata` | Get detailed sample metadata | Benchling |
| `list_pipelines` | List available pipelines | Pipeline Registry |
| `get_pipeline_schema` | Get pipeline input requirements | Pipeline Registry |
| `generate_samplesheet` | Create CSV from samples | Benchling + Templates |
| `generate_config` | Create Nextflow config | Templates |
| `validate_inputs` | Check files and params | GCS + Validation Rules |
| `submit_run` | Submit to GCP Batch | Batch API |

### Data Layer

#### Cloud SQL (PostgreSQL)

Primary application database for run records and chat checkpoints.

| Table | Purpose | Access Pattern |
|-------|---------|----------------|
| `runs` | Pipeline run records | Write-heavy, read with filters |
| `checkpoints` | LangGraph chat checkpoints | Write-heavy, append-only |

#### Firestore (User Accounts)

Stores user profiles and preferences (read-heavy, low write volume).

#### Google Cloud Storage

Object storage for pipeline files.

| Bucket Path | Content | Lifecycle |
|-------------|---------|-----------|
| `gs://{settings.nextflow_bucket}/runs/{id}/inputs/` | Samplesheet, config, params | Permanent |
| `gs://{settings.nextflow_bucket}/runs/{id}/work/` | Nextflow work directory | Delete after 30 days |
| `gs://{settings.nextflow_bucket}/runs/{id}/results/` | Pipeline outputs | Permanent |
| `gs://{settings.nextflow_bucket}/runs/{id}/logs/` | Execution logs | Permanent |

All bucket references are derived from configuration (`settings.nextflow_bucket`) rather
than hardcoded paths.

#### Benchling Data Warehouse

Read-only access to Arc's Benchling instance via SQL queries.

| Table | Key Data |
|-------|----------|
| `ngs_run$raw` | NGS run metadata |
| `library_prep_sample$raw` | Sample information |
| `ngs_run_output_sample$raw` | FASTQ file locations |
| `ngs_library_metadata_v2$raw` | Sample metadata (organism, tissue, etc.) |

### Compute Layer

#### GCP Batch - Orchestrator Jobs

Long-running jobs that execute `nextflow run`.

| Aspect | Details |
|--------|---------|
| **Image** | Custom container with Nextflow + GCloud SDK |
| **Machine** | e2-standard-2 (2 vCPU, 8GB RAM) |
| **Provisioning** | Spot instances (3x retry on preemption) |
| **Duration** | Up to 7 days |
| **Logging** | Cloud Logging (automatic) |

#### GCP Batch - Task Jobs

Individual pipeline process jobs spawned by Nextflow.

| Aspect | Details |
|--------|---------|
| **Image** | Pipeline-specific containers (from nf-core) |
| **Machine** | Variable based on process requirements |
| **Provisioning** | Spot instances |
| **Duration** | Minutes to hours per task |

## Data Flow Patterns

### Pattern 1: Chat Message Flow

```
User Input → Frontend → WebSocket → FastAPI → DeepAgent → LLM
                                                    ↓
                                              Tool Execution
                                                    ↓
User Display ← Frontend ← WebSocket ← FastAPI ← Stream Response
```

### Pattern 2: File Generation Flow

```
Agent Tool Call → Benchling Query → Data Transformation → CSV/Config Generation
                                                              ↓
                                                    Frontend State Update
                                                              ↓
                                                      Editor Render
```

### Pattern 3: Run Submission Flow

```
Submit Button → Frontend → REST API → Validation → GCS Upload → Batch Submit
                                                                     ↓
                                                             PostgreSQL Write
                                                                     ↓
User Feedback ← Frontend ← REST Response ← Job Created Confirmation
```

### Pattern 4: Run Monitoring Flow

```
                              ┌─────────────────┐
                              │ Batch Job       │
                              │ (Orchestrator)  │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
SSE/HTTP Polling ◀──────────  │ PostgreSQL      │ ◀──────── Status Update Script
(Frontend)                    │ runs            │           (in Batch container)
       │                      └─────────────────┘
       ▼
UI Status Update
```

## Scalability Considerations

### Horizontal Scaling

| Component | Scaling Strategy |
|-----------|------------------|
| Cloud Run | Auto-scale based on request concurrency |
| Cloud SQL | Vertical scaling + read replicas if needed |
| GCS | Automatic (serverless) |
| GCP Batch | Queue-based, limited by quotas |

### Bottlenecks and Mitigations

| Bottleneck | Mitigation |
|------------|------------|
| Benchling query latency | Caching for metadata lookups |
| LLM response time | Streaming responses |
| GCP Batch quotas | Request quota increases, queue management |
| Cloud SQL connection limits | Pooling, short-lived transactions |

## Failure Modes

### Application Failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Cloud Run crash | Health check fails | Auto-restart |
| WebSocket disconnect | Client heartbeat | Auto-reconnect |
| API timeout | HTTP 504 | Client retry with backoff |

### Pipeline Failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Orchestrator preemption | Batch event | Auto-retry (3x) |
| Task failure | Nextflow error handling | Retry based on config |
| GCS access denied | IAM error | Alert, manual intervention |
| Benchling unavailable | Connection timeout | Graceful degradation |

### Data Failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| PostgreSQL write fail | Exception | Retry with backoff |
| GCS upload fail | Exception | Retry, then fail submission |
| State inconsistency | Periodic audit | Reconciliation job |

## Security Architecture

### Authentication Flow

```
User → Cloud Load Balancer → IAP Authentication → Cloud Run
                                    │
                                    ▼
                          Google Workspace SSO
                                    │
                                    ▼
                          X-Goog-IAP-JWT-Assertion header
                                    │
                                    ▼
                          FastAPI extracts user identity
```

### Service Account Permissions

| Service Account | Permissions | Used By |
|-----------------|-------------|---------|
| Cloud Run SA | Cloud SQL Client, GCS R/W, Batch submit | Web app |
| Batch Orchestrator SA | GCS R/W, Cloud SQL Client, Batch spawn | Orchestrator jobs |
| Nextflow Task SA | GCS R/W (work bucket only) | Pipeline tasks |

### Network Security

| Control | Implementation |
|---------|----------------|
| Ingress | IAP-protected, HTTPS only |
| Egress | VPC with Cloud NAT |
| Internal | Private Google Access |
| Benchling | Allowlisted IPs |

## Technology Decisions

### Why FastAPI + Next.js Static?

- **Single container deployment**: Simplifies Cloud Run configuration
- **Python ecosystem**: Access to bioinformatics libraries, LangChain
- **Static frontend**: Fast loads, CDN-friendly, no SSR complexity
- **Arc precedent**: Matches existing internal applications

### Why LangChain DeepAgents?

- **Tool orchestration**: Native support for complex tool pipelines
- **Streaming**: First-class streaming support
- **State management**: Built-in checkpointing
- **Arc precedent**: Established patterns in other Arc apps

### Why GCP Batch over Kubernetes?

- **Simplicity**: No cluster management
- **Cost**: Pay only for job runtime
- **Nextflow support**: Native GCP Batch executor
- **Scaling**: Automatic resource provisioning

### Why PostgreSQL over Firestore?

- **Checkpointing**: AsyncPostgresSaver and LangGraph are first-class
- **Transactions**: ACID guarantees for run state updates
- **Querying**: Rich filtering and ordering for run history
- **Consolidation**: Aligns with Benchling warehouse query patterns
