#!/usr/bin/env python3
"""Regenerate lib/taxonomy.py and references/categories.md from arXiv itself.

arXiv adds categories (econ.* and eess.* are recent additions). Rather than
hand-maintaining a list that goes stale — the failure this whole module exists
to fix — regenerate it from the published taxonomy page.

Usage: refresh_taxonomy.py [--check]
  --check  exit 1 if the generated files are out of date, without writing
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import http  # noqa: E402

TAXONOMY_URL = "https://arxiv.org/category_taxonomy"
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)

ARCHIVE_LABEL = {
    "astro-ph": "Astrophysics",
    "cond-mat": "Condensed Matter",
    "cs": "Computer Science",
    "econ": "Economics",
    "eess": "Electrical Engineering and Systems Science",
    "gr-qc": "General Relativity and Quantum Cosmology",
    "hep-ex": "High Energy Physics - Experiment",
    "hep-lat": "High Energy Physics - Lattice",
    "hep-ph": "High Energy Physics - Phenomenology",
    "hep-th": "High Energy Physics - Theory",
    "math": "Mathematics",
    "math-ph": "Mathematical Physics",
    "nlin": "Nonlinear Sciences",
    "nucl-ex": "Nuclear Experiment",
    "nucl-th": "Nuclear Theory",
    "physics": "Physics",
    "q-bio": "Quantitative Biology",
    "q-fin": "Quantitative Finance",
    "quant-ph": "Quantum Physics",
    "stat": "Statistics",
}


def scrape() -> list:
    body = http.get(TAXONOMY_URL, use_cache=False).body
    pairs = re.findall(
        r"<h4>\s*([a-zA-Z\-]+(?:\.[a-zA-Z\-]+)?)\s*<span>\((.*?)\)</span>", body
    )
    return sorted((cid, html.unescape(label).strip()) for cid, label in pairs)


def render_python(pairs: list) -> str:
    archives = sorted({cid.split(".")[0] for cid, _ in pairs})
    lines = [
        '"""Complete arXiv subject taxonomy, generated from https://arxiv.org/category_taxonomy.',
        "",
        "Generated, not hand-written: the hand-curated list this replaces covered 23 of",
        "the 155 real categories, which is how three of five eval problems ended up",
        "guessing an id (quant-ph, q-bio.BM, math.NA) with no way to check the guess.",
        "",
        "Regenerate with: scripts/refresh_taxonomy.py",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "CATEGORIES = {",
    ]
    lines += [f"    {cid!r}: {label!r}," for cid, label in pairs]
    lines += ["}", "", "ARCHIVES = {"]
    lines += [f"    {a!r}: {ARCHIVE_LABEL.get(a, a)!r}," for a in archives]
    lines += [
        "}",
        "",
        '''

def is_valid(category_id: str) -> bool:
    """True when the id is a real arXiv category or a whole archive."""
    cid = (category_id or "").strip()
    return cid in CATEGORIES or cid in ARCHIVES


def suggest(category_id: str, limit: int = 5) -> list:
    """Nearest real category ids, for the error message when a guess is wrong."""
    import difflib

    cid = (category_id or "").strip()
    pool = list(CATEGORIES) + list(ARCHIVES)
    close = difflib.get_close_matches(cid, pool, n=limit, cutoff=0.5)
    if close:
        return close
    archive = cid.split(".")[0]
    return sorted(c for c in CATEGORIES if c.startswith(archive + "."))[:limit]
''',
    ]
    return "\n".join(lines) + "\n"


CURATED_PROMPT_ROWS = [
    ("cs.AI", "general AI systems, agents, planning, knowledge representation"),
    ("cs.LG", "learning algorithms, training methods, model architectures"),
    ("cs.CL", "NLP, language models, text processing"),
    ("cs.CV", "image/video understanding, generation, perception"),
    ("cs.IR", "search, ranking, recommendation, retrieval-augmented systems"),
    ("cs.DC", "distributed systems, consensus, sharding, replication, scheduling"),
    ("cs.DB", "storage engines, query processing, indexing, transactions, consistency"),
    ("cs.SE", "development practices, testing, program analysis, tooling"),
    ("cs.PL", "language design, type systems, compilers, runtimes"),
    ("cs.CR", "protocols, authentication, adversarial robustness, privacy"),
    ("cs.NI", "routing, congestion control, edge/CDN"),
    ("cs.OS", "kernels, schedulers, memory management, virtualization"),
    ("cs.HC", "interface design, usability, interaction models"),
    ("cs.MA", "coordination, negotiation, emergent behavior among agents"),
    ("cs.RO", "control, perception, manipulation, motion planning"),
    ("cs.DS", "algorithmic techniques, complexity, data structure design"),
    ("cs.GT", "mechanism design, auctions, incentive-compatible systems"),
    ("cs.PF", "benchmarking, profiling, systems performance modeling"),
    ("stat.ML", "statistical learning theory, probabilistic models"),
    ("math.NA", "numerical analysis, solvers, discretization, conditioning"),
    ("math.OC", "optimization, scheduling, resource allocation"),
    ("eess.SP", "signal processing, sensor data, filtering, compression"),
    ("eess.SY", "control theory, feedback systems"),
    ("quant-ph", "quantum computing, decoherence, error correction"),
    ("q-bio.BM", "biomolecules, protein/ligand structure and interaction"),
    ("q-fin.CP", "computational finance, pricing, risk modelling"),
    ("econ.EM", "econometrics, causal estimation from observational data"),
]


