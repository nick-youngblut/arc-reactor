# Sprint 2: Data Layer & Core Backend APIs

## Overview

This sprint implements the data models, persistence layer, and core REST API endpoints for run management , pipeline configuration, and log access.

## References

- [03-backend-spec.md](../SPEC/03-backend-spec.md) - API specifications
- [06-data-model-spec.md](../SPEC/06-data-model-spec.md) - Data models
- [07-integration-spec.md](../SPEC/07-integration-spec.md) - Service integrations
- [12-recovery-spec.md](../SPEC/12-recovery-spec.md) - Recovery workflow

---

## Phase 2.1: Data Models & Persistence Layer

### PostgreSQL Schema Design

- [ ] Create `backend/models/database.py` with SQLAlchemy models:
  - [ ] Define `Base` declarative base class
  - [ ] Configure metadata naming conventions

### Runs Table

- [ ] Create `backend/models/runs.py`:
  - [ ] Define `Run` SQLAlchemy model with columns:
    - [ ] `run_id` (VARCHAR(50), PRIMARY KEY)
    - [ ] `pipeline` (VARCHAR(100), NOT NULL)
    - [ ] `pipeline_version` (VARCHAR(20), NOT NULL)
    - [ ] `status` (VARCHAR(20), NOT NULL)
    - [ ] `user_email` (VARCHAR(255), NOT NULL)
    - [ ] `user_name` (VARCHAR(255))
    - [ ] `created_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] `updated_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] `submitted_at` (TIMESTAMPTZ, nullable)
    - [ ] `started_at` (TIMESTAMPTZ, nullable)
    - [ ] `completed_at` (TIMESTAMPTZ, nullable)
    - [ ] `failed_at` (TIMESTAMPTZ, nullable)
    - [ ] `cancelled_at` (TIMESTAMPTZ, nullable)
    - [ ] `gcs_path` (TEXT, NOT NULL)
    - [ ] `batch_job_name` (TEXT, nullable)
    - [ ] `params` (JSONB, NOT NULL)
    - [ ] `sample_count` (INTEGER, NOT NULL)
    - [ ] `source_ngs_runs` (TEXT[], nullable)
    - [ ] `source_project` (TEXT, nullable)
    - [ ] `parent_run_id` (VARCHAR(50), nullable)
    - [ ] `is_recovery` (BOOLEAN, DEFAULT FALSE)
    - [ ] `recovery_notes` (TEXT, nullable)
    - [ ] `reused_work_dir` (TEXT, nullable)
    - [ ] `exit_code` (INTEGER, nullable)
    - [ ] `error_message` (TEXT, nullable)
    - [ ] `error_task` (TEXT, nullable)
    - [ ] `metrics` (JSONB, nullable)
  - [ ] Define indexes:
    - [ ] `idx_runs_user_email_created_at` (user_email, created_at DESC)
    - [ ] `idx_runs_status_created_at` (status, created_at DESC)
    - [ ] `idx_runs_created_at` (created_at DESC)

### Users Table

- [ ] Create `backend/models/users.py`:
  - [ ] Define `User` SQLAlchemy model with columns:
    - [ ] `email` (VARCHAR(255), PRIMARY KEY)
    - [ ] `display_name` (VARCHAR(255), NOT NULL)
    - [ ] `created_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] `last_login_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] `preferences` (JSONB, NOT NULL, DEFAULT JSON object)
    - [ ] `stats` (JSONB, NOT NULL, DEFAULT JSON object)
  - [ ] Define indexes:
    - [ ] `idx_users_last_login_at` (last_login_at DESC)

### Checkpoints Table

- [ ] Create `backend/models/checkpoints.py`:
  - [ ] Define `Checkpoint` SQLAlchemy model for LangGraph:
    - [ ] `thread_id` (VARCHAR(100), NOT NULL)
    - [ ] `checkpoint_id` (VARCHAR(100), NOT NULL)
    - [ ] `parent_checkpoint_id` (VARCHAR(100), nullable)
    - [ ] `checkpoint` (JSONB, NOT NULL)
    - [ ] `metadata` (JSONB, nullable)
    - [ ] `created_at` (TIMESTAMPTZ, DEFAULT NOW())
    - [ ] PRIMARY KEY (thread_id, checkpoint_id)

### Pydantic Request/Response Models

