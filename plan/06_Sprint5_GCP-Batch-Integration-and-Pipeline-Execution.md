# Sprint 5: GCP Batch Integration & Pipeline Execution

## Overview

This sprint implements the complete pipeline execution workflow including GCP Batch job submission, the Nextflow orchestrator container, status update mechanism, and recovery support with `-resume`.

## References

- [06-data-model-spec.md](../spec/06-data-model-spec.md) - Status update mechanism
- [07-integration-spec.md](../spec/07-integration-spec.md) - GCP Batch integration
- [09-deployment-spec.md](../spec/09-deployment-spec.md) - Orchestrator container
- [12-recovery-spec.md](../spec/12-recovery-spec.md) - Recovery orchestration

---

## Phase 5.1: GCP Batch Job Management

> **Spec References:**
> - [07-integration-spec.md#gcp-batch-integration](../spec/07-integration-spec.md) - Complete Batch integration
> - [07-integration-spec.md#job-submission](../spec/07-integration-spec.md) - Job submission details
> - [03-backend-spec.md#batchservice](../spec/03-backend-spec.md) - Service interface

### BatchService Implementation

- [x] Create `backend/services/batch.py` — *See [03-backend-spec.md#batchservice](../spec/03-backend-spec.md)*:
  - [x] Import `google.cloud.batch_v1`
  - [x] Implement `BatchService` class
  - [x] Initialize BatchServiceClient

### Job Submission

> **Spec References:**
> - [07-integration-spec.md#job-submission](../spec/07-integration-spec.md) - Job specification
> - [07-integration-spec.md#orchestrator-job-specification](../spec/07-integration-spec.md) - Orchestrator config

- [x] Implement `submit_orchestrator_job()` method — *See [07-integration-spec.md#job-submission](../spec/07-integration-spec.md)*:
  - [x] Parameters:
    - [x] `run_id`: Run identifier
    - [x] `pipeline`: Pipeline name
    - [x] `pipeline_version`: Pipeline version
    - [x] `config_gcs_path`: GCS path to config
    - [x] `params_gcs_path`: GCS path to params
    - [x] `work_dir`: GCS work directory
    - [x] `is_recovery`: Boolean for resume mode — *See [12-recovery-spec.md#orchestrator-behavior](../spec/12-recovery-spec.md)*
  - [x] Build TaskSpec — *See [07-integration-spec.md#orchestrator-job-specification](../spec/07-integration-spec.md)*:
    - [x] Container image: orchestrator image from settings
    - [x] Environment variables:
      - [x] `RUN_ID`
      - [x] `PIPELINE`
      - [x] `PIPELINE_VERSION`
      - [x] `CONFIG_GCS_PATH`
      - [x] `PARAMS_GCS_PATH`
      - [x] `WORK_DIR`
      - [x] `DATABASE_URL` (Cloud SQL private IP) — *See [07-integration-spec.md#batch-to-cloud-sql](../spec/07-integration-spec.md)*
      - [x] `IS_RECOVERY` (for -resume flag)
    - [x] Compute resources:
      - [x] CPU: 2000 milli (2 vCPU)
      - [x] Memory: 4096 MiB (4 GB)
    - [x] Max run duration: 604800s (7 days)
    - [x] Max retry count: 2
  - [x] Build TaskGroup with single task
  - [x] Build AllocationPolicy:
    - [x] Machine type: `e2-standard-2`
    - [x] Provisioning model: SPOT — *See [09-deployment-spec.md#cost-optimization](../spec/09-deployment-spec.md)*
    - [x] Service account: orchestrator service account — *See [08-security-spec.md#batch-orchestrator-service-account](../spec/08-security-spec.md)*
  - [x] Build LogsPolicy:
    - [x] Destination: CLOUD_LOGGING
  - [x] Build Job with labels — *See [07-integration-spec.md#required-labels-on-batch-jobs](../spec/07-integration-spec.md)*:
    - [x] `run-id`: run identifier
    - [x] `app`: "arc-reactor"
  - [x] Create job request:
    - [x] Parent: `projects/{project}/locations/{region}`
    - [x] Job ID: `nf-{run_id}`
  - [x] Submit job and return job name

### Job Status Monitoring

> **Spec References:**
> - [07-integration-spec.md#status-monitoring](../spec/07-integration-spec.md) - Status polling

- [x] Implement `get_job_status()` method — *See [07-integration-spec.md#status-monitoring](../spec/07-integration-spec.md)*:
  - [x] Parameters:
    - [x] `job_name`: Full job resource name
  - [x] Fetch job from Batch API
  - [x] Extract status information:
    - [x] State (QUEUED, SCHEDULED, RUNNING, SUCCEEDED, FAILED, etc.)
    - [x] Status events with type and description
  - [x] Map Batch states to run status — *See [06-data-model-spec.md#run-status-values](../spec/06-data-model-spec.md)*:
    - [x] QUEUED/SCHEDULED → submitted
    - [x] RUNNING → running
    - [x] SUCCEEDED → completed
    - [x] FAILED/CANCELLED → failed/cancelled
  - [x] Return status dict

- [x] Implement `poll_job_until_terminal()` method:
  - [x] Poll job status at interval
  - [x] Return when terminal state reached
  - [x] Timeout after configurable duration

### Job Cancellation

> **Spec References:**
> - [07-integration-spec.md#job-cancellation](../spec/07-integration-spec.md) - Cancellation process

- [x] Implement `cancel_job()` method — *See [07-integration-spec.md#job-cancellation](../spec/07-integration-spec.md)*:
  - [x] Parameters:
    - [x] `job_name`: Full job resource name
  - [x] Create DeleteJobRequest
  - [x] Execute deletion
  - [x] Handle already-deleted gracefully
  - [x] Return success boolean

### Job Label Strategy

> **Spec References:**
> - [07-integration-spec.md#required-labels-on-batch-jobs](../spec/07-integration-spec.md) - Label requirements

- [x] Define standard labels for all Batch jobs — *See [07-integration-spec.md#required-labels-on-batch-jobs](../spec/07-integration-spec.md)*:
  - [x] `run-id`: Arc Reactor run identifier
  - [x] `app`: "arc-reactor"
  - [x] `pipeline`: Pipeline name
  - [x] `user-email`: Submitting user (sanitized)
- [x] Document label format in code comments
- [x] Use labels for Cloud Logging queries — *See [07-integration-spec.md#query-patterns](../spec/07-integration-spec.md)*

### BatchService Error Handling

> **Spec References:**
> - [07-integration-spec.md#error-handling-matrix](../spec/07-integration-spec.md) - Error types and handling

- [x] Implement error handling for common failures — *See [07-integration-spec.md#error-handling-matrix](../spec/07-integration-spec.md)*:
  - [x] Quota exceeded: Raise appropriate exception
  - [x] Permission denied: Log and raise
  - [x] Job creation failed: Retry with backoff
  - [x] Network errors: Retry with backoff
- [x] Create custom exception classes:
  - [x] `BatchQuotaExceededError`
  - [x] `BatchJobCreationError`
  - [x] `BatchJobNotFoundError`

### BatchService Unit Tests

- [x] Create `backend/tests/test_batch_service.py`:
  - [x] Mock BatchServiceClient
  - [x] Test job submission with valid params
  - [x] Test job status retrieval
  - [x] Test job cancellation
  - [x] Test error handling scenarios

---

## Phase 5.2: Nextflow Orchestrator Container

> **Spec References:**
> - [09-deployment-spec.md#nextflow-orchestrator-dockerfile](../spec/09-deployment-spec.md) - Dockerfile specification
> - [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md) - Status update process
> - [12-recovery-spec.md#orchestrator-behavior](../spec/12-recovery-spec.md) - Resume support

### Orchestrator Directory Structure

- [x] Create `orchestrator/` directory:
  - [x] `Dockerfile.orchestrator`
  - [x] `entrypoint.sh`
  - [x] `update_status.py`
  - [x] `nextflow.config.template`

### Orchestrator Dockerfile

> **Spec References:**
> - [09-deployment-spec.md#nextflow-orchestrator-dockerfile](../spec/09-deployment-spec.md) - Complete Dockerfile

- [x] Create `orchestrator/Dockerfile.orchestrator` — *See [09-deployment-spec.md#nextflow-orchestrator-dockerfile](../spec/09-deployment-spec.md)*:
  - [x] Base image: `nextflow/nextflow:24.04.4`
  - [x] Install system dependencies:
    - [x] curl
    - [x] python3
    - [x] python3-pip
  - [x] Install Google Cloud SDK:
    - [x] Add to PATH
  - [x] Install Python dependencies:
    - [x] asyncpg (for PostgreSQL)
    - [x] psycopg2-binary (sync fallback)
  - [x] Copy scripts:
    - [x] `entrypoint.sh` to `/entrypoint.sh`
    - [x] `update_status.py` to `/update_status.py`
  - [x] Make scripts executable
  - [x] Set entrypoint to `/entrypoint.sh`

### Entrypoint Script

> **Spec References:**
> - [07-integration-spec.md#orchestrator-job-specification](../spec/07-integration-spec.md) - Environment variables
> - [12-recovery-spec.md#orchestrator-behavior](../spec/12-recovery-spec.md) - Resume flag handling

- [x] Create `orchestrator/entrypoint.sh`:
  - [x] Parse environment variables:
    - [x] `RUN_ID`
    - [x] `PIPELINE`
    - [x] `PIPELINE_VERSION`
    - [x] `CONFIG_GCS_PATH`
    - [x] `PARAMS_GCS_PATH`
    - [x] `WORK_DIR`
    - [x] `IS_RECOVERY` — *See [12-recovery-spec.md#orchestrator-behavior](../spec/12-recovery-spec.md)*
  - [x] Log startup information
  - [x] Create local work directory
  - [x] Download config and params from GCS:
    - [x] `gsutil cp $CONFIG_GCS_PATH /config/nextflow.config`
    - [x] `gsutil cp $PARAMS_GCS_PATH /config/params.yaml`
  - [x] Build Nextflow command:
    - [x] `nextflow run ${PIPELINE}`
    - [x] `-r ${PIPELINE_VERSION}`
    - [x] `-c /config/nextflow.config`
    - [x] `-params-file /config/params.yaml`
    - [x] `-work-dir ${WORK_DIR}`
    - [x] `-with-trace`
    - [x] `-with-timeline`
    - [x] `-with-report`
    - [x] Add `-resume` if `IS_RECOVERY=true` — *See [12-recovery-spec.md#nextflow-resume](../spec/12-recovery-spec.md)*
  - [x] Execute Nextflow
  - [x] Capture exit code
  - [x] Upload logs to GCS — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*:
    - [x] `.nextflow.log` → `logs/nextflow.log`
    - [x] `trace.txt` → `logs/trace.txt`
    - [x] `timeline.html` → `logs/timeline.html`
    - [x] `report.html` → `logs/report.html`
  - [x] Exit with Nextflow exit code

### Status Update Script

> **Spec References:**
> - [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md) - Update process
> - [07-integration-spec.md#orchestrator-status-updates](../spec/07-integration-spec.md) - Implementation details

- [x] Create `orchestrator/update_status.py` — *See [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md)*:
  - [x] Parse command line arguments:
    - [x] `run_id` (positional)
    - [x] `status` (positional)
    - [x] `--started_at` (optional)
    - [x] `--completed_at` (optional)
    - [x] `--failed_at` (optional)
    - [x] `--error_message` (optional)
    - [x] `--error_task` (optional)
    - [x] `--exit_code` (optional)
    - [x] `--metrics` (optional, JSON string)
  - [x] Read DATABASE_URL from environment — *See [07-integration-spec.md#batch-to-cloud-sql](../spec/07-integration-spec.md)*
  - [x] Connect to PostgreSQL (sync connection)
  - [x] Build UPDATE query:
    - [x] Update `status` column
    - [x] Update `updated_at` to NOW()
    - [x] Update timestamp columns based on status
    - [x] Update error fields if provided — *See [06-data-model-spec.md#error-fields](../spec/06-data-model-spec.md)*
    - [x] Update metrics if provided — *See [06-data-model-spec.md#metrics-jsonb](../spec/06-data-model-spec.md)*
  - [x] Execute query with parameterized values — *See [08-security-spec.md#sql-injection-prevention](../spec/08-security-spec.md)*
  - [x] Log success/failure
  - [x] Exit with appropriate code

### Nextflow Hooks Configuration

> **Spec References:**
> - [07-integration-spec.md#orchestrator-status-updates](../spec/07-integration-spec.md) - Hook implementation

- [x] Create `orchestrator/nextflow.config.template` — *See [07-integration-spec.md#orchestrator-status-updates](../spec/07-integration-spec.md)*:
  - [x] Include workflow hooks:
    ```groovy
    workflow.onStart {
      "python3 /update_status.py ${params.run_id} running --started_at '${new Date().toInstant().toString()}'".execute()
    }
    
    workflow.onComplete {
      def status = workflow.success ? "completed" : "failed"
      def timestamp = status == "completed" ? "--completed_at" : "--failed_at"
      def cmd = "python3 /update_status.py ${params.run_id} ${status} ${timestamp} '${new Date().toInstant().toString()}'"
      if (!workflow.success) {
        cmd += " --exit_code ${workflow.exitStatus}"
        if (workflow.errorMessage) {
          cmd += " --error_message '${workflow.errorMessage.replaceAll("'", "")}'"
        }
      }
      cmd.execute()
    }
    
    workflow.onError {
      "python3 /update_status.py ${params.run_id} failed --failed_at '${new Date().toInstant().toString()}' --error_message '${workflow.errorMessage?.replaceAll("'", "") ?: 'Unknown error'}'".execute()
    }
    ```

### Nextflow GCP Batch Executor Configuration

> **Spec References:**
> - [07-integration-spec.md#nextflow-gcp-batch-executor](../spec/07-integration-spec.md) - Executor configuration

- [x] Document Nextflow executor configuration — *See [07-integration-spec.md#nextflow-gcp-batch-executor](../spec/07-integration-spec.md)*:
  - [x] Process block:
    ```groovy
    process {
      executor = 'google-batch'
      errorStrategy = 'retry'
      maxRetries = 3
      scratch = true
      resourceLimits = [cpus: 36, memory: 500.GB, time: 48.h]
    }
    ```
  - [x] Google block:
    ```groovy
    google {
      project = '<PROJECT_ID>'
      location = 'us-west1'
      batch {
        serviceAccountEmail = 'nextflow-tasks@project.iam.gserviceaccount.com'
        spot = true
        maxSpotAttempts = 3
        bootDiskSize = 100.GB
      }
    }
    ```

### Build and Push Orchestrator Image

> **Spec References:**
> - [09-deployment-spec.md#container-build](../spec/09-deployment-spec.md) - Build process

- [x] Create build script `scripts/build-orchestrator.sh` — *See [09-deployment-spec.md#container-build](../spec/09-deployment-spec.md)*:
  - [x] Build Docker image:
    - [x] `docker build -f orchestrator/Dockerfile.orchestrator -t ${IMAGE_NAME}:${VERSION} .`
    - [x] Use `--platform linux/amd64`
  - [x] Tag with version and latest
  - [x] Push to Artifact Registry or GCR
- [x] Add orchestrator build to CI/CD pipeline — *See [09-deployment-spec.md#github-actions-workflow](../spec/09-deployment-spec.md)*

### Orchestrator Integration Tests

- [x] Create local orchestrator test:
  - [x] Mock PostgreSQL connection
  - [x] Test entrypoint with sample config
  - [x] Verify update_status.py works
  - [x] Test error handling paths

---

## Phase 5.3: End-to-End Pipeline Flow

> **Spec References:**
> - [02-architecture-overview.md#run-submission-flow](../spec/02-architecture-overview.md) - Complete data flow
> - [02-architecture-overview.md#run-monitoring-flow](../spec/02-architecture-overview.md) - Status updates
> - [12-recovery-spec.md](../spec/12-recovery-spec.md) - Recovery workflow

### Run Submission Integration

> **Spec References:**
> - [02-architecture-overview.md#run-submission-flow](../spec/02-architecture-overview.md) - Submission sequence

- [ ] Update `backend/services/runs.py`:
  - [ ] Add `submit_run()` method:
    - [ ] Input: RunCreateRequest
    - [ ] Create run record with status "pending"
    - [ ] Upload files to GCS — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*:
      - [ ] samplesheet.csv → inputs/samplesheet.csv
      - [ ] nextflow.config → inputs/nextflow.config
      - [ ] params.yaml → inputs/params.yaml
    - [ ] Call BatchService.submit_orchestrator_job()
    - [ ] Update run status to "submitted"
    - [ ] Store batch_job_name
    - [ ] Return run_id

- [ ] Update `backend/services/runs.py`:
  - [ ] Add `submit_recovery_run()` method — *See [12-recovery-spec.md#backend-workflow](../spec/12-recovery-spec.md)*:
    - [ ] Input: parent_run_id, optional overrides
    - [ ] Verify parent run in terminal state — *See [12-recovery-spec.md#recovery-preconditions](../spec/12-recovery-spec.md)*
    - [ ] Verify work directory exists — *See [12-recovery-spec.md#work-directory-reuse](../spec/12-recovery-spec.md)*
    - [ ] Create new run record with parent_run_id
    - [ ] Copy or override config/params
    - [ ] Submit with IS_RECOVERY=true
    - [ ] Return new run_id

### Status Update Flow

> **Spec References:**
> - [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md) - Status flow
> - [06-data-model-spec.md#status-transitions](../spec/06-data-model-spec.md) - Valid transitions

- [ ] Document complete status flow — *See [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md)*:
  1. Backend creates run: `pending`
  2. Backend submits Batch job: `submitted`
  3. Orchestrator workflow.onStart hook: `running`
  4. Orchestrator workflow.onComplete hook: `completed` or `failed`
  5. Orchestrator workflow.onError hook: `failed`

- [ ] Implement status transition validation — *See [06-data-model-spec.md#status-transitions](../spec/06-data-model-spec.md)*:
  - [ ] Define valid transitions
  - [ ] Reject invalid transitions
  - [ ] Log all status changes

### SSE Status Propagation

> **Spec References:**
> - [07-integration-spec.md#sse-integration](../spec/07-integration-spec.md) - SSE implementation

- [ ] Update run event service for complete flow — *See [07-integration-spec.md#sse-integration](../spec/07-integration-spec.md)*:
  - [ ] Poll database for status changes
  - [ ] Emit events with:
    - [ ] Current status
    - [ ] Relevant timestamp
    - [ ] Progress information (if available)
  - [ ] Handle terminal states properly

### GCS File Lifecycle

> **Spec References:**
> - [06-data-model-spec.md#file-lifecycle](../spec/06-data-model-spec.md) - Retention policies
> - [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md) - Directory structure

- [ ] Document complete file lifecycle — *See [06-data-model-spec.md#file-lifecycle](../spec/06-data-model-spec.md)*:
  1. Run created:
     - [ ] `inputs/samplesheet.csv` (permanent)
     - [ ] `inputs/nextflow.config` (permanent)
     - [ ] `inputs/params.yaml` (permanent)
  2. Run executing:
     - [ ] `work/` directory (30-day retention) — *See [06-data-model-spec.md#file-lifecycle](../spec/06-data-model-spec.md)*
  3. Run completed:
     - [ ] `results/` directory (permanent)
     - [ ] `logs/nextflow.log` (permanent)
     - [ ] `logs/trace.txt` (permanent)
     - [ ] `logs/timeline.html` (permanent)
     - [ ] `logs/report.html` (permanent)

- [ ] Verify lifecycle policy is applied — *See [07-integration-spec.md#lifecycle-policies](../spec/07-integration-spec.md)*:
  - [ ] Check work/ deletion after 30 days
  - [ ] Ensure results/ not affected

### nf-core/scrnaseq Pipeline Testing

> **Spec References:**
> - [01-project-overview.md#mvp-scope](../spec/01-project-overview.md) - MVP pipeline

- [ ] Create test fixtures for scrnaseq — *See [01-project-overview.md#mvp-scope](../spec/01-project-overview.md)*:
  - [ ] Sample samplesheet with test data paths
  - [ ] Sample config with minimal settings
  - [ ] Sample params.yaml

- [ ] Test complete submission flow:
  - [ ] Create run via API
  - [ ] Verify files uploaded to GCS
  - [ ] Verify Batch job created
  - [ ] Monitor status transitions
  - [ ] Verify logs accessible

- [ ] Test recovery flow — *See [12-recovery-spec.md](../spec/12-recovery-spec.md)*:
  - [ ] Create run that partially completes
  - [ ] Trigger recovery via API
  - [ ] Verify -resume flag used
  - [ ] Verify work directory reused

### Error Handling

> **Spec References:**
> - [07-integration-spec.md#error-handling-matrix](../spec/07-integration-spec.md) - Error categories

- [ ] Implement comprehensive error handling — *See [07-integration-spec.md#error-handling-matrix](../spec/07-integration-spec.md)*:
  - [ ] Batch job creation failure:
    - [ ] Update run status to "failed"
    - [ ] Store error message
  - [ ] Orchestrator startup failure:
    - [ ] Ensure status updated to "failed"
    - [ ] Capture error from Batch job
  - [ ] Nextflow execution failure:
    - [ ] Capture error message and task
    - [ ] Update run with details
  - [ ] Log upload failure:
    - [ ] Retry with backoff
    - [ ] Log warning but don't fail run

### Cleanup and Monitoring

> **Spec References:**
> - [08-security-spec.md#audit-logging](../spec/08-security-spec.md) - Logging requirements

- [ ] Implement stale run detection:
  - [ ] Find runs stuck in "submitted" or "running"
  - [ ] Check corresponding Batch job status
  - [ ] Reconcile status if job completed

- [ ] Add monitoring hooks — *See [08-security-spec.md#audit-logging](../spec/08-security-spec.md)*:
  - [ ] Log run submission events
  - [ ] Log status transitions
  - [ ] Log error events with details
  - [ ] Emit metrics for observability

---

## Key Deliverables Checklist

- [ ] BatchService with:
  - [ ] Job submission
  - [ ] Status monitoring
  - [ ] Job cancellation
- [ ] Orchestrator job specification:
  - [ ] Machine type and resources
  - [ ] Environment variables
  - [ ] Service account
  - [ ] Spot instance configuration
- [ ] Job labeling for log filtering
- [ ] Orchestrator Docker image:
  - [ ] Nextflow base image
  - [ ] Google Cloud SDK
  - [ ] Python with asyncpg
  - [ ] Custom scripts
- [ ] Entrypoint script:
  - [ ] Config download from GCS
  - [ ] Nextflow execution
  - [ ] -resume support
  - [ ] Log upload
- [ ] update_status.py script:
  - [ ] PostgreSQL connection
  - [ ] Status updates
  - [ ] Error recording
  - [ ] Metrics recording
- [ ] Nextflow hooks:
  - [ ] onStart → running
  - [ ] onComplete → completed/failed
  - [ ] onError → failed
- [ ] Nextflow GCP Batch executor config
- [ ] Run submission integration:
  - [ ] File upload to GCS
  - [ ] Batch job submission
  - [ ] Status tracking
- [ ] Recovery submission:
  - [ ] Work directory verification
  - [ ] Parent run linking
  - [ ] -resume flag
- [ ] Complete status update flow
- [ ] SSE propagation working
- [ ] GCS file lifecycle verified
- [ ] nf-core/scrnaseq tested end-to-end
- [ ] Error handling for all failure modes
- [ ] Stale run detection
