#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*"
}

require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
}

require_env RUN_ID
require_env PIPELINE
require_env PIPELINE_VERSION
require_env CONFIG_GCS_PATH
require_env PARAMS_GCS_PATH
require_env WORK_DIR
require_env IS_RECOVERY
require_env DATABASE_URL

CONFIG_DIR="${CONFIG_DIR:-/config}"
LOCAL_WORK_DIR="${LOCAL_WORK_DIR:-/work}"

log "Starting Nextflow orchestrator for run ${RUN_ID}"
log "Pipeline: ${PIPELINE} (${PIPELINE_VERSION})"
log "Config: ${CONFIG_GCS_PATH}"
log "Params: ${PARAMS_GCS_PATH}"
log "Work dir: ${WORK_DIR}"
log "Recovery: ${IS_RECOVERY}"

mkdir -p "${CONFIG_DIR}" "${LOCAL_WORK_DIR}"

log "Downloading config and params from GCS"
gsutil cp "${CONFIG_GCS_PATH}" "${CONFIG_DIR}/nextflow.config"
gsutil cp "${PARAMS_GCS_PATH}" "${CONFIG_DIR}/params.yaml"

if [ -f "/nextflow.config.template" ]; then
  log "Appending Arc Reactor hooks to config"
  cat "/nextflow.config.template" >> "${CONFIG_DIR}/nextflow.config"
fi

if ! grep -q '^run_id:' "${CONFIG_DIR}/params.yaml"; then
  printf '\nrun_id: "%s"\n' "${RUN_ID}" >> "${CONFIG_DIR}/params.yaml"
fi

cmd=(
  nextflow run "${PIPELINE}"
  -r "${PIPELINE_VERSION}"
  -c "${CONFIG_DIR}/nextflow.config"
  -params-file "${CONFIG_DIR}/params.yaml"
  -work-dir "${WORK_DIR}"
  -with-trace
  -with-timeline
  -with-report
)

if [ "${IS_RECOVERY}" = "true" ]; then
  cmd+=( -resume )
fi

log "Launching Nextflow"
cd "${LOCAL_WORK_DIR}"
set +e
"${cmd[@]}"
exit_code=$?
set -e

bucket="${CONFIG_GCS_PATH#gs://}"
bucket="${bucket%%/*}"
log_root="gs://${bucket}/runs/${RUN_ID}/logs"

log "Uploading logs to ${log_root}"
upload_with_retry() {
  local src="$1"
  local dest="$2"
  local attempts=3
  local delay=2

  for attempt in $(seq 1 "${attempts}"); do
    if gsutil -m cp "${src}" "${dest}"; then
      return 0
    fi
    log "Warning: failed to upload ${src} (attempt ${attempt}/${attempts})"
    sleep "${delay}"
    delay=$((delay * 2))
  done

  log "Warning: giving up on uploading ${src} after ${attempts} attempts"
  return 1
}

if [ -f ".nextflow.log" ]; then
  upload_with_retry ".nextflow.log" "${log_root}/nextflow.log" || true
fi
if [ -f "trace.txt" ]; then
  upload_with_retry "trace.txt" "${log_root}/trace.txt" || true
fi
if [ -f "timeline.html" ]; then
  upload_with_retry "timeline.html" "${log_root}/timeline.html" || true
fi
if [ -f "report.html" ]; then
  upload_with_retry "report.html" "${log_root}/report.html" || true
fi

log "Nextflow finished with exit code ${exit_code}"
exit "${exit_code}"
