#!/usr/bin/env python3
"""Escalate one document from its abstract to its actual full text.

The second reading tier, and the expensive one: it is meant for the top few
papers of the winning cluster, never for a whole result set. It fetches, extracts
and bounds the text; the model does the reading.

Usage:
  fulltext.py --id 2311.02384
  fulltext.py --id 2311.02384 --sections-only
  fulltext.py --id 10.1371/journal.pone.0119705 --doi 10.1371/journal.pone.0119705

Exit codes: 0 on success, 2 when no tier could supply text — a legitimate
outcome meaning the document stays abstract-only, not a crash.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.fulltext import MAX_CHARS, TIER_UNAVAILABLE, fetch, select_sections  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="fulltext.py",
        description="Fetch and extract the full text of one document.",
    )
    parser.add_argument("--id", required=True, help="arXiv id or URL, e.g. 2311.02384")
    parser.add_argument("--doi", default=None, help="DOI, used for the Europe PMC open-access tier")
    parser.add_argument("--no-cache", action="store_true", help="Bypass the on-disk cache")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=MAX_CHARS,
        help=f"Total extracted characters to keep (default: {MAX_CHARS})",
    )
    parser.add_argument(
        "--sections-only",
        action="store_true",
        help="Keep only method / evaluation / limitation sections",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    result = fetch(
        args.id,
        doi=args.doi,
        use_cache=not args.no_cache,
        max_chars=args.max_chars,
    )

    sections = select_sections(result) if args.sections_only else result.sections

    payload = {
        "id": args.id,
        "tier": result.tier,
        "source_url": result.source_url,
        "truncated": result.truncated,
        "notes": result.notes,
        "sections": sections,
    }

    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    return 2 if result.tier == TIER_UNAVAILABLE else 0


if __name__ == "__main__":
    raise SystemExit(main())
