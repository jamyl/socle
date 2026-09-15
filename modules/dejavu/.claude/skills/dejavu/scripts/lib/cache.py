"""On-disk fetch cache shared by the skill and the Node CLI.

Both frontends call the same scripts, so both hit the same cache: a run in
Claude Code warms the cache for a later `dejavu "..."` on the command line and
vice versa. Re-running the same problem is then free and works offline.

Entries are plain files keyed by a hash of the URL, with the fetch timestamp
in the payload so a TTL can be applied at read time rather than at write time
(the same entry can be fresh for a document lookup and stale for a search).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

# TTLs by kind of request. Searches move as new work is published; a document
# fetched by immutable id (an arXiv id, a DOI, an accession number) does not
# change, so it never needs re-fetching.
TTL_SEARCH = 7 * 24 * 3600
TTL_DOCUMENT = None  # never expires
TTL_FULLTEXT = 30 * 24 * 3600
TTL_FILING_SEARCH = 24 * 3600
TTL_CODE = 7 * 24 * 3600


def cache_dir() -> Path:
    override = os.environ.get("DEJAVU_CACHE_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME", "").strip()
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "dejavu"


def _key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _entry_path(url: str) -> Path:
    key = _key(url)
    # Two-level fan-out keeps directory listings small once a cache has grown.
    return cache_dir() / "http" / key[:2] / f"{key}.json"


def throttle_path(host: str) -> Path:
    safe = host.replace("/", "_") or "unknown"
    return cache_dir() / "throttle" / safe


def read(url: str, *, ttl: float | None, allow_stale: bool = False) -> str | None:
    path = _entry_path(url)
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    if allow_stale or ttl is None:
        return payload.get("body")
    age = time.time() - float(payload.get("fetched_at", 0))
    if age > ttl:
        return None
    return payload.get("body")


def write(url: str, body: str) -> None:
    path = _entry_path(url)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"url": url, "fetched_at": time.time(), "body": body}))
        tmp.replace(path)
    except OSError:
        # A failed cache write must never fail the fetch it was meant to speed up.
        pass


def stats() -> dict:
    root = cache_dir() / "http"
    if not root.exists():
        return {"entries": 0, "bytes": 0, "dir": str(cache_dir())}
    entries = list(root.rglob("*.json"))
    return {
        "entries": len(entries),
        "bytes": sum(p.stat().st_size for p in entries),
        "dir": str(cache_dir()),
    }


def clear() -> int:
    root = cache_dir() / "http"
    if not root.exists():
        return 0
    removed = 0
    for path in root.rglob("*.json"):
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass
    return removed
