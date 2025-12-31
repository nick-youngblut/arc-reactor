# Arc Nextflow Platform - Data Model Specification

## Overview

The platform uses multiple data stores, each optimized for its specific purpose:

1. **Cloud SQL (PostgreSQL)**: Application state (runs, chat checkpoints)
2. **Firestore**: User accounts and preferences
3. **Google Cloud Storage**: Pipeline files (inputs, outputs, logs)
4. **Benchling Data Warehouse**: Sample and sequencing data (read-only)

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
    metrics JSONB
);

CREATE INDEX idx_runs_user_email_created_at ON runs(user_email, created_at DESC);
CREATE INDEX idx_runs_status_created_at ON runs(status, created_at DESC);
CREATE INDEX idx_runs_created_at ON runs(created_at DESC);
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
  "batch_job_name": "projects/arc-ctc-project/locations/us-west1/jobs/nf-run-abc123",
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

### Table: `checkpoints`

Stores LangGraph conversation checkpoints for reconnection and recovery.

```sql
CREATE TABLE checkpoints (
    thread_id VARCHAR(100) NOT NULL,
    checkpoint_id VARCHAR(100) NOT NULL,
    parent_checkpoint_id VARCHAR(100),
    checkpoint JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (thread_id, checkpoint_id)
);
```

## Firestore Collections (User Accounts)

### Collection: `users`

Stores user profiles and preferences.

```typescript
interface User {
  // Identity
  email: string;                     // Primary key (IAP email)
  display_name: string;              // From Google Workspace
  
  // Timestamps
  created_at: Timestamp;             // First login
  last_login_at: Timestamp;          // Most recent login
  
  // Preferences
  preferences: {
    default_pipeline?: string;       // Default pipeline selection
    default_genome?: string;         // Default genome
    default_protocol?: string;       // Default 10X protocol
    notifications_enabled: boolean;  // Email notifications (future)
  };
  
  // Usage stats
  stats: {
    total_runs: number;
    successful_runs: number;
    total_samples_processed: number;
  };
}
```

**Example Document:**
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

### Collection: `sessions`

Stores chat session state (optional, can use in-memory).

```typescript
interface Session {
  // Identity
  session_id: string;                // Unique identifier
  user_email: string;                // Owner
  
  // Timestamps
  created_at: Timestamp;
  updated_at: Timestamp;
  
  // State
  pipeline: string;                  // Selected pipeline
  pipeline_version: string;
  
  // Generated files (cached)
  generated_samplesheet?: string;    // CSV content
  generated_config?: string;         // Config content
  
  // Agent state
  thread_id: string;                 // LangChain thread ID
  
  // Expiry
  expires_at: Timestamp;             // Auto-delete after 24 hours
}
```

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
   └── PostgreSQL: Update status to "running"

4. Nextflow executes
   └── GCS: Write to work/ directory
   └── GCS: Write to results/ directory

5. Nextflow completes
   └── GCS: Write logs
   └── PostgreSQL: Update status to "completed" or "failed"
```

### Status Update Flow

```
┌─────────────────┐         ┌─────────────────┐
│  Batch Job      │         │  PostgreSQL     │
│  (Orchestrator) │ ──────▶ │  runs           │
└─────────────────┘         └────────┬────────┘
                                     │
                                     │ SSE or polling
                                     ▼
                            ┌─────────────────┐
                            │  Frontend       │
                            │  (UI update)    │
                            └─────────────────┘
```

### Status Update Mechanism

The orchestrator container must update the `runs` table directly in PostgreSQL
using a lightweight status update script. The script is invoked by Nextflow
workflow hooks and only touches allowed fields.

**Script location:** `orchestrator/update_status.py` (packaged into the orchestrator image)

**Required environment:**
- `DATABASE_URL` (Cloud SQL connection string; Batch service account has `roles/cloudsql.client`).
  For GCP Batch, this must use the Cloud SQL **Private IP**, not the Cloud Run Unix socket.

**CLI usage (examples):**
```
python3 /update_status.py run-abc123 running --started_at 2025-12-30T18:22:11Z
python3 /update_status.py run-abc123 completed \
  --completed_at 2025-12-30T20:01:00Z \
  --metrics '{"duration_seconds": 5929, "tasks_completed": 423}'
python3 /update_status.py run-abc123 failed \
  --failed_at 2025-12-30T20:01:00Z \
  --exit_code 1 \
  --error_message "Process failed: fastq_qc"
```

**Allowed fields:**
- `status`, `submitted_at`, `started_at`, `completed_at`, `failed_at`, `cancelled_at`
- `exit_code`, `error_message`, `error_task`
- `metrics` (JSON)
- `batch_job_name`

**Nextflow hooks:**
```groovy
workflow.onStart {
  "python3 /update_status.py ${params.run_id} running --started_at '${new Date().toInstant().toString()}'".execute()
}

workflow.onComplete {
  if (workflow.success) {
    "python3 /update_status.py ${params.run_id} completed --completed_at '${new Date().toInstant().toString()}'".execute()
  }
}

workflow.onError {
  "python3 /update_status.py ${params.run_id} failed --failed_at '${new Date().toInstant().toString()}' --error_message '${workflow.errorMessage}' --exit_code ${workflow.exitStatus}".execute()
}
```

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
| Run metadata | Indefinite | Never deleted |
| User profiles | Indefinite | Never deleted |
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
