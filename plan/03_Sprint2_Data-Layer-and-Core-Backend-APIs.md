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

- [x] Create `backend/models/database.py` with SQLAlchemy models:
  - [x] Define `Base` declarative base class
  - [x] Configure metadata naming conventions

### Runs Table

> **Spec References:**
> - [06-data-model-spec.md#runs-table](../spec/06-data-model-spec.md) - Complete column definitions
> - [06-data-model-spec.md#run-status-values](../spec/06-data-model-spec.md) - Valid status values
> - [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md) - Recovery-specific fields

- [x] Create `backend/models/runs.py`:
  - [x] Define `Run` SQLAlchemy model with columns — *See [06-data-model-spec.md#runs-table](../spec/06-data-model-spec.md)*:
    - [x] `run_id` (VARCHAR(50), PRIMARY KEY)
    - [x] `pipeline` (VARCHAR(100), NOT NULL)
    - [x] `pipeline_version` (VARCHAR(20), NOT NULL)
    - [x] `status` (VARCHAR(20), NOT NULL) — *See [06-data-model-spec.md#run-status-values](../spec/06-data-model-spec.md)*
    - [x] `user_email` (VARCHAR(255), NOT NULL)
    - [x] `user_name` (VARCHAR(255))
    - [x] `created_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [x] `updated_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [x] `submitted_at` (TIMESTAMPTZ, nullable)
    - [x] `started_at` (TIMESTAMPTZ, nullable)
    - [x] `completed_at` (TIMESTAMPTZ, nullable)
    - [x] `failed_at` (TIMESTAMPTZ, nullable)
    - [x] `cancelled_at` (TIMESTAMPTZ, nullable)
    - [x] `gcs_path` (TEXT, NOT NULL) — *See [06-data-model-spec.md#google-cloud-storage](../spec/06-data-model-spec.md)*
    - [x] `batch_job_name` (TEXT, nullable)
    - [x] `params` (JSONB, NOT NULL) — *See [06-data-model-spec.md#params-jsonb](../spec/06-data-model-spec.md)*
    - [x] `sample_count` (INTEGER, NOT NULL)
    - [x] `source_ngs_runs` (TEXT[], nullable)
    - [x] `source_project` (TEXT, nullable)
    - [x] `parent_run_id` (VARCHAR(50), nullable) — *See [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md)*
    - [x] `is_recovery` (BOOLEAN, DEFAULT FALSE) — *See [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md)*
    - [x] `recovery_notes` (TEXT, nullable) — *See [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md)*
    - [x] `reused_work_dir` (TEXT, nullable) — *See [12-recovery-spec.md#run-record-fields](../spec/12-recovery-spec.md)*
    - [x] `exit_code` (INTEGER, nullable)
    - [x] `error_message` (TEXT, nullable) — *See [06-data-model-spec.md#error-fields](../spec/06-data-model-spec.md)*
    - [x] `error_task` (TEXT, nullable)
    - [x] `metrics` (JSONB, nullable) — *See [06-data-model-spec.md#metrics-jsonb](../spec/06-data-model-spec.md)*
  - [x] Define indexes — *See [06-data-model-spec.md#indexes](../spec/06-data-model-spec.md)*:
    - [x] `idx_runs_user_email_created_at` (user_email, created_at DESC)
    - [x] `idx_runs_status_created_at` (status, created_at DESC)
    - [x] `idx_runs_created_at` (created_at DESC)

### Users Table

> **Spec References:**
> - [06-data-model-spec.md#users-table](../spec/06-data-model-spec.md) - Complete column definitions

- [x] Create `backend/models/users.py`:
  - [x] Define `User` SQLAlchemy model with columns — *See [06-data-model-spec.md#users-table](../spec/06-data-model-spec.md)*:
    - [x] `email` (VARCHAR(255), PRIMARY KEY)
    - [x] `display_name` (VARCHAR(255), NOT NULL)
    - [x] `created_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [x] `last_login_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [x] `preferences` (JSONB, NOT NULL, DEFAULT JSON object) — *See [06-data-model-spec.md#preferences-jsonb](../spec/06-data-model-spec.md)*
    - [x] `stats` (JSONB, NOT NULL, DEFAULT JSON object) — *See [06-data-model-spec.md#stats-jsonb](../spec/06-data-model-spec.md)*
  - [x] Define indexes:
    - [x] `idx_users_last_login_at` (last_login_at DESC)

### Checkpoints Table

> **Spec References:**
> - [06-data-model-spec.md#checkpoints-table](../spec/06-data-model-spec.md) - LangGraph checkpoint storage

- [x] Create `backend/models/checkpoints.py`:
  - [x] Define `Checkpoint` SQLAlchemy model for LangGraph — *See [06-data-model-spec.md#checkpoints-table](../spec/06-data-model-spec.md)*:
    - [x] `thread_id` (VARCHAR(100), NOT NULL)
    - [x] `checkpoint_id` (VARCHAR(100), NOT NULL)
    - [x] `parent_checkpoint_id` (VARCHAR(100), nullable)
    - [x] `checkpoint` (JSONB, NOT NULL)
    - [x] `metadata` (JSONB, nullable)
    - [x] `created_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [x] PRIMARY KEY (thread_id, checkpoint_id)

### Pydantic Request/Response Models

> **Spec References:**
> - [03-backend-spec.md#request-response-models](../spec/03-backend-spec.md) - Model definitions
> - [03-backend-spec.md#run-models](../spec/03-backend-spec.md) - Run request/response schemas

- [x] Create `backend/models/schemas/runs.py` — *See [03-backend-spec.md#run-models](../spec/03-backend-spec.md)*:
  - [x] Define `RunStatus` enum (pending, submitted, running, completed, failed, cancelled)
  - [x] Define `RunCreateRequest` model:
    - [x] `pipeline` (str, regex pattern validation)
    - [x] `pipeline_version` (str, semver pattern)
    - [x] `samplesheet_csv` (str, max length 10MB)
    - [x] `config_content` (str, max length 100KB)
    - [x] `params` (dict)
  - [x] Define `RunResponse` model with all run fields
  - [x] Define `RunListResponse` model with pagination
  - [x] Define `RunRecoverRequest` model — *See [12-recovery-spec.md#api](../spec/12-recovery-spec.md)*:
    - [x] `reuse_work_dir` (bool, default True)
    - [x] `notes` (str, optional)
    - [x] `override_params` (dict, optional)
    - [x] `override_config` (str, optional)
- [x] Create `backend/models/schemas/pipelines.py` — *See [03-backend-spec.md#pipeline-models](../spec/03-backend-spec.md)*:
  - [x] Define `PipelineParam` model
  - [x] Define `SamplesheetColumn` model
  - [x] Define `PipelineSchema` model
  - [x] Define `PipelineListResponse` model
- [x] Create `backend/models/schemas/logs.py`:
  - [x] Define `LogEntry` model
  - [x] Define `TaskInfo` model
  - [x] Define `TaskLogs` model

### Database Migrations with Alembic

- [x] Initialize Alembic in backend directory:
  - [x] Run `alembic init migrations`
  - [x] Configure `alembic.ini` with database URL
  - [x] Update `migrations/env.py` for async support
- [x] Create initial migration:
  - [x] `alembic revision --autogenerate -m "initial_schema"`
  - [x] Review generated migration file
  - [x] Include runs, users, and checkpoints tables
- [ ] Test migration:
  - [ ] Apply migration to dev database
  - [ ] Verify table creation

### RunStoreService

> **Spec References:**
> - [03-backend-spec.md#runstoreservice](../spec/03-backend-spec.md) - Service interface
> - [06-data-model-spec.md#status-transitions](../spec/06-data-model-spec.md) - Valid status transitions
> - [06-data-model-spec.md#data-integrity](../spec/06-data-model-spec.md) - Validation rules

- [x] Create `backend/services/runs.py` — *See [03-backend-spec.md#runstoreservice](../spec/03-backend-spec.md)*:
  - [x] Implement `RunStoreService` class
  - [x] Implement `create_run()` method:
    - [x] Generate unique run_id (e.g., "run-{uuid4[:8]}")
    - [x] Set initial status to "pending"
    - [x] Set created_at and updated_at timestamps
    - [x] Construct gcs_path from settings and run_id — *See [06-data-model-spec.md#gcs-path-format](../spec/06-data-model-spec.md)*
    - [x] Insert into database
    - [x] Return run_id
  - [x] Implement `get_run()` method:
    - [x] Query by run_id
    - [x] Return RunResponse or None
  - [x] Implement `list_runs()` method:
    - [x] Support filtering by user_email, status, pipeline
    - [x] Support pagination (page, page_size)
    - [x] Support ordering by created_at DESC
    - [x] Return RunListResponse
  - [x] Implement `update_run_status()` method — *See [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md)*:
    - [x] Update status and corresponding timestamp
    - [x] Update updated_at
    - [x] Handle status-specific fields (error_message, exit_code, etc.)
    - [x] Validate status transitions — *See [06-data-model-spec.md#status-transitions](../spec/06-data-model-spec.md)*
  - [x] Implement `create_recovery_run()` method — *See [12-recovery-spec.md#backend-workflow](../spec/12-recovery-spec.md)*:
    - [x] Create new run linked to parent_run_id
    - [x] Set is_recovery to True
    - [x] Copy relevant fields from parent run
    - [x] Set reused_work_dir from parent
- [x] Add validation for status transitions — *See [06-data-model-spec.md#status-transitions](../spec/06-data-model-spec.md)*:
  - [x] pending → submitted, cancelled
  - [x] submitted → running, cancelled
  - [x] running → completed, failed, cancelled
- [x] Add unit tests for RunStoreService

### UserService

> **Spec References:**
> - [07-integration-spec.md#user-data-integration](../spec/07-integration-spec.md) - User data storage

- [x] Create `backend/services/users.py`:
  - [x] Implement `UserService` class
  - [x] Implement `get_or_create_user()` method:
    - [x] Check if user exists by email
    - [x] If exists, update last_login_at and return
    - [x] If not exists, create new user record
  - [x] Implement `get_user()` method
  - [x] Implement `update_preferences()` method
  - [x] Implement `update_stats()` method — *See [06-data-model-spec.md#stats-jsonb](../spec/06-data-model-spec.md)*:
    - [x] Increment total_runs
    - [x] Increment successful_runs (on completion)
    - [x] Add to total_samples_processed
- [x] Add unit tests for UserService

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

- [x] Create `backend/api/routes/runs.py` — *See [03-backend-spec.md#run-management-endpoints](../spec/03-backend-spec.md)*:
  - [x] Implement `GET /api/runs` endpoint:
    - [x] Accept query parameters: status, pipeline, page, page_size
    - [x] Filter by current user or all (based on permissions) — *See [03-backend-spec.md#authorization](../spec/03-backend-spec.md)*
    - [x] Return paginated RunListResponse
  - [x] Implement `GET /api/runs/{id}` endpoint:
    - [x] Fetch run by ID
    - [x] Check user authorization (owner or admin) — *See [08-security-spec.md#resource-level-access](../spec/08-security-spec.md)*
    - [x] Return RunResponse
    - [x] Return 404 if not found
  - [x] Implement `POST /api/runs` endpoint:
    - [x] Validate RunCreateRequest
    - [x] Validate pipeline exists in registry
    - [x] Create run record with status "pending"
    - [x] Return RunResponse with run_id
  - [x] Implement `DELETE /api/runs/{id}` endpoint:
    - [x] Verify run is cancellable (not already terminal)
    - [x] Cancel GCP Batch job if running
    - [x] Update status to "cancelled"
    - [x] Set cancelled_at timestamp
  - [x] Implement `POST /api/runs/{id}/recover` endpoint — *See [12-recovery-spec.md#api](../spec/12-recovery-spec.md)*:
    - [x] Validate run is in terminal state (failed or cancelled) — *See [12-recovery-spec.md#recovery-preconditions](../spec/12-recovery-spec.md)*
    - [x] Verify work directory exists in GCS
    - [x] Accept RunRecoverRequest body
    - [x] Create new recovery run record
    - [x] Return new RunResponse
- [x] Register runs router in main app

### Run Files Endpoint

> **Spec References:**
> - [03-backend-spec.md#run-files-endpoint](../spec/03-backend-spec.md) - Files API
> - [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md) - File organization

- [x] Implement `GET /api/runs/{id}/files` endpoint:
  - [x] List files under run's GCS path — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*
  - [x] Group by directory (inputs, results, logs)
  - [x] Return file metadata (name, size, updated_at)
  - [x] Include signed download URLs — *See [07-integration-spec.md#signed-url-generation](../spec/07-integration-spec.md)*

### Run Status Events Endpoint (SSE)

> **Spec References:**
> - [03-backend-spec.md#run-events-endpoint](../spec/03-backend-spec.md) - SSE specification
> - [07-integration-spec.md#sse-integration](../spec/07-integration-spec.md) - SSE implementation

- [x] Implement `GET /api/runs/{id}/events` endpoint — *See [03-backend-spec.md#run-events-endpoint](../spec/03-backend-spec.md)*:
  - [x] Use Server-Sent Events (SSE) format
  - [x] Poll database for status changes — *See [07-integration-spec.md#sse-integration](../spec/07-integration-spec.md)*
  - [x] Emit "status" events on change
  - [x] Emit "done" event when run reaches terminal state
  - [x] Handle client disconnection gracefully
  - [x] Implement timeout for long-running connections

### Pipeline Registry Endpoints

> **Spec References:**
> - [03-backend-spec.md#pipeline-endpoints](../spec/03-backend-spec.md) - Pipeline API
> - [03-backend-spec.md#pipelineregistry](../spec/03-backend-spec.md) - Registry service

- [x] Create `backend/services/pipelines.py` — *See [03-backend-spec.md#pipelineregistry](../spec/03-backend-spec.md)*:
  - [x] Implement `PipelineRegistry` class
  - [x] Define nf-core/scrnaseq configuration — *See [01-project-overview.md#mvp-scope](../spec/01-project-overview.md)*:
    - [x] Pipeline name and display name
    - [x] Description
    - [x] Repository URL
    - [x] Available versions (2.7.1, 2.6.0, 2.5.1)
    - [x] Default version
    - [x] Samplesheet columns (sample, fastq_1, fastq_2, expected_cells)
    - [x] Required params (genome, protocol)
    - [x] Optional params (aligner, expected_cells)
  - [x] Implement `list_pipelines()` method
  - [x] Implement `get_pipeline()` method
  - [x] Implement `get_samplesheet_schema()` method
  - [x] Implement `validate_params()` method
  - [x] Implement `render_config()` method (template rendering)

- [x] Create `backend/api/routes/pipelines.py` — *See [03-backend-spec.md#pipeline-endpoints](../spec/03-backend-spec.md)*:
  - [x] Implement `GET /api/pipelines` endpoint:
    - [x] Return list of available pipelines
  - [x] Implement `GET /api/pipelines/{name}` endpoint:
    - [x] Return pipeline configuration
    - [x] Return 404 if not found
  - [x] Implement `GET /api/pipelines/{name}/schema` endpoint:
    - [x] Return samplesheet schema and parameter definitions
- [x] Register pipelines router in main app

### Benchling Data Endpoints

> **Spec References:**
> - [03-backend-spec.md#benchling-endpoints](../spec/03-backend-spec.md) - Benchling API
> - [06-data-model-spec.md#benchling-data-warehouse](../spec/06-data-model-spec.md) - Available tables

- [x] Create `backend/api/routes/benchling.py`:
  - [x] Implement `GET /api/benchling/runs` endpoint:
    - [x] Accept query parameters for filtering
    - [x] Query Benchling warehouse for NGS runs — *See [06-data-model-spec.md#key-tables](../spec/06-data-model-spec.md)*
    - [x] Return formatted list
  - [x] Implement `GET /api/benchling/runs/{name}/samples` endpoint:
    - [x] Query samples for specific NGS run
    - [x] Include FASTQ paths and metadata
  - [x] Implement `GET /api/benchling/metadata` endpoint:
    - [x] Return available projects, instruments, etc.
    - [x] Cache results (5 minute TTL) — *See [07-integration-spec.md#caching-strategy](../spec/07-integration-spec.md)*
- [x] Register benchling router in main app

### Authentication Middleware

> **Spec References:**
> - [03-backend-spec.md#authentication](../spec/03-backend-spec.md) - Auth middleware
> - [07-integration-spec.md#gcp-iap-integration](../spec/07-integration-spec.md) - IAP JWT handling
> - [08-security-spec.md#jwt-token-handling](../spec/08-security-spec.md) - Token validation

- [x] Create `backend/utils/auth.py` — *See [07-integration-spec.md#jwt-verification](../spec/07-integration-spec.md)*:
  - [x] Implement `verify_iap_jwt()` function:
    - [x] Verify JWT signature using Google's public keys
    - [x] Validate audience claim
    - [x] Validate expiration
    - [x] Confirm hosted domain — *See [08-security-spec.md#jwt-token-handling](../spec/08-security-spec.md)*
  - [x] Implement `get_current_user()` dependency — *See [07-integration-spec.md#user-context](../spec/07-integration-spec.md)*:
    - [x] Extract JWT from `X-Goog-IAP-JWT-Assertion` header
    - [x] Verify JWT and extract claims
    - [x] Return User object (email, name)
    - [x] Support development bypass when debug=True
- [x] Apply authentication to all API routes

### Error Handling

> **Spec References:**
> - [03-backend-spec.md#error-handling](../spec/03-backend-spec.md) - Error response format
> - [07-integration-spec.md#error-handling-matrix](../spec/07-integration-spec.md) - Integration errors

- [x] Create `backend/utils/errors.py` — *See [03-backend-spec.md#error-handling](../spec/03-backend-spec.md)*:
  - [x] Define custom exception classes:
    - [x] `NotFoundError`
    - [x] `ValidationError`
    - [x] `AuthorizationError`
    - [x] `BenchlingError`
    - [x] `BatchError`
  - [x] Define `ErrorResponse` model — *See [03-backend-spec.md#error-response-format](../spec/03-backend-spec.md)*
  - [x] Implement exception handlers for FastAPI
- [x] Register exception handlers in main app

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
