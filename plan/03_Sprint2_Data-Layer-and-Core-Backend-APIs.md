# Sprint 2: Data Layer & Core Backend APIs

## Overview

This sprint implements the data models, persistence layer, and core REST API endpoints for run management , pipeline configuration, and log access.

## References

- [03-backend-spec.md](../spec/03-backend-spec.md) - API specifications
- [06-data-model-spec.md](../spec/06-data-model-spec.md) - Data models
- [07-integration-spec.md](../spec/07-integration-spec.md) - Service integrations
- [12-recovery-spec.md](../spec/12-recovery-spec.md) - Recovery workflow

---

## Phase 2.1: Data Models & Persistence Layer

> **Spec References:**
> - [06-data-model-spec.md#cloud-sql-postgresql](../spec/06-data-model-spec.md) - Complete database schema
> - [06-data-model-spec.md#runs-table](../spec/06-data-model-spec.md) - Runs table definition
> - [06-data-model-spec.md#users-table](../spec/06-data-model-spec.md) - Users table definition
> - [06-data-model-spec.md#checkpoints-table](../spec/06-data-model-spec.md) - Checkpoints for LangGraph

### PostgreSQL Schema Design

- [ ] Create `backend/models/database.py` with SQLAlchemy models:
  - [ ] Define `Base` declarative base class
  - [ ] Configure metadata naming conventions

### Runs Table

> **Spec References:**
> - [06-data-model-spec.md#runs-table](../spec/06-data-model-spec.md) - Complete column definitions
> - [06-data-model-spec.md#run-status-values](../spec/06-data-model-spec.md) - Valid status values
> - [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md) - Recovery-specific fields

- [ ] Create `backend/models/runs.py`:
  - [ ] Define `Run` SQLAlchemy model with columns — *See [06-data-model-spec.md#runs-table](../spec/06-data-model-spec.md)*:
    - [ ] `run_id` (VARCHAR(50), PRIMARY KEY)
    - [ ] `pipeline` (VARCHAR(100), NOT NULL)
    - [ ] `pipeline_version` (VARCHAR(20), NOT NULL)
    - [ ] `status` (VARCHAR(20), NOT NULL) — *See [06-data-model-spec.md#run-status-values](../spec/06-data-model-spec.md)*
    - [ ] `user_email` (VARCHAR(255), NOT NULL)
    - [ ] `user_name` (VARCHAR(255))
    - [ ] `created_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] `updated_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] `submitted_at` (TIMESTAMPTZ, nullable)
    - [ ] `started_at` (TIMESTAMPTZ, nullable)
    - [ ] `completed_at` (TIMESTAMPTZ, nullable)
    - [ ] `failed_at` (TIMESTAMPTZ, nullable)
    - [ ] `cancelled_at` (TIMESTAMPTZ, nullable)
    - [ ] `gcs_path` (TEXT, NOT NULL) — *See [06-data-model-spec.md#google-cloud-storage](../spec/06-data-model-spec.md)*
    - [ ] `batch_job_name` (TEXT, nullable)
    - [ ] `params` (JSONB, NOT NULL) — *See [06-data-model-spec.md#params-jsonb](../spec/06-data-model-spec.md)*
    - [ ] `sample_count` (INTEGER, NOT NULL)
    - [ ] `source_ngs_runs` (TEXT[], nullable)
    - [ ] `source_project` (TEXT, nullable)
    - [ ] `parent_run_id` (VARCHAR(50), nullable) — *See [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md)*
    - [ ] `is_recovery` (BOOLEAN, DEFAULT FALSE) — *See [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md)*
    - [ ] `recovery_notes` (TEXT, nullable) — *See [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md)*
    - [ ] `reused_work_dir` (TEXT, nullable) — *See [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md)*
    - [ ] `exit_code` (INTEGER, nullable)
    - [ ] `error_message` (TEXT, nullable) — *See [06-data-model-spec.md#error-fields](../spec/06-data-model-spec.md)*
    - [ ] `error_task` (TEXT, nullable)
    - [ ] `metrics` (JSONB, nullable) — *See [06-data-model-spec.md#metrics-jsonb](../spec/06-data-model-spec.md)*
  - [ ] Define indexes — *See [06-data-model-spec.md#indexes](../spec/06-data-model-spec.md)*:
    - [ ] `idx_runs_user_email_created_at` (user_email, created_at DESC)
    - [ ] `idx_runs_status_created_at` (status, created_at DESC)
    - [ ] `idx_runs_created_at` (created_at DESC)

### Users Table

> **Spec References:**
> - [06-data-model-spec.md#users-table](../spec/06-data-model-spec.md) - Complete column definitions

- [ ] Create `backend/models/users.py`:
  - [ ] Define `User` SQLAlchemy model with columns — *See [06-data-model-spec.md#users-table](../spec/06-data-model-spec.md)*:
    - [ ] `email` (VARCHAR(255), PRIMARY KEY)
    - [ ] `display_name` (VARCHAR(255), NOT NULL)
    - [ ] `created_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] `last_login_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] `preferences` (JSONB, NOT NULL, DEFAULT JSON object) — *See [06-data-model-spec.md#preferences-jsonb](../spec/06-data-model-spec.md)*
    - [ ] `stats` (JSONB, NOT NULL, DEFAULT JSON object) — *See [06-data-model-spec.md#stats-jsonb](../spec/06-data-model-spec.md)*
  - [ ] Define indexes:
    - [ ] `idx_users_last_login_at` (last_login_at DESC)

### Checkpoints Table

> **Spec References:**
> - [06-data-model-spec.md#checkpoints-table](../spec/06-data-model-spec.md) - LangGraph checkpoint storage

- [ ] Create `backend/models/checkpoints.py`:
  - [ ] Define `Checkpoint` SQLAlchemy model for LangGraph — *See [06-data-model-spec.md#checkpoints-table](../spec/06-data-model-spec.md)*:
    - [ ] `thread_id` (VARCHAR(100), NOT NULL)
    - [ ] `checkpoint_id` (VARCHAR(100), NOT NULL)
    - [ ] `parent_checkpoint_id` (VARCHAR(100), nullable)
    - [ ] `checkpoint` (JSONB, NOT NULL)
    - [ ] `metadata` (JSONB, nullable)
    - [ ] `created_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] PRIMARY KEY (thread_id, checkpoint_id)

### Pydantic Request/Response Models

> **Spec References:**
> - [03-backend-spec.md#request-response-models](../spec/03-backend-spec.md) - Model definitions
> - [03-backend-spec.md#run-models](../spec/03-backend-spec.md) - Run request/response schemas

- [ ] Create `backend/models/schemas/runs.py` — *See [03-backend-spec.md#run-models](../spec/03-backend-spec.md)*:
  - [ ] Define `RunStatus` enum (pending, submitted, running, completed, failed, cancelled)
  - [ ] Define `RunCreateRequest` model:
    - [ ] `pipeline` (str, regex pattern validation)
    - [ ] `pipeline_version` (str, semver pattern)
    - [ ] `samplesheet_csv` (str, max length 10MB)
    - [ ] `config_content` (str, max length 100KB)
    - [ ] `params` (dict)
  - [ ] Define `RunResponse` model with all run fields
  - [ ] Define `RunListResponse` model with pagination
  - [ ] Define `RunRecoverRequest` model — *See [12-recovery-spec.md#api](../spec/12-recovery-spec.md)*:
    - [ ] `reuse_work_dir` (bool, default True)
    - [ ] `notes` (str, optional)
    - [ ] `override_params` (dict, optional)
    - [ ] `override_config` (str, optional)
- [ ] Create `backend/models/schemas/pipelines.py` — *See [03-backend-spec.md#pipeline-models](../spec/03-backend-spec.md)*:
  - [ ] Define `PipelineParam` model
  - [ ] Define `SamplesheetColumn` model
  - [ ] Define `PipelineSchema` model
  - [ ] Define `PipelineListResponse` model
- [ ] Create `backend/models/schemas/logs.py`:
  - [ ] Define `LogEntry` model
  - [ ] Define `TaskInfo` model
  - [ ] Define `TaskLogs` model

### Database Migrations with Alembic

- [ ] Initialize Alembic in backend directory:
  - [ ] Run `alembic init migrations`
  - [ ] Configure `alembic.ini` with database URL
  - [ ] Update `migrations/env.py` for async support
- [ ] Create initial migration:
  - [ ] `alembic revision --autogenerate -m "initial_schema"`
  - [ ] Review generated migration file
  - [ ] Include runs, users, and checkpoints tables
- [ ] Test migration:
  - [ ] Apply migration to dev database
  - [ ] Verify table creation

### RunStoreService

> **Spec References:**
> - [03-backend-spec.md#runstoreservice](../spec/03-backend-spec.md) - Service interface
> - [06-data-model-spec.md#status-transitions](../spec/06-data-model-spec.md) - Valid status transitions
> - [06-data-model-spec.md#data-integrity](../spec/06-data-model-spec.md) - Validation rules

- [ ] Create `backend/services/runs.py` — *See [03-backend-spec.md#runstoreservice](../spec/03-backend-spec.md)*:
  - [ ] Implement `RunStoreService` class
  - [ ] Implement `create_run()` method:
    - [ ] Generate unique run_id (e.g., "run-{uuid4[:8]}")
    - [ ] Set initial status to "pending"
    - [ ] Set created_at and updated_at timestamps
    - [ ] Construct gcs_path from settings and run_id — *See [06-data-model-spec.md#gcs-path-format](../spec/06-data-model-spec.md)*
    - [ ] Insert into database
    - [ ] Return run_id
  - [ ] Implement `get_run()` method:
    - [ ] Query by run_id
    - [ ] Return RunResponse or None
  - [ ] Implement `list_runs()` method:
    - [ ] Support filtering by user_email, status, pipeline
    - [ ] Support pagination (page, page_size)
    - [ ] Support ordering by created_at DESC
    - [ ] Return RunListResponse
  - [ ] Implement `update_run_status()` method — *See [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md)*:
    - [ ] Update status and corresponding timestamp
    - [ ] Update updated_at
    - [ ] Handle status-specific fields (error_message, exit_code, etc.)
    - [ ] Validate status transitions — *See [06-data-model-spec.md#status-transitions](../spec/06-data-model-spec.md)*
  - [ ] Implement `create_recovery_run()` method — *See [12-recovery-spec.md#backend-workflow](../spec/12-recovery-spec.md)*:
    - [ ] Create new run linked to parent_run_id
    - [ ] Set is_recovery to True
    - [ ] Copy relevant fields from parent run
    - [ ] Set reused_work_dir from parent
- [ ] Add validation for status transitions — *See [06-data-model-spec.md#status-transitions](../spec/06-data-model-spec.md)*:
  - [ ] pending → submitted, cancelled
  - [ ] submitted → running, cancelled
  - [ ] running → completed, failed, cancelled
- [ ] Add unit tests for RunStoreService

### UserService

> **Spec References:**
> - [07-integration-spec.md#user-data-integration](../spec/07-integration-spec.md) - User data storage

- [ ] Create `backend/services/users.py`:
  - [ ] Implement `UserService` class
  - [ ] Implement `get_or_create_user()` method:
    - [ ] Check if user exists by email
    - [ ] If exists, update last_login_at and return
    - [ ] If not exists, create new user record
  - [ ] Implement `get_user()` method
  - [ ] Implement `update_preferences()` method
  - [ ] Implement `update_stats()` method — *See [06-data-model-spec.md#stats-jsonb](../spec/06-data-model-spec.md)*:
    - [ ] Increment total_runs
    - [ ] Increment successful_runs (on completion)
    - [ ] Add to total_samples_processed
- [ ] Add unit tests for UserService

---

## Phase 2.2: Core REST API Endpoints

> **Spec References:**
> - [03-backend-spec.md#api-endpoints](../spec/03-backend-spec.md) - Complete API specification
> - [03-backend-spec.md#run-management-endpoints](../spec/03-backend-spec.md) - Run CRUD operations
> - [03-backend-spec.md#pipeline-endpoints](../spec/03-backend-spec.md) - Pipeline registry API

### Run Management Endpoints

> **Spec References:**
> - [03-backend-spec.md#run-management-endpoints](../spec/03-backend-spec.md) - Endpoints specification
> - [03-backend-spec.md#authorization](../spec/03-backend-spec.md) - Access control rules

- [ ] Create `backend/api/routes/runs.py` — *See [03-backend-spec.md#run-management-endpoints](../spec/03-backend-spec.md)*:
  - [ ] Implement `GET /api/runs` endpoint:
    - [ ] Accept query parameters: status, pipeline, page, page_size
    - [ ] Filter by current user or all (based on permissions) — *See [03-backend-spec.md#authorization](../spec/03-backend-spec.md)*
    - [ ] Return paginated RunListResponse
  - [ ] Implement `GET /api/runs/{id}` endpoint:
    - [ ] Fetch run by ID
    - [ ] Check user authorization (owner or admin) — *See [08-security-spec.md#resource-level-access](../spec/08-security-spec.md)*
    - [ ] Return RunResponse
    - [ ] Return 404 if not found
  - [ ] Implement `POST /api/runs` endpoint:
    - [ ] Validate RunCreateRequest
    - [ ] Validate pipeline exists in registry
    - [ ] Create run record with status "pending"
    - [ ] Return RunResponse with run_id
  - [ ] Implement `DELETE /api/runs/{id}` endpoint:
    - [ ] Verify run is cancellable (not already terminal)
    - [ ] Cancel GCP Batch job if running
    - [ ] Update status to "cancelled"
    - [ ] Set cancelled_at timestamp
  - [ ] Implement `POST /api/runs/{id}/recover` endpoint — *See [12-recovery-spec.md#api](../spec/12-recovery-spec.md)*:
    - [ ] Validate run is in terminal state (failed or cancelled) — *See [12-recovery-spec.md#recovery-preconditions](../spec/12-recovery-spec.md)*
    - [ ] Verify work directory exists in GCS
    - [ ] Accept RunRecoverRequest body
    - [ ] Create new recovery run record
    - [ ] Return new RunResponse
- [ ] Register runs router in main app

### Run Files Endpoint

> **Spec References:**
> - [03-backend-spec.md#run-files-endpoint](../spec/03-backend-spec.md) - Files API
> - [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md) - File organization

- [ ] Implement `GET /api/runs/{id}/files` endpoint:
  - [ ] List files under run's GCS path — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*
  - [ ] Group by directory (inputs, results, logs)
  - [ ] Return file metadata (name, size, updated_at)
  - [ ] Include signed download URLs — *See [07-integration-spec.md#signed-url-generation](../spec/07-integration-spec.md)*

### Run Status Events Endpoint (SSE)

> **Spec References:**
> - [03-backend-spec.md#run-events-endpoint](../spec/03-backend-spec.md) - SSE specification
> - [07-integration-spec.md#sse-integration](../spec/07-integration-spec.md) - SSE implementation

- [ ] Implement `GET /api/runs/{id}/events` endpoint — *See [03-backend-spec.md#run-events-endpoint](../spec/03-backend-spec.md)*:
  - [ ] Use Server-Sent Events (SSE) format
  - [ ] Poll database for status changes — *See [07-integration-spec.md#sse-integration](../spec/07-integration-spec.md)*
  - [ ] Emit "status" events on change
  - [ ] Emit "done" event when run reaches terminal state
  - [ ] Handle client disconnection gracefully
  - [ ] Implement timeout for long-running connections

### Pipeline Registry Endpoints

> **Spec References:**
> - [03-backend-spec.md#pipeline-endpoints](../spec/03-backend-spec.md) - Pipeline API
> - [03-backend-spec.md#pipelineregistry](../spec/03-backend-spec.md) - Registry service

- [ ] Create `backend/services/pipelines.py` — *See [03-backend-spec.md#pipelineregistry](../spec/03-backend-spec.md)*:
  - [ ] Implement `PipelineRegistry` class
  - [ ] Define nf-core/scrnaseq configuration — *See [01-project-overview.md#mvp-scope](../spec/01-project-overview.md)*:
    - [ ] Pipeline name and display name
    - [ ] Description
    - [ ] Repository URL
    - [ ] Available versions (2.7.1, 2.6.0, 2.5.1)
    - [ ] Default version
    - [ ] Samplesheet columns (sample, fastq_1, fastq_2, expected_cells)
    - [ ] Required params (genome, protocol)
    - [ ] Optional params (aligner, expected_cells)
  - [ ] Implement `list_pipelines()` method
  - [ ] Implement `get_pipeline()` method
  - [ ] Implement `get_samplesheet_schema()` method
  - [ ] Implement `validate_params()` method
  - [ ] Implement `render_config()` method (template rendering)

- [ ] Create `backend/api/routes/pipelines.py` — *See [03-backend-spec.md#pipeline-endpoints](../spec/03-backend-spec.md)*:
  - [ ] Implement `GET /api/pipelines` endpoint:
    - [ ] Return list of available pipelines
  - [ ] Implement `GET /api/pipelines/{name}` endpoint:
    - [ ] Return pipeline configuration
    - [ ] Return 404 if not found
  - [ ] Implement `GET /api/pipelines/{name}/schema` endpoint:
    - [ ] Return samplesheet schema and parameter definitions
- [ ] Register pipelines router in main app

### Benchling Data Endpoints

> **Spec References:**
> - [03-backend-spec.md#benchling-endpoints](../spec/03-backend-spec.md) - Benchling API
> - [06-data-model-spec.md#benchling-data-warehouse](../spec/06-data-model-spec.md) - Available tables

- [ ] Create `backend/api/routes/benchling.py`:
  - [ ] Implement `GET /api/benchling/runs` endpoint:
    - [ ] Accept query parameters for filtering
    - [ ] Query Benchling warehouse for NGS runs — *See [06-data-model-spec.md#key-tables](../spec/06-data-model-spec.md)*
    - [ ] Return formatted list
  - [ ] Implement `GET /api/benchling/runs/{name}/samples` endpoint:
    - [ ] Query samples for specific NGS run
    - [ ] Include FASTQ paths and metadata
  - [ ] Implement `GET /api/benchling/metadata` endpoint:
    - [ ] Return available projects, instruments, etc.
    - [ ] Cache results (5 minute TTL) — *See [07-integration-spec.md#caching-strategy](../spec/07-integration-spec.md)*
- [ ] Register benchling router in main app

### Authentication Middleware

> **Spec References:**
> - [03-backend-spec.md#authentication](../spec/03-backend-spec.md) - Auth middleware
> - [07-integration-spec.md#gcp-iap-integration](../spec/07-integration-spec.md) - IAP JWT handling
> - [08-security-spec.md#jwt-token-handling](../spec/08-security-spec.md) - Token validation

- [ ] Create `backend/utils/auth.py` — *See [07-integration-spec.md#jwt-verification](../spec/07-integration-spec.md)*:
  - [ ] Implement `verify_iap_jwt()` function:
    - [ ] Verify JWT signature using Google's public keys
    - [ ] Validate audience claim
    - [ ] Validate expiration
    - [ ] Confirm hosted domain — *See [08-security-spec.md#jwt-token-handling](../spec/08-security-spec.md)*
  - [ ] Implement `get_current_user()` dependency — *See [07-integration-spec.md#user-context](../spec/07-integration-spec.md)*:
    - [ ] Extract JWT from `X-Goog-IAP-JWT-Assertion` header
    - [ ] Verify JWT and extract claims
    - [ ] Return User object (email, name)
    - [ ] Support development bypass when debug=True
- [ ] Apply authentication to all API routes

### Error Handling

> **Spec References:**
> - [03-backend-spec.md#error-handling](../spec/03-backend-spec.md) - Error response format
> - [07-integration-spec.md#error-handling-matrix](../spec/07-integration-spec.md) - Integration errors

- [ ] Create `backend/utils/errors.py` — *See [03-backend-spec.md#error-handling](../spec/03-backend-spec.md)*:
  - [ ] Define custom exception classes:
    - [ ] `NotFoundError`
    - [ ] `ValidationError`
    - [ ] `AuthorizationError`
    - [ ] `BenchlingError`
    - [ ] `BatchError`
  - [ ] Define `ErrorResponse` model — *See [03-backend-spec.md#error-response-format](../spec/03-backend-spec.md)*
  - [ ] Implement exception handlers for FastAPI
- [ ] Register exception handlers in main app

---

## Phase 2.3: Log Service & File Management

> **Spec References:**
> - [03-backend-spec.md#logservice](../spec/03-backend-spec.md) - Log service interface
> - [03-backend-spec.md#log-endpoints](../spec/03-backend-spec.md) - Log API specification
> - [07-integration-spec.md#cloud-logging-integration](../spec/07-integration-spec.md) - Cloud Logging queries

### Log Service Implementation

- [ ] Create `backend/services/logs.py` — *See [03-backend-spec.md#logservice](../spec/03-backend-spec.md)*:
  - [ ] Implement `LogService` class

#### Workflow Log Access

> **Spec References:**
> - [03-backend-spec.md#workflow-log](../spec/03-backend-spec.md) - Workflow log streaming

- [ ] Implement `get_workflow_log()` method:
  - [ ] Fetch `nextflow.log` from GCS (`logs/nextflow.log`) — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*
  - [ ] Parse log lines into LogEntry objects
  - [ ] Support offset/limit for pagination
  - [ ] Handle missing log file gracefully

- [ ] Implement `stream_workflow_log()` method:
  - [ ] Async generator for log streaming
  - [ ] Poll GCS for new content periodically
  - [ ] Track file offset for incremental reads
  - [ ] Yield LogEntry objects

#### Task Log Access

> **Spec References:**
> - [03-backend-spec.md#task-logs](../spec/03-backend-spec.md) - Task log retrieval
> - [07-integration-spec.md#cloud-logging-integration](../spec/07-integration-spec.md) - Log query patterns

- [ ] Implement `list_tasks()` method — *See [03-backend-spec.md#task-list](../spec/03-backend-spec.md)*:
  - [ ] Fetch and parse `trace.txt` from GCS
  - [ ] Extract task metadata:
    - [ ] task_id, name, process
    - [ ] status, exit_code
    - [ ] duration, cpu_percent, memory_peak
    - [ ] start_time, end_time
    - [ ] work_dir
  - [ ] Return list of TaskInfo objects
  - [ ] Cache trace parsing results

- [ ] Implement `get_task_logs()` method:
  - [ ] Fetch task stdout/stderr from Cloud Logging — *See [07-integration-spec.md#query-patterns](../spec/07-integration-spec.md)*
  - [ ] Filter by run_id and task labels — *See [07-integration-spec.md#required-labels-on-batch-jobs](../spec/07-integration-spec.md)*
  - [ ] Return TaskLogs object with stdout and stderr

- [ ] Implement `stream_task_logs()` method:
  - [ ] Async generator for Cloud Logging streaming
  - [ ] Filter by task identifiers

#### Log Download

- [ ] Implement `create_log_archive()` method:
  - [ ] Download all log files for a run
  - [ ] Create zip archive in memory or temp file
  - [ ] Include nextflow.log, trace.txt, timeline.html, report.html
  - [ ] Return archive path or bytes

### Log API Endpoints

> **Spec References:**
> - [03-backend-spec.md#log-endpoints](../spec/03-backend-spec.md) - Complete log API

- [ ] Create `backend/api/routes/logs.py` — *See [03-backend-spec.md#log-endpoints](../spec/03-backend-spec.md)*:
  - [ ] Implement `GET /api/runs/{id}/logs` endpoint:
    - [ ] Return complete workflow log
    - [ ] Support query params: offset, limit
  - [ ] Implement `GET /api/runs/{id}/logs/stream` (SSE) endpoint:
    - [ ] Stream workflow log in real-time
    - [ ] Return LogEntry objects as SSE events
    - [ ] Handle end-of-log gracefully
  - [ ] Implement `GET /api/runs/{id}/tasks` endpoint:
    - [ ] Return list of tasks with metadata
    - [ ] Parse from trace.txt
  - [ ] Implement `GET /api/runs/{id}/tasks/{task_id}/logs` endpoint:
    - [ ] Return stdout and stderr for specific task
    - [ ] Fetch from Cloud Logging
  - [ ] Implement `GET /api/runs/{id}/logs/download` endpoint:
    - [ ] Generate log archive
    - [ ] Return as attachment with appropriate content-type
- [ ] Register logs router in main app

### GCS File Operations Enhancement

> **Spec References:**
> - [03-backend-spec.md#storageservice](../spec/03-backend-spec.md) - Storage operations
> - [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md) - File organization

- [ ] Enhance `backend/services/storage.py`:
  - [ ] Implement `upload_run_files()` method:
    - [ ] Accept run_id and dict of filename -> content
    - [ ] Upload samplesheet.csv, nextflow.config, params.yaml
    - [ ] Return list of GCS URIs
  - [ ] Implement `get_run_files()` method:
    - [ ] List all files for a run
    - [ ] Organize by directory (inputs, results, logs) — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*
    - [ ] Return FileInfo objects with metadata
  - [ ] Implement `get_file_content()` method:
    - [ ] Download and return file content
    - [ ] Support text and binary modes
  - [ ] Implement `check_work_dir_exists()` method — *See [12-recovery-spec.md#recovery-preconditions](../spec/12-recovery-spec.md)*:
    - [ ] Check if work directory exists for recovery
    - [ ] Return boolean

### GCS Lifecycle Policies

> **Spec References:**
> - [06-data-model-spec.md#file-lifecycle](../spec/06-data-model-spec.md) - Retention policies
> - [07-integration-spec.md#lifecycle-policies](../spec/07-integration-spec.md) - Policy configuration

- [ ] Create lifecycle policy configuration — *See [07-integration-spec.md#lifecycle-policies](../spec/07-integration-spec.md)*:
  - [ ] Delete objects under `runs/*/work/` after 30 days
  - [ ] Document in terraform or gcloud commands
- [ ] Implement in terraform:
  - [ ] Add lifecycle_rule to GCS bucket resource
  - [ ] Condition: age = 30, matches_prefix = ["runs/*/work/"]
  - [ ] Action: Delete

### Run Event Service

> **Spec References:**
> - [03-backend-spec.md#runeventservice](../spec/03-backend-spec.md) - Event service interface

- [ ] Create `backend/services/run_events.py` — *See [03-backend-spec.md#runeventservice](../spec/03-backend-spec.md)*:
  - [ ] Implement `RunEventService` class
  - [ ] Implement `stream_run_events()` method:
    - [ ] Poll database for run status changes
    - [ ] Compare with last known status
    - [ ] Yield event on change
    - [ ] Implement configurable poll interval
    - [ ] Handle terminal states (stop polling)
  - [ ] Define event types:
    - [ ] "status" - Status change event
    - [ ] "progress" - Optional progress updates
    - [ ] "done" - Terminal state reached

---

## Key Deliverables Checklist

- [ ] PostgreSQL schema for runs, users, checkpoints tables
- [ ] SQLAlchemy async models with Pydantic validation
- [ ] Alembic migrations applied to dev database
- [ ] RunStoreService with CRUD operations
- [ ] UserService with on-login upsert
- [ ] Complete REST API for run management:
  - [ ] List runs with filtering/pagination
  - [ ] Get run details
  - [ ] Create run
  - [ ] Cancel run
  - [ ] Recover run
  - [ ] List run files
- [ ] SSE endpoint for run status updates
- [ ] Pipeline registry with nf-core/scrnaseq configuration
- [ ] Benchling data endpoints
- [ ] Log service with:
  - [ ] Workflow log access and streaming
  - [ ] Task list from trace.txt
  - [ ] Task logs from Cloud Logging
  - [ ] Log archive download
- [ ] IAP authentication middleware
- [ ] Error handling and custom exceptions
- [ ] Unit tests for all services and endpoints
