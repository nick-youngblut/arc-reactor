from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_entrypoint_uploads_logs(tmp_path: Path) -> None:
    entrypoint = Path("orchestrator/entrypoint.sh")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    gcs_root = tmp_path / "gcs"
    config_src = gcs_root / "bucket" / "runs" / "run-123" / "inputs"
    config_src.mkdir(parents=True)
    (config_src / "nextflow.config").write_text("process {}")
    (config_src / "params.yaml").write_text("foo: bar\n")

    gsutil_script = bin_dir / "gsutil"
    gsutil_script.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [ \"$1\" = \"-m\" ]; then
  shift
fi
if [ \"$1\" != \"cp\" ]; then
  echo \"unsupported\" >&2
  exit 1
fi
src=\"$2\"
dest=\"$3\"
root=\"${MOCK_GCS_ROOT}\"
map_path() {
  local uri=\"$1\"
  uri=\"${uri#gs://}\"
  echo \"${root}/${uri}\"
}
if [[ \"$src\" == gs://* ]]; then
  src=\"$(map_path \"$src\")\"
fi
if [[ \"$dest\" == gs://* ]]; then
  dest=\"$(map_path \"$dest\")\"
fi
mkdir -p \"$(dirname \"$dest\")\"
cp \"$src\" \"$dest\"
"""
    )
    gsutil_script.chmod(0o755)

    nextflow_script = bin_dir / "nextflow"
    nextflow_script.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
echo \"nextflow log\" > .nextflow.log
echo \"trace\" > trace.txt
echo \"timeline\" > timeline.html
echo \"report\" > report.html
exit 0
"""
    )
    nextflow_script.chmod(0o755)

    config_dir = tmp_path / "config"
    work_dir = tmp_path / "work"

    env = os.environ.copy()
    env.update(
        {
            "RUN_ID": "run-123",
            "PIPELINE": "nf-core/scrnaseq",
            "PIPELINE_VERSION": "2.7.1",
            "CONFIG_GCS_PATH": "gs://bucket/runs/run-123/inputs/nextflow.config",
            "PARAMS_GCS_PATH": "gs://bucket/runs/run-123/inputs/params.yaml",
            "WORK_DIR": "gs://bucket/runs/run-123/work/",
            "IS_RECOVERY": "false",
            "WEBLOG_URL": "https://arc-reactor-weblog.example.com/weblog",
            "WEBLOG_SECRET": "secret",
            "CONFIG_DIR": str(config_dir),
            "LOCAL_WORK_DIR": str(work_dir),
            "MOCK_GCS_ROOT": str(gcs_root),
            "PATH": f"{bin_dir}{os.pathsep}{env.get('PATH', '')}",
        }
    )

    result = subprocess.run([str(entrypoint)], env=env, check=False, capture_output=True)
    assert result.returncode == 0

    log_root = gcs_root / "bucket" / "runs" / "run-123" / "logs"
    assert (log_root / "nextflow.log").exists()
    assert (log_root / "trace.txt").exists()
    assert (log_root / "timeline.html").exists()
    assert (log_root / "report.html").exists()
