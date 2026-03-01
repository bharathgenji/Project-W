"""Unit tests for services/api-server/cache — in-memory TTL cache."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_api_path = str(Path(__file__).resolve().parents[2] / "services" / "api-server")
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)

from cache import TTLCache  # noqa: E402


@pytest.mark.unit
class TestTTLCache:
    """Tests for the simple TTL cache used by the API server."""

    def test_set_then_get_returns_value(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", {"data": [1, 2, 3]})
        assert cache.get("key1") == {"data": [1, 2, 3]}

    def test_get_nonexistent_key_returns_none(self):
        cache = TTLCache(ttl_seconds=60)
        assert cache.get("does_not_exist") is None

    def test_expired_key_returns_none_with_mock(self):
        """Use mocked time to verify expiration without sleeping."""
        cache = TTLCache(ttl_seconds=10)

        t0 = 1000.0
        with patch("cache.time.time", return_value=t0):
            cache.set("key2", "hello")

        # Still valid at t0+5
        with patch("cache.time.time", return_value=t0 + 5):
            assert cache.get("key2") == "hello"

        # Expired at t0+11 (TTL=10)
        with patch("cache.time.time", return_value=t0 + 11):
            assert cache.get("key2") is None

    def test_expired_key_returns_none_with_sleep(self):
        """Real TTL test with a very short TTL."""
        cache = TTLCache(ttl_seconds=1)
        cache.set("ephemeral", 42)
        assert cache.get("ephemeral") == 42
        time.sleep(1.1)
        assert cache.get("ephemeral") is None

    def test_overwrite_existing_key(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key3", "old")
        cache.set("key3", "new")
        assert cache.get("key3") == "new"

    def test_invalidate_removes_key(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key4", "value")
        cache.invalidate("key4")
        assert cache.get("key4") is None

    def test_invalidate_nonexistent_key_no_error(self):
        cache = TTLCache(ttl_seconds=60)
        cache.invalidate("never_existed")  # should not raise

    def test_clear_removes_all(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.get("c") is None

    def test_different_value_types(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("str", "hello")
        cache.set("int", 42)
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"k": "v"})
        cache.set("none", None)

        assert cache.get("str") == "hello"
        assert cache.get("int") == 42
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"k": "v"}
        # None is a valid cached value, but our cache considers None as not-found
        # Actually, looking at the cache impl: it stores (timestamp, None) which is truthy
        # so get returns None correctly as a value.

    def test_default_ttl(self):
        """Default TTL is 3600 seconds."""
        cache = TTLCache()
        assert cache._ttl == 3600
