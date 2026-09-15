#!/usr/bin/env python3
"""Search shipped code and trending papers, and emit normalized Document JSON.

The sibling of search.py, aimed at a different question. search.py answers "has
anyone published this"; this answers "has anyone shipped this" — a maintained
repository, or a preprint the community is upvoting with code attached. Those
feed the practicality read, not the novelty read.

Usage:
  codesearch.py --terms "cache invalidation"
  codesearch.py --terms "leader election" --limit 5 --sources github
  codesearch.py --terms "kv cache compression" --sources github,hfpapers --no-cache

Exit codes: 0 on success (even with zero results — that is a finding), 2 when
every requested provider failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.document import dedup  # noqa: E402
from lib.providers.base import Query  # noqa: E402
from lib.providers.github import GitHubProvider  # noqa: E402
from lib.providers.hf import HuggingFacePapersProvider  # noqa: E402

# Kept local rather than in providers/base.registry(): these are the code-tier
# providers, and search.py's `--sources` should not offer them by accident.
PROVIDERS = {
    GitHubProvider.name: GitHubProvider,
    HuggingFacePapersProvider.name: HuggingFacePapersProvider,
}
DEFAULT_SOURCES = "github,hfpapers"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="codesearch.py",
        description="Search code prior art (GitHub, Hugging Face daily papers).",
    )
    parser.add_argument(
        "--terms",
        nargs="+",
        required=True,
        help="Technical mechanism terms, e.g. 'cache invalidation' 'leader election'",
    )
    parser.add_argument(
        "--sources",
        default=DEFAULT_SOURCES,
        help=f"Comma-separated providers (default: {DEFAULT_SOURCES}). "
        f"Available: {','.join(sorted(PROVIDERS))}",
    )
    parser.add_argument("--limit", type=int, default=5, help="Documents per provider query")
    parser.add_argument("--no-cache", action="store_true", help="Bypass the on-disk cache")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    requested = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in requested if s not in PROVIDERS]
    selected = [s for s in requested if s in PROVIDERS]

    query = Query(terms=args.terms, limit=args.limit, use_cache=not args.no_cache)

    notes = [f"'{s}' is not a known code provider; skipped." for s in unknown]
    if not selected:
        notes.append(f"No usable provider requested. Available: {', '.join(sorted(PROVIDERS))}.")

    provider_results = []
    documents = []
    for name in selected:
        result = PROVIDERS[name]().search(query)
        provider_results.append(result)
        documents.extend(result.documents)

    merged = dedup(documents)

    payload = {
        "query": {
            "terms": args.terms,
            "sources": selected,
            "limit": args.limit,
            "cache": "bypassed" if args.no_cache else "enabled",
        },
        "counts": {
            "returned_by_providers": len(documents),
            "after_dedup": len(merged),
            "with_code": sum(1 for d in merged if d.has_code),
            "archived": sum(1 for d in merged if d.extra.get("archived")),
        },
        "diagnostics": {
            "notes": notes + [n for r in provider_results for n in r.notes],
            "providers": [
                {
                    "provider": r.provider,
                    "documents": len(r.documents),
                    "total_available": r.total_available,
                    "failed": r.failed,
                    "queries": r.queries,
                }
                for r in provider_results
            ],
            "all_providers_failed": bool(provider_results)
            and all(r.failed for r in provider_results),
        },
        "documents": [d.to_dict() for d in merged],
    }

    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    if payload["diagnostics"]["all_providers_failed"] or not selected:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
