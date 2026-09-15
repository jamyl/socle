#!/usr/bin/env python3
"""Search SEC EDGAR filings and emit normalized Document JSON.

The finance-side twin of `search.py`, and deliberately the same shape: same
envelope, same diagnostics, same exit codes, so everything downstream (scoring,
clustering, convergence) is unchanged. Only the source is different.

Research grounding from public filings — not investment advice.

Usage:
  filings.py --query "supply chain disruption" --forms 10-K --limit 5
  filings.py --query "material weakness" --cik 0000320193 --sections
  filings.py --query "goodwill impairment" --forms 10-K 10-Q --no-cache

Requires DEJAVU_CONTACT: the SEC mandates a User-Agent naming a contact
(https://www.sec.gov/os/accessing-edgar-data).

Exit codes: 0 on success (zero results included — that is a finding), 2 when
the search failed outright.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.providers.base import Query  # noqa: E402
from lib.providers.edgar import (  # noqa: E402
    ContactRequiredError,
    EdgarProvider,
    fetch_sections,
    require_contact,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="filings.py",
        description="Search SEC EDGAR full text, return normalized Documents.",
    )
    parser.add_argument(
        "--query", required=True, help='Phrase to search, e.g. "supply chain disruption"'
    )
    parser.add_argument("--forms", nargs="*", default=[], help="Form types, e.g. 10-K 10-Q 8-K")
    parser.add_argument("--cik", nargs="*", default=[], help="Restrict to these CIKs")
    parser.add_argument("--limit", type=int, default=5, help="Filings to return")
    parser.add_argument("--since-years", type=int, default=0, help="Drop filings older than N years")
    parser.add_argument(
        "--sections",
        action="store_true",
        help="Fetch each filing and split it into Item sections (the isolated-read unit)",
    )
    parser.add_argument("--no-cache", action="store_true", help="Bypass the on-disk cache")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        require_contact()
    except ContactRequiredError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    provider = EdgarProvider(forms=args.forms, ciks=args.cik)
    query = Query(terms=[args.query], limit=args.limit, since_years=args.since_years,
                  use_cache=not args.no_cache)

    result = provider.search(query)
    notes = list(result.notes)

    sections_by_id = {}
    if args.sections:
        for doc in result.documents:
            extra = doc.extra
            try:
                sections, why = fetch_sections(
                    extra["accession"],
                    extra["cik"],
                    extra.get("primary_document"),
                    use_cache=not args.no_cache,
                )
            except ContactRequiredError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            except Exception as exc:  # noqa: BLE001 - one bad filing must not sink the run
                notes.append(f"{extra['accession']}: section extraction failed: {exc}")
                continue
            notes.extend(why)
            # PLAN.md §6: one Document is a filing section, so each section
            # carries the id the reader and the convergence step will cite.
            sections_by_id[doc.id] = [
                {"id": f"{extra['accession']}#{s['heading']}", **s} for s in sections
            ]

    payload = {
        "query": {
            "query": args.query,
            "forms": args.forms,
            "ciks": args.cik,
            "limit": args.limit,
            "since_years": args.since_years,
            "sections": args.sections,
            "cache": "bypassed" if args.no_cache else "enabled",
        },
        "counts": {
            "returned": len(result.documents),
            "total_available": result.total_available,
            "amended": sum(1 for d in result.documents if d.retraction_status == "has-correction"),
            "sections_extracted": sum(len(v) for v in sections_by_id.values()),
        },
        "diagnostics": {
            "notes": notes,
            "providers": [
                {
                    "provider": result.provider,
                    "documents": len(result.documents),
                    "total_available": result.total_available,
                    "failed": result.failed,
                    "queries": result.queries,
                }
            ],
            "all_providers_failed": result.failed,
            "disclaimer": "Research grounding from public filings — not investment advice.",
        },
        "documents": [
            {
                **doc.to_dict(),
                **({"sections": sections_by_id[doc.id]} if doc.id in sections_by_id else {}),
            }
            for doc in result.documents
        ],
    }

    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 2 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
