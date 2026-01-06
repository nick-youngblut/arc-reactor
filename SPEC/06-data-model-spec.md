# Arc Nextflow Platform - Data Model Specification

## Overview

The platform uses the following data stores:

1. **Cloud SQL (PostgreSQL)**: All application state (runs, users, chat checkpoints)
2. **Google Cloud Storage**: Pipeline files (inputs, outputs, logs)
3. **Benchling Data Warehouse**: Sample and sequencing data (read-only)

> **Design Decision:** A single PostgreSQL database is used for all application state rather than splitting data across multiple database technologies (e.g., Firestore for users). This simplifies infrastructure management, local development (one less service to mock), backup/recovery procedures, and reduces operational complexity.

## Cloud SQL (PostgreSQL)

### Table: `runs`

Stores pipeline run metadata and status.

```typescript
interface Run {
  // Identity
  run_id: string;                    // Unique identifier (e.g., "run-abc123")
  
  // Pipeline info
  pipeline: string;                  // e.g., "nf-core/scrnaseq"
  pipeline_version: string;          // e.g., "2.7.1"
  
  // Status
  status: RunStatus;                 // pending | submitted | running | completed | failed | cancelled
  
  // User info
  user_email: string;                // IAP authenticated email
  user_name: string;                 // Display name
  
  // Timestamps (TIMESTAMPTZ stored as ISO 8601)
  created_at: string;                // When run was created in UI
  updated_at: string;                // Last status update
  submitted_at?: string;             // When submitted to Batch
  started_at?: string;               // When Nextflow started
  completed_at?: string;             // When Nextflow finished (success)
  failed_at?: string;                // When Nextflow finished (failure)
  cancelled_at?: string;             // When user cancelled
  
  // GCP resources
  gcs_path: string;                  // gs://bucket/runs/{run_id}
  batch_job_name?: string;           // Full Batch job resource name
  
  // Configuration
  params: Record<string, any>;       // Pipeline parameters
  sample_count: number;              // Number of samples
  
  // Benchling context
  source_ngs_runs?: string[];        // NGS run IDs used as input
  source_project?: string;           // Project name

  // Recovery
  parent_run_id?: string;            // Original run ID if recovered
  is_recovery?: boolean;             // True if created via -resume recovery
  recovery_notes?: string;           // User-provided notes
  reused_work_dir?: string;          // GCS work dir reused for -resume
  
  // Error info (if failed)
  exit_code?: number;                // Nextflow exit code
  error_message?: string;            // Human-readable error
  error_task?: string;               // Failed task name
  
  // Metrics (populated after completion)
  metrics?: {
    duration_seconds: number;
    cpu_hours: number;
    memory_gb_hours: number;
    tasks_completed: number;
    tasks_failed: number;
  };

  // Weblog integration
  weblog_secret_hash?: string;      // SHA-256 of per-run secret token
  weblog_run_id?: string;           // Nextflow internal run UUID
  weblog_run_name?: string;         // Nextflow run name (e.g., "friendly_turing")
  last_weblog_event_at?: string;    // Timestamp of last weblog event
}

type RunStatus = 
  | "pending"      // Created but not submitted
  | "submitted"    // Submitted to Batch, waiting to start
  | "running"      // Nextflow is executing
  | "completed"    // Finished successfully
  | "failed"       // Finished with error
  | "cancelled";   // User cancelled
```

**Schema (PostgreSQL):**
```sql
CREATE TABLE runs (
    run_id VARCHAR(50) PRIMARY KEY,
    pipeline VARCHAR(100) NOT NULL,
    pipeline_version VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    user_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    gcs_path TEXT NOT NULL,
    batch_job_name TEXT,
    params JSONB NOT NULL,
    sample_count INTEGER NOT NULL,
    source_ngs_runs TEXT[],
    source_project TEXT,
    parent_run_id VARCHAR(50),
    is_recovery BOOLEAN DEFAULT FALSE,
    recovery_notes TEXT,
    reused_work_dir TEXT,
    exit_code INTEGER,
    error_message TEXT,
    error_task TEXT,
    metrics JSONB,
    weblog_secret_hash VARCHAR(64),
    weblog_run_id VARCHAR(36),
    weblog_run_name VARCHAR(255),
    last_weblog_event_at TIMESTAMPTZ
);

CREATE INDEX idx_runs_user_email_created_at ON runs(user_email, created_at DESC);
CREATE INDEX idx_runs_status_created_at ON runs(status, created_at DESC);
CREATE INDEX idx_runs_created_at ON runs(created_at DESC);
CREATE INDEX idx_runs_stale_detection ON runs(status, updated_at)
    WHERE status IN ('submitted', 'running');
```

