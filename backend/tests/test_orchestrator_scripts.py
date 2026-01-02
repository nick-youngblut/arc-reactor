from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def _load_update_status(monkeypatch, tmp_path: Path):
    queries: list[tuple[str, dict]] = []

    class _Cursor:
        def __init__(self) -> None:
            self.rowcount = 1

        def execute(self, query: str, params: dict) -> None:
            queries.append((query, params))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Conn:
        def cursor(self):
            return _Cursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Psycopg2:
        def connect(self, _url):
            return _Conn()

    class _Extras:
        @staticmethod
        def Json(value):
            return value

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    monkeypatch.setitem(sys.modules, "psycopg2", _Psycopg2())
    monkeypatch.setitem(sys.modules, "psycopg2.extras", _Extras)

    module_path = Path("orchestrator/update_status.py")
    spec = importlib.util.spec_from_file_location("update_status", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module, queries


def test_update_status_builds_query(monkeypatch, tmp_path: Path) -> None:
    module, queries = _load_update_status(monkeypatch, tmp_path)

    exit_code = module.main(
        [
            "run-123",
            "completed",
            "--completed_at",
            "2025-12-30T20:01:00Z",
            "--metrics",
            '{"duration_seconds": 10}',
        ]
    )

    assert exit_code == 0
    assert queries
    query, params = queries[0]
    assert "status = %(status)s" in query
    assert params["status"] == "completed"
    assert "completed_at" in query


def test_update_status_missing_database_url(monkeypatch, tmp_path: Path) -> None:
    module, _queries = _load_update_status(monkeypatch, tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    exit_code = module.main(["run-123", "running"])
    assert exit_code == 1


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
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
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
