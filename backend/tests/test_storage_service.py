from __future__ import annotations

from backend.services.storage import StorageService


class _Blob:
    def __init__(self, name: str, content: bytes = b"data") -> None:
        self.name = name
        self._content = content
        self.size = len(content)
        self.updated = "2025-01-01T00:00:00Z"
        self.metadata = {}

    def upload_from_string(self, content: str | bytes) -> None:
        self._content = content.encode() if isinstance(content, str) else content

    def download_as_bytes(self) -> bytes:
        return self._content

    def exists(self) -> bool:
        return True

    def generate_signed_url(self, *args, **kwargs) -> str:
        return "https://signed-url"


class _Bucket:
    def __init__(self) -> None:
        self.blobs: dict[str, _Blob] = {}

    def blob(self, name: str) -> _Blob:
        blob = self.blobs.get(name)
        if not blob:
            blob = _Blob(name)
            self.blobs[name] = blob
        return blob

    def exists(self) -> bool:
        return True


class _Client:
    def __init__(self, bucket: _Bucket) -> None:
        self._bucket = bucket

    def bucket(self, name: str) -> _Bucket:
        return self._bucket

    def list_blobs(self, name: str, prefix: str, max_results: int | None = None):
        blobs = [blob for blob in self._bucket.blobs.values() if blob.name.startswith(prefix)]
        if max_results is not None:
            return blobs[:max_results]
        return blobs


def test_storage_upload_and_download() -> None:
    bucket = _Bucket()
    client = _Client(bucket)
    service = StorageService(client=client, bucket_name="arc-reactor-runs")

    uri = service.upload_run_file("run-1", "inputs.csv", "abc", "dev@arc.org")
    assert uri == "gs://arc-reactor-runs/runs/run-1/inputs/inputs.csv"

    blob = bucket.blobs["runs/run-1/inputs/inputs.csv"]
    assert blob.metadata["run-id"] == "run-1"
    assert blob.metadata["user-email"] == "dev@arc.org"

    downloaded = service.download_file(uri)
    assert downloaded == b"abc"


def test_storage_listing_and_exists() -> None:
    bucket = _Bucket()
    client = _Client(bucket)
    service = StorageService(client=client, bucket_name="arc-reactor-runs")

    service.upload_run_file("run-1", "inputs.csv", "abc", "dev@arc.org")
    files = service.list_files("runs/run-1")
    assert files

    exists = service.files_exist(["gs://arc-reactor-runs/runs/run-1/inputs/inputs.csv"])
    assert exists["gs://arc-reactor-runs/runs/run-1/inputs/inputs.csv"] is True

    signed = service.generate_signed_url(
        "gs://arc-reactor-runs/runs/run-1/inputs/inputs.csv"
    )
    assert signed == "https://signed-url"


def test_storage_run_files_helpers() -> None:
    bucket = _Bucket()
    client = _Client(bucket)
    service = StorageService(client=client, bucket_name="arc-reactor-runs")

    uploaded = service.upload_run_files(
        "run-2",
        {
            "samplesheet.csv": "a,b",
            "nextflow.config": "params {}",
            "params.yaml": "genome: GRCh38",
        },
        "dev@arc.org",
    )
    assert len(uploaded) == 3

    files = service.get_run_files("run-2")
    assert files["inputs"]

    content = service.get_file_content(uploaded[0], text=True)
    assert isinstance(content, str)

    assert service.check_work_dir_exists("run-2") is False
    bucket.blob("runs/run-2/work/.keep").upload_from_string("x")
    assert service.check_work_dir_exists("run-2") is True