**Example Document:**
```json
{
  "run_id": "run-abc123",
  "pipeline": "nf-core/scrnaseq",
  "pipeline_version": "2.7.1",
  "status": "running",
  "user_email": "jane.smith@arcinstitute.org",
  "user_name": "Jane Smith",
  "created_at": "2024-12-18T14:30:00Z",
  "updated_at": "2024-12-18T14:35:00Z",
  "submitted_at": "2024-12-18T14:31:00Z",
  "started_at": "2024-12-18T14:35:00Z",
  "gcs_path": "gs://arc-reactor-runs/runs/run-abc123",
  "batch_job_name": "projects/arc-genomics02/locations/us-west1/jobs/nf-run-abc123",
  "params": {
    "genome": "GRCh38",
    "protocol": "10XV3",
    "aligner": "simpleaf"
  },
  "sample_count": 24,
  "source_ngs_runs": ["NR-2024-0156"],
  "source_project": "CellAtlas",
  "parent_run_id": null,
  "is_recovery": false,
  "recovery_notes": null,
  "reused_work_dir": null
}
```

Recovery behavior and `-resume` semantics are defined in
`SPEC/12-recovery-spec.md`.

### Table: `tasks` (Nextflow Task Tracking)

Stores individual task status and metrics streamed from Nextflow weblog events.

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id VARCHAR(50) NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    task_id INTEGER NOT NULL,
    hash VARCHAR(32) NOT NULL,
    name VARCHAR(500) NOT NULL,
    process VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL,
    exit_code INTEGER,
    submit_time BIGINT,
    start_time BIGINT,
    complete_time BIGINT,
    duration_ms BIGINT,
    realtime_ms BIGINT,
    cpu_percent FLOAT,
    peak_rss BIGINT,
    peak_vmem BIGINT,
    read_bytes BIGINT,
    write_bytes BIGINT,
    workdir TEXT,
    container VARCHAR(500),
    attempt INTEGER DEFAULT 1,
    native_id VARCHAR(255),
    error_message TEXT,
    trace_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(run_id, task_id, attempt)
);

CREATE INDEX idx_tasks_run_id ON tasks(run_id);
CREATE INDEX idx_tasks_run_status ON tasks(run_id, status);
CREATE INDEX idx_tasks_process ON tasks(process);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
```

### Table: `weblog_event_log` (Deduplication)

Deduplicates Pub/Sub weblog events to ensure idempotent processing.

```sql
CREATE TABLE weblog_event_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    task_id INTEGER,
    attempt INTEGER,
    event_timestamp TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(run_id, event_type, task_id, attempt)
);

CREATE INDEX idx_weblog_event_log_cleanup ON weblog_event_log(processed_at);
```

### Table: `checkpoints`

Stores LangGraph conversation checkpoints for reconnection and recovery.

```sql
CREATE TABLE checkpoints (
    thread_id VARCHAR(100) NOT NULL,
    checkpoint_id VARCHAR(100) NOT NULL,
    parent_checkpoint_id VARCHAR(100),
    checkpoint JSONB NOT NULL,
    checkpoint_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (thread_id, checkpoint_id)
);
```

> **Note:** The column is named `checkpoint_metadata` instead of `metadata` to avoid conflicts with SQLAlchemy's reserved `metadata` attribute used for schema management.

### Table: `users`

Stores user profiles and preferences. This table is populated on first login and updated on subsequent logins.

```typescript
interface User {
  // Identity
  email: string;                     // Primary key (IAP email)
  display_name: string;              // From Google Workspace
  
  // Timestamps
  created_at: string;                // First login (TIMESTAMPTZ as ISO 8601)
  last_login_at: string;             // Most recent login
  
  // Preferences (JSONB)
  preferences: {
    default_pipeline?: string;       // Default pipeline selection
    default_genome?: string;         // Default genome
    default_protocol?: string;       // Default 10X protocol
    notifications_enabled: boolean;  // Email notifications (future)
  };
  
  // Usage stats (JSONB)
  stats: {
    total_runs: number;
    successful_runs: number;
    total_samples_processed: number;
  };
}
```

**Schema (PostgreSQL):**
```sql
CREATE TABLE users (
    email VARCHAR(255) PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ DEFAULT NOW(),
    preferences JSONB NOT NULL DEFAULT '{"notifications_enabled": false}'::jsonb,
    stats JSONB NOT NULL DEFAULT '{"total_runs": 0, "successful_runs": 0, "total_samples_processed": 0}'::jsonb
);

