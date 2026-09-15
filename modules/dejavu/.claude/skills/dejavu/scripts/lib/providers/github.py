"""GitHub repository search provider.

The papers layer answers "has anyone published this"; this one answers "has
anyone shipped this", which is often the better answer — a maintained
repository is prior art you can read, run and depend on. That makes this the
source that feeds the practicality score rather than the novelty score.

No key required. `GITHUB_TOKEN`, if the environment happens to carry one, only
buys a higher rate limit.

API docs: https://docs.github.com/rest/search/search#search-repositories
"""

from __future__ import annotations

import os

from .. import cache, http
from ..document import UNKNOWN, Document
from .base import Provider, ProviderResult, Query

API = "https://api.github.com/search/repositories"

# Unauthenticated search is capped at 10 requests/minute (observed
# `x-ratelimit-limit: 10`, `x-ratelimit-resource: search`), and lib/http.py
# spaces api.github.com calls 6s apart to respect it — so every extra request
# costs six seconds of the run. `search` therefore issues exactly one, with
# the terms joined into a single query, rather than looping one query per
# term. This constant states what the code does; it is not a guard, because
# there is only one call site to guard.
REQUESTS_PER_RUN = 1


def auth_headers() -> dict:
    """Authorization header when a token is around, nothing when it isn't.

    The token is only ever passed to urllib — never logged, never echoed into
    a note or a query string.
    """
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


def parse_repositories(payload: dict):
    """Parse a /search/repositories response into (documents, total_count)."""
    total = payload.get("total_count")

    documents = []
    for repo in payload.get("items") or []:
        full_name = repo.get("full_name")
        if not full_name:
            continue

        pushed_at = repo.get("pushed_at") or ""

        documents.append(
            Document(
                id=f"github:{full_name}",
                title=full_name,
                abstract=repo.get("description") or "",
                venue="GitHub",
                date=pushed_at[:10] or None,
                # Stars are this source's citation analogue: the count of people
                # who found the work worth marking, which is what `citations`
                # means everywhere else in the corpus.
                citations=repo.get("stargazers_count"),
                urls={"landing": repo.get("html_url")},
                source="github",
                # Retraction has no meaning for a repository, and claiming
                # "clear" would imply a check nobody performed.
                retraction_status=UNKNOWN,
                has_code=True,
                extra={
                    # An archived repo is a real signal, not a reason to drop
                    # the hit: the idea shipped and then stopped being
                    # maintained, which the practicality score should see.
                    "archived": bool(repo.get("archived")),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count"),
                    "last_push": pushed_at or None,
                },
            )
        )

    return documents, total


class GitHubProvider(Provider):
    name = "github"

    def search(self, query: Query) -> ProviderResult:
        result = ProviderResult(provider=self.name)

        phrase = query.phrase()
        result.queries.append(phrase)
        url = http.build_url(API, {"q": phrase, "per_page": query.limit})

        try:
            response = http.get(
                url,
                accept="application/vnd.github+json",
                headers=auth_headers(),
                cache_ttl=cache.TTL_CODE,
                use_cache=query.use_cache,
            )
        except http.HTTPError as exc:
            result.notes.append(f"GitHub request failed for '{phrase}': {exc}")
            result.failed = True
            return result

        if response.stale:
            result.notes.append(
                f"Served a cached (stale) GitHub response for '{phrase}' — network unavailable."
            )

        try:
            documents, total = parse_repositories(response.json())
        except ValueError as exc:
            result.notes.append(f"GitHub returned unparseable JSON for '{phrase}': {exc}")
            result.failed = True
            return result

        result.total_available = total
        if total == 0:
            result.notes.append(
                f"GitHub reported total_count=0 for '{phrase}'. Nobody has shipped this "
                "under these terms — that is a finding about practicality, not a failure."
            )

        result.documents.extend(documents)
        self.apply_recency_filter(result, query.since_years)

        if result.documents and result.documents[0].extra.get("archived"):
            result.notes.append(
                f"The top GitHub hit ({result.documents[0].title}) is archived — the work "
                "exists but is unmaintained, so it is prior art rather than a live option."
            )

        return result
