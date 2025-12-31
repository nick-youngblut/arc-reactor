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

- [ ] Create `backend/services/batch.py` — *See [03-backend-spec.md#batchservice](../spec/03-backend-spec.md)*:
  - [ ] Import `google.cloud.batch_v1`
  - [ ] Implement `BatchService` class
  - [ ] Initialize BatchServiceClient

### Job Submission

> **Spec References:**
> - [07-integration-spec.md#job-submission](../spec/07-integration-spec.md) - Job specification
> - [07-integration-spec.md#orchestrator-job-specification](../spec/07-integration-spec.md) - Orchestrator config

- [ ] Implement `submit_orchestrator_job()` method — *See [07-integration-spec.md#job-submission](../spec/07-integration-spec.md)*:
  - [ ] Parameters:
    - [ ] `run_id`: Run identifier
    - [ ] `pipeline`: Pipeline name
    - [ ] `pipeline_version`: Pipeline version
    - [ ] `config_gcs_path`: GCS path to config
    - [ ] `params_gcs_path`: GCS path to params
    - [ ] `work_dir`: GCS work directory
    - [ ] `is_recovery`: Boolean for resume mode — *See [12-recovery-spec.md#orchestrator-behavior](../spec/12-recovery-spec.md)*
  - [ ] Build TaskSpec — *See [07-integration-spec.md#orchestrator-job-specification](../spec/07-integration-spec.md)*:
    - [ ] Container image: orchestrator image from settings
    - [ ] Environment variables:
      - [ ] `RUN_ID`
      - [ ] `PIPELINE`
      - [ ] `PIPELINE_VERSION`
      - [ ] `CONFIG_GCS_PATH`
      - [ ] `PARAMS_GCS_PATH`
      - [ ] `WORK_DIR`
      - [ ] `DATABASE_URL` (Cloud SQL private IP) — *See [07-integration-spec.md#batch-to-cloud-sql](../spec/07-integration-spec.md)*
      - [ ] `IS_RECOVERY` (for -resume flag)
    - [ ] Compute resources:
      - [ ] CPU: 2000 milli (2 vCPU)
      - [ ] Memory: 4096 MiB (4 GB)
    - [ ] Max run duration: 604800s (7 days)
    - [ ] Max retry count: 2
  - [ ] Build TaskGroup with single task
  - [ ] Build AllocationPolicy:
    - [ ] Machine type: `e2-standard-2`
    - [ ] Provisioning model: SPOT — *See [09-deployment-spec.md#cost-optimization](../spec/09-deployment-spec.md)*
    - [ ] Service account: orchestrator service account — *See [08-security-spec.md#batch-orchestrator-service-account](../spec/08-security-spec.md)*
  - [ ] Build LogsPolicy:
    - [ ] Destination: CLOUD_LOGGING
  - [ ] Build Job with labels — *See [07-integration-spec.md#required-labels-on-batch-jobs](../spec/07-integration-spec.md)*:
    - [ ] `run-id`: run identifier
    - [ ] `app`: "arc-reactor"
  - [ ] Create job request:
    - [ ] Parent: `projects/{project}/locations/{region}`
    - [ ] Job ID: `nf-{run_id}`
  - [ ] Submit job and return job name

### Job Status Monitoring

> **Spec References:**
> - [07-integration-spec.md#status-monitoring](../spec/07-integration-spec.md) - Status polling

- [ ] Implement `get_job_status()` method — *See [07-integration-spec.md#status-monitoring](../spec/07-integration-spec.md)*:
  - [ ] Parameters:
    - [ ] `job_name`: Full job resource name
  - [ ] Fetch job from Batch API
  - [ ] Extract status information:
    - [ ] State (QUEUED, SCHEDULED, RUNNING, SUCCEEDED, FAILED, etc.)
    - [ ] Status events with type and description
  - [ ] Map Batch states to run status — *See [06-data-model-spec.md#run-status-values](../spec/06-data-model-spec.md)*:
    - [ ] QUEUED/SCHEDULED → submitted
    - [ ] RUNNING → running
    - [ ] SUCCEEDED → completed
    - [ ] FAILED/CANCELLED → failed/cancelled
  - [ ] Return status dict

- [ ] Implement `poll_job_until_terminal()` method:
  - [ ] Poll job status at interval
  - [ ] Return when terminal state reached
  - [ ] Timeout after configurable duration

### Job Cancellation

> **Spec References:**
> - [07-integration-spec.md#job-cancellation](../spec/07-integration-spec.md) - Cancellation process

- [ ] Implement `cancel_job()` method — *See [07-integration-spec.md#job-cancellation](../spec/07-integration-spec.md)*:
  - [ ] Parameters:
    - [ ] `job_name`: Full job resource name
  - [ ] Create DeleteJobRequest
  - [ ] Execute deletion
  - [ ] Handle already-deleted gracefully
  - [ ] Return success boolean

### Job Label Strategy

> **Spec References:**
> - [07-integration-spec.md#required-labels-on-batch-jobs](../spec/07-integration-spec.md) - Label requirements

- [ ] Define standard labels for all Batch jobs — *See [07-integration-spec.md#required-labels-on-batch-jobs](../spec/07-integration-spec.md)*:
  - [ ] `run-id`: Arc Reactor run identifier
  - [ ] `app`: "arc-reactor"
  - [ ] `pipeline`: Pipeline name
  - [ ] `user-email`: Submitting user (sanitized)
- [ ] Document label format in code comments
- [ ] Use labels for Cloud Logging queries — *See [07-integration-spec.md#query-patterns](../spec/07-integration-spec.md)*

### BatchService Error Handling

> **Spec References:**
> - [07-integration-spec.md#error-handling-matrix](../spec/07-integration-spec.md) - Error types and handling

- [ ] Implement error handling for common failures — *See [07-integration-spec.md#error-handling-matrix](../spec/07-integration-spec.md)*:
  - [ ] Quota exceeded: Raise appropriate exception
  - [ ] Permission denied: Log and raise
  - [ ] Job creation failed: Retry with backoff
  - [ ] Network errors: Retry with backoff
- [ ] Create custom exception classes:
  - [ ] `BatchQuotaExceededError`
  - [ ] `BatchJobCreationError`
  - [ ] `BatchJobNotFoundError`

### BatchService Unit Tests

- [ ] Create `backend/tests/test_batch_service.py`:
  - [ ] Mock BatchServiceClient
  - [ ] Test job submission with valid params
  - [ ] Test job status retrieval
  - [ ] Test job cancellation
  - [ ] Test error handling scenarios

---

## Phase 5.2: Nextflow Orchestrator Container

> **Spec References:**
> - [09-deployment-spec.md#nextflow-orchestrator-dockerfile](../spec/09-deployment-spec.md) - Dockerfile specification
> - [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md) - Status update process
> - [12-recovery-spec.md#orchestrator-behavior](../spec/12-recovery-spec.md) - Resume support

### Orchestrator Directory Structure

- [ ] Create `orchestrator/` directory:
  - [ ] `Dockerfile.orchestrator`
  - [ ] `entrypoint.sh`
  - [ ] `update_status.py`
  - [ ] `nextflow.config.template`

### Orchestrator Dockerfile

> **Spec References:**
> - [09-deployment-spec.md#nextflow-orchestrator-dockerfile](../spec/09-deployment-spec.md) - Complete Dockerfile

- [ ] Create `orchestrator/Dockerfile.orchestrator` — *See [09-deployment-spec.md#nextflow-orchestrator-dockerfile](../spec/09-deployment-spec.md)*:
  - [ ] Base image: `nextflow/nextflow:24.04.4`
  - [ ] Install system dependencies:
    - [ ] curl
    - [ ] python3
    - [ ] python3-pip
  - [ ] Install Google Cloud SDK:
    - [ ] Add to PATH
  - [ ] Install Python dependencies:
    - [ ] asyncpg (for PostgreSQL)
    - [ ] psycopg2-binary (sync fallback)
  - [ ] Copy scripts:
    - [ ] `entrypoint.sh` to `/entrypoint.sh`
    - [ ] `update_status.py` to `/update_status.py`
  - [ ] Make scripts executable
  - [ ] Set entrypoint to `/entrypoint.sh`

### Entrypoint Script

> **Spec References:**
> - [07-integration-spec.md#orchestrator-job-specification](../spec/07-integration-spec.md) - Environment variables
> - [12-recovery-spec.md#orchestrator-behavior](../spec/12-recovery-spec.md) - Resume flag handling

- [ ] Create `orchestrator/entrypoint.sh`:
  - [ ] Parse environment variables:
    - [ ] `RUN_ID`
    - [ ] `PIPELINE`
    - [ ] `PIPELINE_VERSION`
    - [ ] `CONFIG_GCS_PATH`
    - [ ] `PARAMS_GCS_PATH`
    - [ ] `WORK_DIR`
    - [ ] `IS_RECOVERY` — *See [12-recovery-spec.md#orchestrator-behavior](../spec/12-recovery-spec.md)*
  - [ ] Log startup information
  - [ ] Create local work directory
  - [ ] Download config and params from GCS:
    - [ ] `gsutil cp $CONFIG_GCS_PATH /config/nextflow.config`
    - [ ] `gsutil cp $PARAMS_GCS_PATH /config/params.yaml`
  - [ ] Build Nextflow command:
    - [ ] `nextflow run ${PIPELINE}`
    - [ ] `-r ${PIPELINE_VERSION}`
    - [ ] `-c /config/nextflow.config`
    - [ ] `-params-file /config/params.yaml`
    - [ ] `-work-dir ${WORK_DIR}`
    - [ ] `-with-trace`
    - [ ] `-with-timeline`
    - [ ] `-with-report`
    - [ ] Add `-resume` if `IS_RECOVERY=true` — *See [12-recovery-spec.md#nextflow-resume](../spec/12-recovery-spec.md)*
  - [ ] Execute Nextflow
  - [ ] Capture exit code
  - [ ] Upload logs to GCS — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*:
    - [ ] `.nextflow.log` → `logs/nextflow.log`
    - [ ] `trace.txt` → `logs/trace.txt`
    - [ ] `timeline.html` → `logs/timeline.html`
    - [ ] `report.html` → `logs/report.html`
  - [ ] Exit with Nextflow exit code

### Status Update Script

> **Spec References:**
> - [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md) - Update process
> - [07-integration-spec.md#orchestrator-status-updates](../spec/07-integration-spec.md) - Implementation details

- [ ] Create `orchestrator/update_status.py` — *See [06-data-model-spec.md#status-update-mechanism](../spec/06-data-model-spec.md)*:
  - [ ] Parse command line arguments:
    - [ ] `run_id` (positional)
    - [ ] `status` (positional)
    - [ ] `--started_at` (optional)
    - [ ] `--completed_at` (optional)
    - [ ] `--failed_at` (optional)
    - [ ] `--error_message` (optional)
    - [ ] `--error_task` (optional)
    - [ ] `--exit_code` (optional)
    - [ ] `--metrics` (optional, JSON string)
  - [ ] Read DATABASE_URL from environment — *See [07-integration-spec.md#batch-to-cloud-sql](../spec/07-integration-spec.md)*
  - [ ] Connect to PostgreSQL (sync connection)
  - [ ] Build UPDATE query:
    - [ ] Update `status` column
    - [ ] Update `updated_at` to NOW()
    - [ ] Update timestamp columns based on status
    - [ ] Update error fields if provided — *See [06-data-model-spec.md#error-fields](../spec/06-data-model-spec.md)*
    - [ ] Update metrics if provided — *See [06-data-model-spec.md#metrics-jsonb](../spec/06-data-model-spec.md)*
  - [ ] Execute query with parameterized values — *See [08-security-spec.md#sql-injection-prevention](../spec/08-security-spec.md)*
  - [ ] Log success/failure
  - [ ] Exit with appropriate code

### Nextflow Hooks Configuration

> **Spec References:**
> - [07-integration-spec.md#orchestrator-status-updates](../spec/07-integration-spec.md) - Hook implementation

- [ ] Create `orchestrator/nextflow.config.template` — *See [07-integration-spec.md#orchestrator-status-updates](../spec/07-integration-spec.md)*:
  - [ ] Include workflow hooks:
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

- [ ] Document Nextflow executor configuration — *See [07-integration-spec.md#nextflow-gcp-batch-executor](../spec/07-integration-spec.md)*:
  - [ ] Process block:
    ```groovy
    process {
      executor = 'google-batch'
      errorStrategy = 'retry'
      maxRetries = 3
      scratch = true
      resourceLimits = [cpus: 36, memory: 500.GB, time: 48.h]
    }
    ```
  - [ ] Google block:
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

- [ ] Create build script `scripts/build-orchestrator.sh` — *See [09-deployment-spec.md#container-build](../spec/09-deployment-spec.md)*:
  - [ ] Build Docker image:
    - [ ] `docker build -f orchestrator/Dockerfile.orchestrator -t ${IMAGE_NAME}:${VERSION} .`
    - [ ] Use `--platform linux/amd64`
  - [ ] Tag with version and latest
  - [ ] Push to Artifact Registry or GCR
- [ ] Add orchestrator build to CI/CD pipeline — *See [09-deployment-spec.md#github-actions-workflow](../spec/09-deployment-spec.md)*

### Orchestrator Integration Tests

- [ ] Create local orchestrator test:
  - [ ] Mock PostgreSQL connection
  - [ ] Test entrypoint with sample config
  - [ ] Verify update_status.py works
  - [ ] Test error handling paths

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
