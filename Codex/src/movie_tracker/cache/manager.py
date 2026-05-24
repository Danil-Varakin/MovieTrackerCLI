from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from diskcache import Cache

from movie_tracker.config import AppConfig


class CacheManager:
    def __init__(self, config: AppConfig) -> None:
        self.enabled = bool(config.data["cache"].get("enabled", True))
        self._cache: Cache | None = None
        if self.enabled:
            config.cache_dir.mkdir(parents=True, exist_ok=True)
            size_limit = int(config.data["cache"].get("max_size_mb", 100)) * 1024 * 1024
            self._cache = Cache(str(config.cache_dir), size_limit=size_limit)

    @staticmethod
    def make_key(namespace: str, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"{namespace}:{digest}"

    def get(self, key: str) -> Any | None:
        if not self.enabled or self._cache is None:
            return None
        cached = self._cache.get(key)
        if not isinstance(cached, dict) or "payload" not in cached:
            return None
        return cached["payload"]

    def set(self, key: str, payload: Any, *, ttl_seconds: int) -> None:
        if not self.enabled or self._cache is None or ttl_seconds <= 0:
            return
        self._cache.set(
            key,
            {"stored_at": time.time(), "payload": payload},
            expire=ttl_seconds,
        )

    def clear(self, *, older_than_hours: int | None = None) -> int:
        if not self.enabled or self._cache is None:
            return 0
        if older_than_hours is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        threshold = time.time() - older_than_hours * 3600
        removed = 0
        for key in list(self._cache.iterkeys()):
            cached = self._cache.get(key)
            if isinstance(cached, dict) and cached.get("stored_at", time.time()) < threshold:
                del self._cache[key]
                removed += 1
        return removed
