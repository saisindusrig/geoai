"""In-process cache for expensive design-generation intermediates."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

_CACHE: dict[str, tuple[float, Any]] = {}
_TTL_SECONDS = 3600


def _now() -> float:
    return time.time()


def _purge_expired() -> None:
    cutoff = _now() - _TTL_SECONDS
    expired = [k for k, (ts, _) in _CACHE.items() if ts < cutoff]
    for key in expired:
        _CACHE.pop(key, None)


def scenario_input_hash(
    project_id: int,
    boundary: dict | None,
    alignment: dict | None,
    params: dict,
) -> str:
    payload = json.dumps(
        {
            "project_id": project_id,
            "boundary": boundary,
            "alignment": alignment,
            "params": params,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def get_cached(key: str) -> Any | None:
    _purge_expired()
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if ts < _now() - _TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return value


def set_cached(key: str, value: Any) -> None:
    _CACHE[key] = (_now(), value)


def clear_cache() -> None:
    _CACHE.clear()
