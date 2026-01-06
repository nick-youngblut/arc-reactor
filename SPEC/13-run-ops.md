# Run Operations Guide

This document summarizes the end-to-end run flow and file lifecycle for Arc Reactor runs. It mirrors
`spec/06-data-model-spec.md` and `spec/02-architecture-overview.md` for quick reference.

## Status Flow

1. Run record created in PostgreSQL with status `pending`.
2. Inputs are uploaded to GCS and the Batch job is submitted; status becomes `submitted`.
3. Orchestrator starts and Nextflow emits `started` weblog event.
4. Backend updates status to `completed` or `failed` on weblog events.
5. Task-level updates stream into the `tasks` table in real time.

Valid transitions:
```
pending -> submitted -> running -> completed|failed
pending -> cancelled
submitted -> cancelled|failed
running -> cancelled
```

## GCS File Lifecycle

Run inputs and outputs are organized under `gs://<bucket>/runs/<run_id>/`:

- `inputs/`
  - `samplesheet.csv` (permanent)
  - `nextflow.config` (permanent)
  - `params.yaml` (permanent)
- `work/` (30-day retention via lifecycle policy)
- `results/` (permanent)
- `logs/`
  - `nextflow.log` (permanent)
  - `trace.txt` (permanent)
  - `timeline.html` (permanent)
  - `report.html` (permanent)