CREATE INDEX idx_users_last_login_at ON users(last_login_at DESC);
```

**Example Row:**
```json
{
  "email": "jane.smith@arcinstitute.org",
  "display_name": "Jane Smith",
  "created_at": "2024-10-01T09:00:00Z",
  "last_login_at": "2024-12-18T14:30:00Z",
  "preferences": {
    "default_pipeline": "nf-core/scrnaseq",
    "default_genome": "GRCh38",
    "default_protocol": "10XV3",
    "notifications_enabled": false
  },
  "stats": {
    "total_runs": 15,
    "successful_runs": 14,
    "total_samples_processed": 720
  }
}
```

> **Note:** Session state for the chat interface is managed by LangGraph checkpoints in the `checkpoints` table, not a separate sessions table. This eliminates potential inconsistency between session state and agent state.

## Google Cloud Storage Structure

### Bucket: `settings.nextflow_bucket` (default `arc-reactor-runs`)

```
gs://{settings.nextflow_bucket}/
│
├── runs/
│   └── {run_id}/
│       │
│       ├── inputs/
│       │   ├── samplesheet.csv      # Pipeline input samplesheet
│       │   ├── nextflow.config      # Nextflow configuration
│       │   └── params.yaml          # Pipeline parameters
│       │
│       ├── work/                    # Nextflow work directory
│       │   └── {hash}/              # Task work directories
│       │       ├── .command.sh
│       │       ├── .command.log
│       │       └── ...
│       │
│       ├── results/                 # Pipeline outputs
│       │   ├── multiqc/
│       │   ├── cellranger/ or simpleaf/
│       │   └── pipeline_info/
│       │
│       └── logs/
│           ├── nextflow.log         # Main Nextflow log
│           ├── trace.txt            # Execution trace
│           ├── timeline.html        # Timeline visualization
│           └── report.html          # Execution report
│
└── templates/                       # (Optional) Config templates
    └── scrnaseq/
        └── gcp_batch.config
```

### File Lifecycle

| Path | Lifecycle | Retention |
|------|-----------|-----------|
| `inputs/` | Permanent | Forever |
| `work/` | Temporary | 30 days after completion |
| `results/` | Permanent | Forever |
| `logs/` | Permanent | Forever |

### Object Metadata

All uploaded files include metadata:

```json
{
  "x-goog-meta-run-id": "run-abc123",
  "x-goog-meta-user-email": "jane.smith@arcinstitute.org",
  "x-goog-meta-created-at": "2024-12-18T14:30:00Z"
}
```

## Benchling Data Warehouse Schema

### Key Tables (Read-Only)

The platform queries these Benchling tables but never writes to them.

#### `ngs_run$raw`

NGS sequencing runs.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Benchling entity ID |
| `name$` | string | Run name (e.g., "NR-2024-0156") |
| `instrument` | string | FK to ngs_instrument |
| `sequencing_reagent_kit` | string | Kit used |
| `created_at$` | timestamp | Creation time |
| `modified_at$` | timestamp | Last modification |
| `archived$` | boolean | Soft delete flag |

#### `ngs_run_output_v2$raw`

NGS run output information.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Benchling entity ID |
| `ngs_run` | string | FK to ngs_run |
| `completion_date` | date | Sequencing completion date |
| `link_to_sequencing_data` | string | GCS path to raw data |

#### `library_prep_sample$raw`

Library preparation samples.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Benchling entity ID |
| `sample_id` | string | Sample name (e.g., "LPS-001") |
| `lib_prep_method` | string | Library prep method |
| `lib_prep_kit_used` | string | Kit used |
| `project` | string | FK to project_tag |

#### `ngs_run_output_sample$raw`

Per-sample sequencing output.

| Column | Type | Description |
|--------|------|-------------|
| `ngs_run` | string | FK to ngs_run |
| `ngs_library` | string | FK to library_prep_sample |
| `read` | string | Read number (R1/R2) |
| `link_to_fastq_file` | string | GCS path to FASTQ |
| `sequenced_number_of_molecules` | integer | Read count |
| `q30_percent` | float | Quality metric |

#### `ngs_library_metadata_v2$raw`

Sample metadata.

| Column | Type | Description |
|--------|------|-------------|
| `ngs_library` | string | FK to library_prep_sample |
| `organism` | string | Species |
| `tissue` | string | Tissue type |
| `cell_line` | string | Cell line name |
| `perturbation` | string | Treatment condition |
| `replicate` | string | Replicate number |

### Common Queries

#### Get samples for an NGS run

```sql
SELECT 
  lps.sample_id,
  nros.link_to_fastq_file,
  nros.read,
  md.organism,
  md.cell_line
