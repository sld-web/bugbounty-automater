"""Caching layer for OpenAI responses."""
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL support."""

    def __init__(self, value: Any, ttl_seconds: int = 86400):
        self.value = value
        self.created_at = datetime.now(timezone.utc)
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl_seconds <= 0:
            return False
        expiry = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) > expiry

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
        }


class OpenAICache:
    """In-memory cache for OpenAI responses."""

    def __init__(self, default_ttl: int = 86400):
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        self._total_size = 0

    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate cache key from prefix and data."""
        if isinstance(data, dict):
            content = json.dumps(data, sort_keys=True)
        elif isinstance(data, str):
            content = data
        else:
            content = str(data)

        hash_obj = hashlib.sha256(content.encode())
        return f"{prefix}:{hash_obj.hexdigest()[:16]}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            logger.debug(f"Cache miss: {key}")
            return None

        if entry.is_expired():
            self._cache.pop(key, None)
            self._misses += 1
            logger.debug(f"Cache expired: {key}")
            return None

        self._hits += 1
        logger.debug(f"Cache hit: {key}")
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl if ttl is not None else self.default_ttl
        self._cache[key] = CacheEntry(value, ttl)
        self._total_size += 1
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            self._cache.pop(key)
            logger.debug(f"Cache deleted: {key}")
            return True
        return False

    def clear(self) -> int:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._total_size = 0
        logger.info(f"Cache cleared: {count} entries removed")
        return count

    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired()
        ]
        for key in expired_keys:
            self._cache.pop(key, None)

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total,
        }

    def cache_program(self, policy_text: str, result: dict) -> None:
        """Cache program parsing result."""
        key = self._generate_key("program", policy_text)
        self.set(key, result, ttl=86400 * 7)

    def get_cached_program(self, policy_text: str) -> Optional[dict]:
        """Get cached program parsing result."""
        key = self._generate_key("program", policy_text)
        return self.get(key)

    def cache_finding(self, finding_hash: str, result: dict) -> None:
        """Cache finding enhancement result."""
        key = self._generate_key("finding", finding_hash)
        self.set(key, result, ttl=86400)

    def get_cached_finding(self, finding_hash: str) -> Optional[dict]:
        """Get cached finding enhancement."""
        key = self._generate_key("finding", finding_hash)
        return self.get(key)

    def cache_summary(self, findings_hash: str, result: str) -> None:
        """Cache report summary."""
        key = self._generate_key("summary", findings_hash)
        self.set(key, result, ttl=86400)

    def get_cached_summary(self, findings_hash: str) -> Optional[str]:
        """Get cached report summary."""
        key = self._generate_key("summary", findings_hash)
        return self.get(key)


openai_cache = OpenAICache()
