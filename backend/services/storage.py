from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Iterable

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import storage


def _parse_gcs_uri(gcs_uri: str) -> tuple[str, str]:
    if not gcs_uri.startswith("gs://"):
        raise ValueError("GCS URI must start with gs://")
    path = gcs_uri[len("gs://") :]
    bucket_name, _, blob_name = path.partition("/")
    if not bucket_name or not blob_name:
        raise ValueError("GCS URI must include bucket and object path")
    return bucket_name, blob_name


@dataclass
class StorageService:
    client: storage.Client
    bucket_name: str

    @classmethod
    def create(cls, settings: object) -> "StorageService":
        bucket_name = getattr(settings, "nextflow_bucket", None)
        if not bucket_name:
            raise ValueError("nextflow_bucket must be configured")
        try:
            client = storage.Client()
        except DefaultCredentialsError:
            client = storage.Client.create_anonymous_client()
        return cls(client=client, bucket_name=bucket_name)

    def _bucket(self) -> storage.Bucket:
        return self.client.bucket(self.bucket_name)

    def upload_run_file(
        self,
        run_id: str,
        filename: str,
        content: str | bytes,
        user_email: str,
    ) -> str:
        blob = self._bucket().blob(f"runs/{run_id}/inputs/{filename}")
        created_at = datetime.now(timezone.utc).isoformat()
        blob.metadata = {
            "run-id": run_id,
            "user-email": user_email,
            "created-at": created_at,
        }
        blob.upload_from_string(content)
        return f"gs://{self.bucket_name}/runs/{run_id}/inputs/{filename}"

    def upload_run_files(
        self,
        run_id: str,
        files: dict[str, str | bytes],
        user_email: str,
    ) -> list[str]:
        uris: list[str] = []
        for filename, content in files.items():
            uri = self.upload_run_file(run_id, filename, content, user_email)
            uris.append(uri)
        return uris

    def get_run_files(self, run_id: str) -> dict[str, list[dict[str, object]]]:
        prefix = f"runs/{run_id}/"
        grouped: dict[str, list[dict[str, object]]] = {"inputs": [], "results": [], "logs": []}
        for entry in self.list_files(prefix):
            name = str(entry["name"])
            if not name.startswith(prefix):
                continue
            rel = name[len(prefix) :]
            if "/" not in rel:
                continue
            top_dir = rel.split("/", 1)[0]
            if top_dir not in grouped:
                continue
            gcs_uri = f"gs://{self.bucket_name}/{name}"
            grouped[top_dir].append(
                {
                    "name": rel,
                    "size": entry.get("size"),
                    "updated": entry.get("updated"),
                    "gcs_uri": gcs_uri,
                }
            )
        return grouped

    def get_file_content(self, gcs_uri: str, text: bool = True) -> str | bytes:
        data = self.download_file(gcs_uri)
        if not text:
            return data
        return data.decode("utf-8", errors="replace")

    def check_work_dir_exists(self, run_id: str) -> bool:
        prefix = f"runs/{run_id}/work/"
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix, max_results=1)
        return any(True for _ in blobs)

    def download_file(self, gcs_uri: str) -> bytes:
        bucket_name, blob_name = _parse_gcs_uri(gcs_uri)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()

    def list_files(self, prefix: str) -> list[dict[str, object]]:
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        return [
            {
                "name": blob.name,
                "size": blob.size,
                "updated": blob.updated,
            }
            for blob in blobs
        ]

    def files_exist(self, gcs_paths: Iterable[str]) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for path in gcs_paths:
            bucket_name, blob_name = _parse_gcs_uri(path)
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            results[path] = blob.exists()
        return results

    def generate_signed_url(self, gcs_uri: str, expiration_minutes: int = 60) -> str:
        bucket_name, blob_name = _parse_gcs_uri(gcs_uri)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET",
        )

    def health_check(self) -> bool:
        try:
            return self._bucket().exists()
        except Exception:
            return False