FROM library_prep_sample$raw lps
INNER JOIN ngs_library_pooling_v2$raw nlp ON lps.id = nlp.source
INNER JOIN pooled_sample$raw ps ON nlp.destination = ps.id
INNER JOIN ngs_run_pooling_v2$raw nrp ON ps.id = nrp.ngs_library_pool
INNER JOIN ngs_run$raw nr ON nrp.ngs_run = nr.id
INNER JOIN ngs_run_output_sample$raw nros ON nr.id = nros.ngs_run AND lps.id = nros.ngs_library
LEFT JOIN ngs_library_metadata_v2$raw md ON lps.id = md.ngs_library
WHERE nr."name$" = 'NR-2024-0156'
  AND lps.archived$ = FALSE
```

## Data Flow

### Run Submission Flow

```
1. User creates run in UI
   └── PostgreSQL: Create run record (status: pending)

2. User submits run
   └── GCS: Upload samplesheet, config, params
   └── PostgreSQL: Update status to "submitted"
   └── Batch: Create orchestrator job

3. Orchestrator starts
   └── Weblog: Nextflow emits `started` event
   └── PostgreSQL: Backend sets status to "running"

4. Nextflow executes
   └── GCS: Write to work/ directory
   └── GCS: Write to results/ directory

5. Nextflow completes
   └── GCS: Write logs
   └── Weblog: Nextflow emits `completed` or `error`
   └── PostgreSQL: Backend updates status and metrics
```

### Status Update Flow (Weblog + Pub/Sub)

```
┌───────────────────────────────┐   HTTP POST   ┌───────────────────────┐
│ GCP Batch Orchestrator (NF)   │ ────────────▶ │ Weblog Receiver       │
│ -with-weblog enabled          │               │ (Cloud Run)           │
└───────────────────────────────┘               └───────────┬───────────┘
                                                            │ Publish
                                                            ▼
                                                   ┌────────────────────┐
                                                   │ Pub/Sub Topic       │
                                                   └───────────┬────────┘
                                                               │ Push (OIDC)
                                                               ▼
                                                   ┌────────────────────┐
                                                   │ Backend /api/internal│
                                                   │ Weblog Processor    │
                                                   └───────────┬────────┘
                                                               ▼
                                                      ┌─────────────────┐
                                                      │ PostgreSQL       │
                                                      │ runs + tasks     │
                                                      └────────┬────────┘
                                                               │
                                                               ▼
                                                      Frontend (SSE/poll)
```

### Status Update Mechanism

Nextflow emits weblog events to the **weblog receiver** using `-with-weblog`. The weblog receiver validates the per-run secret token and publishes events to Pub/Sub. The backend consumes those events via an OIDC-protected internal endpoint, updates the `runs` table, and records task-level details in the `tasks` table. Deduplication is enforced via the `weblog_event_log` table.

To address missing events, a Cloud Scheduler job calls `/api/internal/reconcile-runs` every 5 minutes to reconcile stale runs against the GCP Batch API.

## Data Integrity

### Consistency Rules

1. **Run ID uniqueness**: Enforced by PostgreSQL primary key
2. **Status transitions**: Only valid transitions allowed
   ```
   pending → submitted → running → completed|failed
   pending → cancelled
   submitted → cancelled
   running → cancelled
   ```
3. **Immutable fields**: `run_id`, `created_at`, `user_email` never change

### Validation Rules

| Field | Rule |
|-------|------|
| `pipeline` | Must exist in pipeline registry |
| `sample_count` | Must be > 0 |
| `gcs_path` | Must be valid GCS URI |
| `params` | Must pass pipeline schema validation |

## Data Retention

| Data Type | Retention | Notes |
|-----------|-----------|-------|
| Run metadata (PostgreSQL) | Indefinite | Never deleted |
| User profiles (PostgreSQL) | Indefinite | Never deleted |
| Chat checkpoints | 30 days | Prune old threads |
| Input files | Indefinite | Never deleted |
| Work directories | 30 days | Cleaned by lifecycle policy |
| Result files | Indefinite | Never deleted |
| Logs | Indefinite | Never deleted |

## Backup and Recovery

### Cloud SQL (PostgreSQL)

- Automated daily backups (GCP managed)
- Point-in-time recovery enabled
- Read replicas for failover (if needed)

### GCS

- Versioning enabled for `inputs/` and `results/`
- Soft delete with 7-day recovery window
- No versioning for `work/` (ephemeral)

## Access Patterns

### High-Frequency Queries

| Query | Frequency | Index |
|-------|-----------|-------|
| List user's recent runs | Every page load | `user_email, created_at DESC` |
| Get run by ID | Every status check | Primary key |
| List running runs (all users) | Admin dashboard | `status, created_at DESC` |

### Low-Frequency Queries

| Query | Frequency | Notes |
|-------|-----------|-------|
| Search by project | On-demand | May need composite index |
| Aggregate stats | Daily | Use batch export |