- [ ] Create `backend/models/schemas/runs.py`:
  - [ ] Define `RunStatus` enum (pending, submitted, running, completed, failed, cancelled)
  - [ ] Define `RunCreateRequest` model:
    - [ ] `pipeline` (str, regex pattern validation)
    - [ ] `pipeline_version` (str, semver pattern)
    - [ ] `samplesheet_csv` (str, max length 10MB)
    - [ ] `config_content` (str, max length 100KB)
    - [ ] `params` (dict)
  - [ ] Define `RunResponse` model with all run fields
  - [ ] Define `RunListResponse` model with pagination
  - [ ] Define `RunRecoverRequest` model:
    - [ ] `reuse_work_dir` (bool, default True)
    - [ ] `notes` (str, optional)
    - [ ] `override_params` (dict, optional)
    - [ ] `override_config` (str, optional)
- [ ] Create `backend/models/schemas/pipelines.py`:
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

- [ ] Create `backend/services/runs.py`:
  - [ ] Implement `RunStoreService` class
  - [ ] Implement `create_run()` method:
    - [ ] Generate unique run_id (e.g., "run-{uuid4[:8]}")
    - [ ] Set initial status to "pending"
    - [ ] Set created_at and updated_at timestamps
    - [ ] Construct gcs_path from settings and run_id
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
  - [ ] Implement `update_run_status()` method:
    - [ ] Update status and corresponding timestamp
    - [ ] Update updated_at
    - [ ] Handle status-specific fields (error_message, exit_code, etc.)
    - [ ] Validate status transitions
  - [ ] Implement `create_recovery_run()` method:
    - [ ] Create new run linked to parent_run_id
    - [ ] Set is_recovery to True
    - [ ] Copy relevant fields from parent run
    - [ ] Set reused_work_dir from parent
- [ ] Add validation for status transitions:
  - [ ] pending → submitted, cancelled
  - [ ] submitted → running, cancelled
  - [ ] running → completed, failed, cancelled
- [ ] Add unit tests for RunStoreService

### UserService

- [ ] Create `backend/services/users.py`:
  - [ ] Implement `UserService` class
  - [ ] Implement `get_or_create_user()` method:
    - [ ] Check if user exists by email
    - [ ] If exists, update last_login_at and return
    - [ ] If not exists, create new user record
  - [ ] Implement `get_user()` method
  - [ ] Implement `update_preferences()` method
  - [ ] Implement `update_stats()` method:
    - [ ] Increment total_runs
    - [ ] Increment successful_runs (on completion)
    - [ ] Add to total_samples_processed
- [ ] Add unit tests for UserService

---

## Phase 2.2: Core REST API Endpoints

### Run Management Endpoints

- [ ] Create `backend/api/routes/runs.py`:
  - [ ] Implement `GET /api/runs` endpoint:
    - [ ] Accept query parameters: status, pipeline, page, page_size
    - [ ] Filter by current user or all (based on permissions)
    - [ ] Return paginated RunListResponse
  - [ ] Implement `GET /api/runs/{id}` endpoint:
    - [ ] Fetch run by ID
    - [ ] Check user authorization (owner or admin)
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
  - [ ] Implement `POST /api/runs/{id}/recover` endpoint:
    - [ ] Validate run is in terminal state (failed or cancelled)
    - [ ] Verify work directory exists in GCS
    - [ ] Accept RunRecoverRequest body
    - [ ] Create new recovery run record
    - [ ] Return new RunResponse
- [ ] Register runs router in main app

### Run Files Endpoint

- [ ] Implement `GET /api/runs/{id}/files` endpoint:
  - [ ] List files under run's GCS path
  - [ ] Group by directory (inputs, results, logs)
  - [ ] Return file metadata (name, size, updated_at)
  - [ ] Include signed download URLs

### Run Status Events Endpoint (SSE)

- [ ] Implement `GET /api/runs/{id}/events` endpoint:
  - [ ] Use Server-Sent Events (SSE) format
  - [ ] Poll database for status changes
  - [ ] Emit "status" events on change
  - [ ] Emit "done" event when run reaches terminal state
  - [ ] Handle client disconnection gracefully
  - [ ] Implement timeout for long-running connections

### Pipeline Registry Endpoints

- [ ] Create `backend/services/pipelines.py`:
  - [ ] Implement `PipelineRegistry` class
  - [ ] Define nf-core/scrnaseq configuration:
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

