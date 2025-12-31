# Arc Reactor - Nextflow Recovery Specification

## Overview

This document defines the recovery workflow for Nextflow runs using
`nextflow run -resume` on GCP Batch. Recovery allows users to re-run a failed
or cancelled workflow while reusing the existing Nextflow work directory so
completed tasks are not recomputed.

## Goals

- Provide a clear, supported recovery path after failure or cancellation.
- Ensure recovery reuses the correct `work/` directory in GCS.
- Preserve run provenance (who recovered, when, from which run).
- Prevent unsafe or confusing recovery attempts (missing work dir, wrong params).

## Key Concepts

### Work Directory Reuse

Nextflow can resume execution if the new job points to the original work
directory and uses `-resume`. For Arc Reactor, the work directory is:

```
gs://{settings.nextflow_bucket}/runs/{run_id}/work/
```

### Recovery Run vs Original Run

Recovery creates a **new run record** that references the original run as its
`parent_run_id`, but uses the same work directory. This preserves auditability
and allows users to track a distinct recovery attempt.

## Recovery Preconditions

Recovery is allowed only when all of the following are true:

1. Original run is in a terminal state (`failed` or `cancelled`).
2. `work/` directory exists for the original run in GCS.
3. Pipeline name and version are unchanged (unless explicitly approved).
4. Required inputs are unchanged or compatible with the original work directory.
5. User confirms recovery (HITL).

## Backend Workflow

### API

```
POST /api/runs/{id}/recover
```

**Request Body:**
```json
{
  "reuse_work_dir": true,
  "notes": "Retry after fixing config",
  "override_params": { "max_memory": "64.GB" },
  "override_config": "optional updated config content"
}
```

**Response:**
```json
{
  "run_id": "run-xyz789",
  "status": "submitted",
  "parent_run_id": "run-abc123",
  "work_dir": "gs://arc-reactor-runs/runs/run-abc123/work/",
  "message": "Recovery run submitted with -resume."
}
```

### Run Record Fields

Add the following fields to the run schema:

```text
parent_run_id: string | null   # Original run ID if recovered
is_recovery: boolean           # True when created via recover endpoint
recovery_notes: string | null  # User-provided notes
reused_work_dir: string | null # Work dir reused for -resume
```

### Submission Behavior

When recovery is requested:

1. Validate that the original `work/` directory exists.
2. Create a new run record with `parent_run_id`.
3. Submit a new GCP Batch job using:
   - `-resume`
   - `-work-dir` pointing to the original run work directory
   - Updated params/config if provided (must be compatible)
4. Store `reused_work_dir` on the new run record.

## Orchestrator Behavior

The orchestrator must support `-resume` for recovery runs:

```bash
nextflow run ${PIPELINE} \
  -r ${PIPELINE_VERSION} \
  -work-dir ${WORK_DIR} \
  -resume \
  -params-file ${PARAMS_GCS_PATH} \
  -c ${CONFIG_GCS_PATH}
```

For non-recovery runs, `-resume` is not used and `WORK_DIR` points to the new
run’s work directory.

## Frontend Workflow

### Run Detail Actions

When a run is in `failed` or `cancelled` state, show a **Recover Run** action.

Recovery modal requires:
- Confirmation that recovery reuses previous work directory
- Optional notes
- Optional override parameters/config (advanced users)

### UI Copy

- **Title:** Recover run with `-resume`
- **Body:** "This will re-run the workflow and reuse completed tasks from the
  previous work directory."

## Observability

Log entries must include:
- `parent_run_id`
- `is_recovery`
- `reused_work_dir`

## Failure Modes

| Failure | Behavior | Message |
|---------|----------|---------|
| Work dir missing | Block recovery | "Recovery unavailable: work directory not found." |
| Params incompatible | Block or warn | "Parameters changed in a way that may invalidate cache." |
| Original run not terminal | Block recovery | "Only failed or cancelled runs can be recovered." |

## Security & HITL

Recovery is a cost-incurring operation and must require explicit user approval.

## Implementation Phases

1. **Phase 1:** Backend recovery endpoint + `-resume` support
2. **Phase 2:** Frontend recovery UI + notes/overrides
3. **Phase 3:** Compatibility checks and advanced warnings
