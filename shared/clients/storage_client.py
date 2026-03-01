from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StorageClient:
    def __init__(
        self,
        backend: str = "local",
        local_path: str = "./data/raw",
        bucket_name: str = "",
    ) -> None:
        self.backend = backend
        self.local_path = Path(local_path)
        self.bucket_name = bucket_name

    def write_jsonl(self, path: str, records: list[dict[str, Any]]) -> str:
        """Write records as JSONL to storage. Returns the storage path."""
        if self.backend == "local":
            full_path = self.local_path / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record, default=str) + "\n")
            return str(full_path)
        else:
            from google.cloud import storage  # type: ignore[attr-defined]

            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(path)
            content = "\n".join(json.dumps(r, default=str) for r in records)
            blob.upload_from_string(content, content_type="application/x-ndjson")
            return f"gs://{self.bucket_name}/{path}"

    def read_jsonl(self, path: str) -> list[dict[str, Any]]:
        """Read JSONL records from storage."""
        if self.backend == "local":
            full_path = self.local_path / path
            if not full_path.exists():
                return []
            records = []
            with open(full_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            return records
        else:
            from google.cloud import storage  # type: ignore[attr-defined]

            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(path)
            content = blob.download_as_text()
            return [json.loads(line) for line in content.strip().split("\n") if line.strip()]

    def list_files(self, prefix: str) -> list[str]:
        """List files under a prefix."""
        if self.backend == "local":
            base = self.local_path / prefix
            if not base.exists():
                return []
            return [str(p.relative_to(self.local_path)) for p in base.rglob("*") if p.is_file()]
        else:
            from google.cloud import storage  # type: ignore[attr-defined]

            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
