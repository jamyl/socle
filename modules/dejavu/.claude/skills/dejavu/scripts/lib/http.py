"""Deterministic HTTP for every dejavu provider.

Standard library only, on purpose: the skill ships this directory and has to
run wherever Claude Code runs, including behind a corporate proxy, with no
install step. `urllib` reads HTTPS_PROXY / HTTP_PROXY / NO_PROXY from the
environment through its default ProxyHandler, which is the whole reason the
fetch layer lives here instead of in the Node CLI (Node's global fetch ignores
those variables unless an agent is wired up explicitly).

Three things every call gets: a declared User-Agent, per-host request spacing
that survives across process invocations, and bounded retries.
"""

from __future__ import annotations

import gzip
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from . import cache as cache_mod

# Every API used here either asks for or rewards a contact address:
# arXiv and Crossref ask clients to identify themselves, OpenAlex routes
# `mailto` callers to a faster pool, and the SEC *requires* a declared
# User-Agent naming a contact (sec.gov/os/accessing-edgar-data).
DEFAULT_CONTACT = "dejavu@example.invalid"
VERSION = "0.2.0"


def contact() -> str:
    return os.environ.get("DEJAVU_CONTACT", "").strip() or DEFAULT_CONTACT


def user_agent() -> str:
    return f"dejavu/{VERSION} (https://github.com/jamyl/dejavu; mailto:{contact()})"


# Minimum seconds between requests to the same host. Each number traces to a
# published limit or an observed response header, not to taste:
#   export.arxiv.org / arxiv.org / ar5iv  — arXiv's terms of use state "no more
#     than one request every three seconds, and limit requests to a single
#     connection at a time" (info.arxiv.org/help/api/tou.html).
#   api.crossref.org — observed `x-rate-limit-limit: 3` per `x-rate-limit-interval: 1s`,
#     so 0.34s keeps us just inside 3/s.
#   *.sec.gov — "Current max request rate: 10 requests/second"
#     (sec.gov/os/accessing-edgar-data); 0.11s is 9/s, one under the cap.
#   api.github.com — unauthenticated search is capped at 10 requests/minute
#     (observed `x-ratelimit-limit: 10`, `x-ratelimit-resource: search`), so 6s.
#   api.openalex.org — no per-second limit published; observed a daily credit
#     budget (`x-ratelimit-limit: 1000`). 0.2s is politeness, not a hard rule.
#   others — no published limit found; 0.5s chosen as a conservative default.
HOST_MIN_INTERVAL = {
    "export.arxiv.org": 3.0,
    "arxiv.org": 3.0,
    "ar5iv.labs.arxiv.org": 3.0,
    "api.crossref.org": 0.34,
    "api.openalex.org": 0.2,
    "www.ebi.ac.uk": 0.5,
    "api.biorxiv.org": 0.5,
    "huggingface.co": 0.5,
    "api.github.com": 6.0,
    "efts.sec.gov": 0.11,
    "data.sec.gov": 0.11,
    "www.sec.gov": 0.11,
}
DEFAULT_MIN_INTERVAL = 0.5

# Retries cover transient conditions only. 429 and 5xx are worth retrying;
# a 400 means the query itself is wrong and retrying just wastes the budget.
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 1.0
# Long enough for arXiv's full-text HTML (observed ~400 KB) on a slow link,
# short enough that a hung provider can't stall a whole run.
DEFAULT_TIMEOUT_SECONDS = 30.0


class HTTPError(RuntimeError):
    """A request that could not be completed within the retry budget."""

    def __init__(self, message: str, *, status: int | None = None, url: str = ""):
        super().__init__(message)
        self.status = status
        self.url = url


@dataclass
class Response:
    url: str
    status: int
    body: str
    from_cache: bool = False
    stale: bool = False
    headers: dict = field(default_factory=dict)

    def json(self):
        return json.loads(self.body)


def _throttle(host: str) -> None:
    """Space out requests to one host, across processes.

    The skill calls these scripts several times in a row (once per provider,
    then again for full text), each a fresh process. In-process spacing would
    reset every time and quietly breach arXiv's one-request-per-three-seconds
    rule, so the last-hit timestamp lives on disk.
    """
    interval = HOST_MIN_INTERVAL.get(host, DEFAULT_MIN_INTERVAL)
    stamp_path = cache_mod.throttle_path(host)
    try:
        last = float(stamp_path.read_text())
    except (OSError, ValueError):
        last = 0.0
    wait = interval - (time.time() - last)
    if wait > 0:
        time.sleep(wait)
    try:
        stamp_path.parent.mkdir(parents=True, exist_ok=True)
        stamp_path.write_text(str(time.time()))
    except OSError:
        # A read-only cache dir shouldn't break fetching; we just lose spacing
        # across processes and fall back to in-request politeness.
        pass


def _read_body(resp) -> str:
    raw = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)
    charset = resp.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def _request_once(url: str, headers: dict, timeout: float) -> Response:
    req = urllib.request.Request(url, headers=headers, method="GET")
    # urlopen goes through the default opener, which installs a ProxyHandler
    # built from the environment (HTTPS_PROXY / HTTP_PROXY / NO_PROXY).
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return Response(
            url=url,
            status=resp.status,
            body=_read_body(resp),
            headers={k.lower(): v for k, v in resp.headers.items()},
        )


def get(
    url: str,
    *,
    accept: str | None = None,
    headers: dict | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    cache_ttl: float | None = None,
    use_cache: bool = True,
) -> Response:
    """Fetch a URL with cache, throttling, retries and proxy support.

    On a network failure, a stale cache entry is served rather than raising:
    an answer grounded in last week's search beats no answer at all when the
    network is unavailable, and the staleness is reported on the Response.
    """
    host = urllib.parse.urlparse(url).netloc
    req_headers = {
        "User-Agent": user_agent(),
        "Accept-Encoding": "gzip",
    }
    if accept:
        req_headers["Accept"] = accept
    if headers:
        req_headers.update(headers)

    if use_cache:
        hit = cache_mod.read(url, ttl=cache_ttl)
        if hit is not None:
            return Response(url=url, status=200, body=hit, from_cache=True)

    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            _throttle(host)
            resp = _request_once(url, req_headers, timeout)
            if use_cache:
                cache_mod.write(url, resp.body)
            return resp
        except urllib.error.HTTPError as exc:  # noqa: PERF203 - retry needs the loop
            last_error = exc
            if exc.code not in RETRY_STATUSES or attempt == MAX_ATTEMPTS - 1:
                break
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            delay = BACKOFF_BASE_SECONDS * (2**attempt)
            if retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    pass
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt == MAX_ATTEMPTS - 1:
                break
            time.sleep(BACKOFF_BASE_SECONDS * (2**attempt))

    stale = cache_mod.read(url, ttl=None, allow_stale=True) if use_cache else None
    if stale is not None:
        return Response(url=url, status=200, body=stale, from_cache=True, stale=True)

    status = getattr(last_error, "code", None)
    raise HTTPError(f"GET {url} failed: {last_error}", status=status, url=url)


def build_url(base: str, params: dict) -> str:
    """Join a base URL with query params, dropping empties for stable cache keys."""
    clean = {k: v for k, v in params.items() if v not in (None, "", [])}
    return f"{base}?{urllib.parse.urlencode(clean)}"
