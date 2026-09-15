#!/usr/bin/env python3
"""Search prior art across providers and emit normalized Document JSON.

This is the deterministic half of the skill. It does the fetching, parsing,
deduplication and diagnostics; the model does the reading, scoring, clustering
and convergence. Nothing here calls an LLM, and nothing here summarizes — the
output is the API's own data, normalized.

Usage:
  search.py --terms "cache invalidation" "consistency" --categories cs.DB cs.DC
  search.py --terms "leader election" --sources arxiv,openalex --limit 6
  search.py --terms "kv cache compression" --brief --json

Exit codes: 0 on success (even with zero results — that is a finding), 2 when
every requested provider failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import cache as cache_mod  # noqa: E402
from lib.document import dedup  # noqa: E402
from lib.providers.base import Query, registry  # noqa: E402

DEFAULT_SOURCES = "arxiv,openalex"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="search.py",
        description="Search prior art across providers, return normalized Documents.",
    )
    parser.add_argument(
        "--terms",
        nargs="+",
        required=True,
        help="Technical mechanism terms, e.g. 'cache invalidation' 'leader election'",
    )
    parser.add_argument(
        "--categories",
        nargs="*",
        default=[],
        help="arXiv category ids (validated against the real taxonomy)",
    )
    parser.add_argument(
        "--sources",
        default=DEFAULT_SOURCES,
        help=f"Comma-separated providers (default: {DEFAULT_SOURCES}). "
        f"Available: {','.join(sorted(registry()))}",
    )
    parser.add_argument("--limit", type=int, default=6, help="Documents per provider query")
    parser.add_argument(
        "--since-years", type=int, default=0, help="Drop documents older than N years (0 = all)"
    )
    parser.add_argument("--no-cache", action="store_true", help="Bypass the on-disk cache")
    parser.add_argument(
        "--brief", action="store_true", help="Omit abstracts (triage listing, smaller output)"
    )
    parser.add_argument("--cache-stats", action="store_true", help="Report cache size and exit")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if args.cache_stats:
        print(json.dumps(cache_mod.stats(), indent=2))
        return 0

    available = registry()
    requested = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in requested if s not in available]
    selected = [s for s in requested if s in available]

    query = Query(
        terms=args.terms,
        categories=args.categories,
        limit=args.limit,
        since_years=args.since_years,
        use_cache=not args.no_cache,
    )

    notes = [f"'{s}' is not a known provider; skipped." for s in unknown]
    if not selected:
        notes.append(f"No usable provider requested. Available: {', '.join(sorted(available))}.")

    provider_results = []
    documents = []
    for name in selected:
        result = available[name]().search(query)
        provider_results.append(result)
        documents.extend(result.documents)

    merged = dedup(documents)

    payload = {
        "query": {
            "terms": args.terms,
            "categories": args.categories,
            "sources": selected,
            "limit": args.limit,
            "since_years": args.since_years,
            "cache": "bypassed" if args.no_cache else "enabled",
        },
        "counts": {
            "returned_by_providers": len(documents),
            "after_dedup": len(merged),
            "with_citations": sum(1 for d in merged if d.citations is not None),
            "retracted_or_corrected": sum(
                1 for d in merged if d.retraction_status in ("retracted", "has-correction")
            ),
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
        "documents": [
            {k: v for k, v in d.to_dict().items() if not (args.brief and k == "abstract")}
            for d in merged
        ],
    }

    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    if payload["diagnostics"]["all_providers_failed"] or not selected:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