- [ ] Create `backend/api/routes/pipelines.py`:
  - [ ] Implement `GET /api/pipelines` endpoint:
    - [ ] Return list of available pipelines
  - [ ] Implement `GET /api/pipelines/{name}` endpoint:
    - [ ] Return pipeline configuration
    - [ ] Return 404 if not found
  - [ ] Implement `GET /api/pipelines/{name}/schema` endpoint:
    - [ ] Return samplesheet schema and parameter definitions
- [ ] Register pipelines router in main app

### Benchling Data Endpoints

- [ ] Create `backend/api/routes/benchling.py`:
  - [ ] Implement `GET /api/benchling/runs` endpoint:
    - [ ] Accept query parameters for filtering
    - [ ] Query Benchling warehouse for NGS runs
    - [ ] Return formatted list
  - [ ] Implement `GET /api/benchling/runs/{name}/samples` endpoint:
    - [ ] Query samples for specific NGS run
    - [ ] Include FASTQ paths and metadata
  - [ ] Implement `GET /api/benchling/metadata` endpoint:
    - [ ] Return available projects, instruments, etc.
    - [ ] Cache results (5 minute TTL)
- [ ] Register benchling router in main app

### Authentication Middleware

- [ ] Create `backend/utils/auth.py`:
  - [ ] Implement `verify_iap_jwt()` function:
    - [ ] Verify JWT signature using Google's public keys
    - [ ] Validate audience claim
    - [ ] Validate expiration
    - [ ] Confirm hosted domain
  - [ ] Implement `get_current_user()` dependency:
    - [ ] Extract JWT from `X-Goog-IAP-JWT-Assertion` header
    - [ ] Verify JWT and extract claims
    - [ ] Return User object (email, name)
    - [ ] Support development bypass when debug=True
- [ ] Apply authentication to all API routes

### Error Handling

- [ ] Create `backend/utils/errors.py`:
  - [ ] Define custom exception classes:
    - [ ] `NotFoundError`
    - [ ] `ValidationError`
    - [ ] `AuthorizationError`
    - [ ] `BenchlingError`
    - [ ] `BatchError`
  - [ ] Define `ErrorResponse` model
  - [ ] Implement exception handlers for FastAPI
- [ ] Register exception handlers in main app

---

## Phase 2.3: Log Service & File Management

### Log Service Implementation

- [ ] Create `backend/services/logs.py`:
  - [ ] Implement `LogService` class

#### Workflow Log Access

- [ ] Implement `get_workflow_log()` method:
  - [ ] Fetch `nextflow.log` from GCS (`logs/nextflow.log`)
  - [ ] Parse log lines into LogEntry objects
  - [ ] Support offset/limit for pagination
  - [ ] Handle missing log file gracefully

- [ ] Implement `stream_workflow_log()` method:
  - [ ] Async generator for log streaming
  - [ ] Poll GCS for new content periodically
  - [ ] Track file offset for incremental reads
  - [ ] Yield LogEntry objects

#### Task Log Access

- [ ] Implement `list_tasks()` method:
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
  - [ ] Fetch task stdout/stderr from Cloud Logging
  - [ ] Filter by run_id and task labels
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

- [ ] Create `backend/api/routes/logs.py`:
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

- [ ] Enhance `backend/services/storage.py`:
  - [ ] Implement `upload_run_files()` method:
    - [ ] Accept run_id and dict of filename -> content
    - [ ] Upload samplesheet.csv, nextflow.config, params.yaml
    - [ ] Return list of GCS URIs
  - [ ] Implement `get_run_files()` method:
    - [ ] List all files for a run
    - [ ] Organize by directory (inputs, results, logs)
    - [ ] Return FileInfo objects with metadata
  - [ ] Implement `get_file_content()` method:
    - [ ] Download and return file content
    - [ ] Support text and binary modes
  - [ ] Implement `check_work_dir_exists()` method:
    - [ ] Check if work directory exists for recovery
    - [ ] Return boolean

### GCS Lifecycle Policies

- [ ] Create lifecycle policy configuration:
  - [ ] Delete objects under `runs/*/work/` after 30 days
  - [ ] Document in terraform or gcloud commands
- [ ] Implement in terraform:
  - [ ] Add lifecycle_rule to GCS bucket resource
  - [ ] Condition: age = 30, matches_prefix = ["runs/*/work/"]
  - [ ] Action: Delete

### Run Event Service

- [ ] Create `backend/services/run_events.py`:
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
