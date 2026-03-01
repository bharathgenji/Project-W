"""Integration tests for shared.clients.storage_client — local filesystem backend.

These tests use a temporary directory so they don't require any external services.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from shared.clients.storage_client import StorageClient  # noqa: E402


@pytest.fixture()
def storage(tmp_path: Path) -> StorageClient:
    """StorageClient backed by a temporary directory."""
    return StorageClient(backend="local", local_path=str(tmp_path))


@pytest.mark.integration
class TestStorageClientLocal:
    """Tests for the local-filesystem StorageClient."""

    def test_write_jsonl_then_read_back(self, storage: StorageClient):
        records = [
            {"id": "r-001", "type": "permit", "value": 100_000},
            {"id": "r-002", "type": "bid", "value": 250_000},
            {"id": "r-003", "type": "permit", "value": 50_000},
        ]
        written_path = storage.write_jsonl("permits/2026-02/batch-001.jsonl", records)
        assert Path(written_path).exists()

        read_back = storage.read_jsonl("permits/2026-02/batch-001.jsonl")
        assert len(read_back) == 3
        assert read_back[0]["id"] == "r-001"
        assert read_back[1]["value"] == 250_000
        assert read_back[2]["type"] == "permit"

    def test_write_creates_directories(self, storage: StorageClient):
        """Nested directories are created automatically."""
        storage.write_jsonl("deep/nested/path/data.jsonl", [{"a": 1}])
        result = storage.read_jsonl("deep/nested/path/data.jsonl")
        assert len(result) == 1
        assert result[0]["a"] == 1

    def test_read_nonexistent_returns_empty(self, storage: StorageClient):
        result = storage.read_jsonl("does/not/exist.jsonl")
        assert result == []

    def test_list_files(self, storage: StorageClient):
        storage.write_jsonl("permits/2026-01/batch-001.jsonl", [{"a": 1}])
        storage.write_jsonl("permits/2026-01/batch-002.jsonl", [{"b": 2}])
        storage.write_jsonl("permits/2026-02/batch-001.jsonl", [{"c": 3}])

        # List all under permits/
        files = storage.list_files("permits")
        assert len(files) == 3

        # List under a month
        files_jan = storage.list_files("permits/2026-01")
        assert len(files_jan) == 2

    def test_list_files_nonexistent_prefix(self, storage: StorageClient):
        files = storage.list_files("nonexistent")
        assert files == []

    def test_empty_records_write(self, storage: StorageClient):
        """Writing an empty list should create an empty file."""
        storage.write_jsonl("empty.jsonl", [])
        result = storage.read_jsonl("empty.jsonl")
        assert result == []

    def test_records_with_datetime(self, storage: StorageClient):
        """Records with datetime values should be serialized via default=str."""
        from datetime import datetime

        records = [{"id": "dt-001", "posted": datetime(2026, 2, 25, 12, 0, 0)}]
        storage.write_jsonl("datetime-test.jsonl", records)
        result = storage.read_jsonl("datetime-test.jsonl")
        assert len(result) == 1
        assert "2026" in result[0]["posted"]

    def test_overwrite_existing_file(self, storage: StorageClient):
        """Writing to the same path overwrites the previous content."""
        storage.write_jsonl("overwrite.jsonl", [{"v": 1}])
        storage.write_jsonl("overwrite.jsonl", [{"v": 2}, {"v": 3}])
        result = storage.read_jsonl("overwrite.jsonl")
        assert len(result) == 2
        assert result[0]["v"] == 2

    def test_special_characters_in_data(self, storage: StorageClient):
        """JSON with special characters should round-trip correctly."""
        records = [
            {"desc": 'He said "hello" & goodbye'},
            {"desc": "Line1\nLine2\tTabbed"},
            {"desc": "Unicode: \u00e9\u00e8\u00ea\u00f1\u00fc"},
        ]
        storage.write_jsonl("special.jsonl", records)
        result = storage.read_jsonl("special.jsonl")
        assert len(result) == 3
        assert result[0]["desc"] == 'He said "hello" & goodbye'
        assert "\n" in result[1]["desc"]