def render_typescript(pairs: list) -> str:
    """Mirror the taxonomy into the Node package so both frontends agree."""
    lines = [
        "// Generated by skills/dejavu/scripts/refresh_taxonomy.py — do not edit by hand.",
        "//",
        "// The full arXiv taxonomy is here for reference and validation; the prompt only",
        "// shows a curated subset, because 155 rows would crowd out the problem itself.",
        "// The category-select prompt tells the model it may name any real id, and the",
        "// Python fetch layer is the authority: it validates every id against this same",
        "// list and reports a named error with suggestions when one is wrong.",
        "",
        "export type CategoryDef = {",
        "  id: string;",
        "  label: string;",
        "};",
        "",
        "export const CATEGORIES: CategoryDef[] = [",
    ]
    for cid, label in pairs:
        safe = label.replace('"', '\\"')
        lines.append(f'  {{ id: "{cid}", label: "{safe}" }},')
    lines += [
        "];",
        "",
        "export const CATEGORY_IDS = new Set(CATEGORIES.map((c) => c.id));",
        "",
        "// The subset shown to the category-select pass, with a builder-facing gloss.",
        "const PROMPT_ROWS: [string, string][] = [",
    ]
    known = {cid for cid, _ in pairs}
    for cid, gloss in CURATED_PROMPT_ROWS:
        if cid not in known:
            continue
        lines.append(f'  ["{cid}", "{gloss}"],')
    lines += [
        "];",
        "",
        "export function renderCategoryTable(): string {",
        "  return PROMPT_ROWS.map(([id, covers]) => `| ${id} | ${covers} |`).join(\"\\n\");",
        "}",
        "",
        "// Shape check only. Authoritative validation lives in the Python fetch layer,",
        "// which knows the whole taxonomy and can suggest the id the model meant; a",
        "// second, stricter gate here would swallow that message.",
        "export function looksLikeCategoryId(id: string): boolean {",
        "  return /^[a-z-]+(\\.[A-Za-z]{2,3})?$/.test(id.trim());",
        "}",
        "",
    ]
    return "\n".join(lines)


def render_markdown(pairs: list) -> str:
    groups: dict = {}
    for cid, label in pairs:
        groups.setdefault(cid.split(".")[0], []).append((cid, label))

    out = [
        "# arXiv category reference",
        "",
        f"All {len(pairs)} categories in arXiv's subject taxonomy, generated from",
        "<https://arxiv.org/category_taxonomy>. Pick 3-5 whose subject matter plausibly",
        "contains prior art for the problem. Ids are validated before any query is sent,",
        'so a wrong guess produces a named error and a suggestion, never an empty result',
        'set that looks like "no prior art exists".',
        "",
        "## Contents",
        "",
    ]
    for archive in sorted(groups):
        label = ARCHIVE_LABEL.get(archive, archive)
        out.append(f"- {label} (`{archive}`)")
    out.append("")
    for archive in sorted(groups):
        label = ARCHIVE_LABEL.get(archive, archive)
        out += [f"## {label} (`{archive}`)", "", "| Category | Covers |", "|---|---|"]
        out += [f"| `{cid}` | {lbl} |" for cid, lbl in sorted(groups[archive])]
        out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="refresh_taxonomy.py")
    parser.add_argument("--check", action="store_true", help="Report drift without writing")
    args = parser.parse_args(argv)

    pairs = scrape()
    if len(pairs) < 100:
        print(f"Refusing to write: only {len(pairs)} categories scraped, page shape changed?")
        return 1

    repo_root = os.path.dirname(os.path.dirname(SKILL_ROOT))
    targets = {
        os.path.join(HERE, "lib", "taxonomy.py"): render_python(pairs),
        os.path.join(SKILL_ROOT, "references", "categories.md"): render_markdown(pairs),
        os.path.join(repo_root, "src", "categories.ts"): render_typescript(pairs),
    }

    drifted = []
    for path, content in targets.items():
        current = open(path).read() if os.path.exists(path) else None
        if current != content:
            drifted.append(path)
        if not args.check:
            with open(path, "w") as handle:
                handle.write(content)

    if args.check:
        for path in drifted:
            print(f"out of date: {path}")
        print(f"{len(pairs)} categories scraped; {len(drifted)} file(s) out of date")
        return 1 if drifted else 0

    print(f"Wrote {len(targets)} file(s) from {len(pairs)} categories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
