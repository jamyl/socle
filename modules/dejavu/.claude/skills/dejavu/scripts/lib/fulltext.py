"""Second-tier reading: the paper itself, not just its abstract.

Every document the skill has read so far is abstract-only, which is enough to
cluster and rank but not enough to say *how* a method works or where it breaks.
This module escalates a handful of papers — in practice the top 3 of the winning
cluster — to their actual text, and only those, which is why every part of it is
bounded: one cascade, first hit wins, hard character budget.

The cascade, stopping at the first tier that yields usable text:
  1. https://arxiv.org/html/<id>            — arXiv's own LaTeXML rendering
  2. https://ar5iv.labs.arxiv.org/html/<id> — the same idea with older coverage
  3. Europe PMC open access                 — for the life-sciences half of the
     corpus, where there is no arXiv id but there is a DOI

Standard library only, like the rest of this directory. Note that the Europe PMC
full text is JATS XML carrying a `<!DOCTYPE>`, which `safe_xml` refuses outright
(entity-expansion and XXE risk) — so it goes through the same HTMLParser used for
the HTML tiers, which never processes a DTD, rather than through ElementTree.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

from . import cache, http
from .document import normalize_arxiv_id, normalize_doi

ARXIV_HTML = "https://arxiv.org/html/{id}"
AR5IV_HTML = "https://ar5iv.labs.arxiv.org/html/{id}"
EPMC_REST = "https://www.ebi.ac.uk/europepmc/webservices/rest"

TIER_ARXIV = "arxiv-html"
TIER_AR5IV = "ar5iv"
TIER_EPMC = "europepmc-oa"
TIER_UNAVAILABLE = "unavailable"

# Roughly 10k tokens: what a single isolated read can absorb without crowding
# out the rest of the run (the other reads, the clustering, the convergence).
# A full paper is commonly 2-5x this, so the budget usually bites — which is the
# point, the alternative is one paper eating the whole context.
MAX_CHARS = 40_000

# Below this a tier "worked" but gave us nothing worth reading — an arXiv HTML
# stub, a landing page, a paywall notice — so the cascade continues.
MIN_USEFUL_CHARS = 500

_ELLIPSIS = " […]"

# 2311.02384 (post-2007) or hep-th/9901001 (the old scheme, already lowercased
# and version-stripped by normalize_arxiv_id).
_ARXIV_ID_RE = re.compile(r"^(\d{4}\.\d{4,5}|[a-z-]+(\.[a-z]{2})?/\d{7})$")

# Headings whose content carries mechanism and failure modes. Everything else —
# related work, acknowledgements, references, author contributions — is real
# text that we simply did not escalate a paper to read.
_SECTION_KEYWORDS = (
    "method",
    "approach",
    "algorithm",
    "implementation",
    "evaluation",
    "experiment",
    "result",
    "limitation",
    "discussion",
    "conclusion",
    "threats to validity",
)

# Tags whose text is chrome, never content. `title` is the one in <head>: the
# body repeats it as an <h1>, and left in it becomes an untitled first section.
_HTML_SKIP_TAGS = frozenset(
    {"script", "style", "nav", "footer", "header", "form", "select", "title"}
)
# LaTeXML wraps the reference list in this class on both arXiv and ar5iv. It is
# structural noise like a <nav>, and left in it would claim a third of the budget.
_HTML_SKIP_CLASSES = ("ltx_bibliography",)
_HTML_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})

# JATS: <front> is journal metadata plus the abstract we already have, <back> is
# references and funding statements. Sections are <sec><title>...</title>, and
# figures and tables carry a <caption><title> too — left in, every caption
# becomes a bogus section and every table dumps its cells into the budget.
_JATS_SKIP_TAGS = frozenset({"front", "back", "ref-list", "fig", "table-wrap"})
_JATS_HEADING_TAGS = frozenset({"title"})

# Boundaries between blocks become a space, so a heading does not glue itself to
# the first word of its paragraph while inline markup stays inside its word.
_BLOCK_TAGS = frozenset(
    {"p", "div", "section", "li", "br", "td", "tr", "table", "sec", "title", "abstract"}
    | _HTML_HEADING_TAGS
)


@dataclass
class FullText:
    source_url: str = ""
    tier: str = TIER_UNAVAILABLE
    sections: list = field(default_factory=list)  # [{"heading": str, "text": str}]
    truncated: bool = False
    notes: list = field(default_factory=list)

    @property
    def chars(self) -> int:
        return sum(len(s["text"]) for s in self.sections)


class _SectionExtractor(HTMLParser):
    """Markup to (heading, text) pairs. Deliberately not a readability engine.

    Two rules only: drop the tags that never carry content, and start a new
    section at every heading. Anything before the first heading is kept as an
    untitled section so a document with no headings still returns its text.
    """

    def __init__(self, *, heading_tags, skip_tags, skip_classes=()):
        super().__init__(convert_charrefs=True)
        self._heading_tags = heading_tags
        self._skip_tags = skip_tags
        self._skip_classes = skip_classes
        self._skip_stack: list = []
        self._in_heading = False
        self._heading_parts: list = []
        self._sections: list = [{"heading": "", "parts": []}]

    def _skipping(self) -> bool:
        return bool(self._skip_stack)

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "") or ""
        if tag in self._skip_tags or any(c in classes for c in self._skip_classes):
            self._skip_stack.append(tag)
            return
        if self._skipping():
            return
        if tag in self._heading_tags:
            self._in_heading = True
            self._heading_parts = []
            self._sections.append({"heading": "", "parts": []})
        elif tag in _BLOCK_TAGS:
            self._sections[-1]["parts"].append(" ")

    def handle_endtag(self, tag):
        if self._skip_stack:
            # Match on the tag name rather than depth: malformed markup that
            # never closes a <nav> would otherwise swallow the whole document.
            if self._skip_stack[-1] == tag:
                self._skip_stack.pop()
            return
        if tag in self._heading_tags and self._in_heading:
            self._sections[-1]["heading"] = _collapse("".join(self._heading_parts))
            self._in_heading = False
        elif tag in _BLOCK_TAGS:
            self._sections[-1]["parts"].append(" ")

    def handle_data(self, data):
        if self._skipping():
            return
        if self._in_heading:
            self._heading_parts.append(data)
        else:
            self._sections[-1]["parts"].append(data)

    def sections(self) -> list:
        out = []
        for section in self._sections:
            text = _collapse("".join(section["parts"]))
            if not text and not section["heading"]:
                continue
            out.append({"heading": section["heading"], "text": text})
        return out


def _collapse(text: str) -> str:
    return " ".join(text.split())


def extract_sections(markup: str, *, jats: bool = False) -> list:
    """Split HTML (or Europe PMC JATS) into [{"heading", "text"}]."""
    parser = _SectionExtractor(
        heading_tags=_JATS_HEADING_TAGS if jats else _HTML_HEADING_TAGS,
        skip_tags=_JATS_SKIP_TAGS if jats else _HTML_SKIP_TAGS,
        skip_classes=() if jats else _HTML_SKIP_CLASSES,
    )
    parser.feed(markup)
    parser.close()
    return parser.sections()


def apply_budget(sections: list, max_chars: int = MAX_CHARS):
    """Cut every section by the same proportion, returning (sections, truncated).

    Proportional rather than a cut at the tail: taking the first 40k characters
    of a paper would keep three copies of the introduction and lose the
    Conclusion and Limitations of every long one, which are the sections the
    escalation exists to read.
    """
    total = sum(len(s["text"]) for s in sections)
    if total <= max_chars or total == 0:
        return sections, False

    ratio = max_chars / total
    out = []
    for section in sections:
        share = int(len(section["text"]) * ratio)
        keep = max(0, share - len(_ELLIPSIS))
        clipped = section["text"][:keep].rsplit(" ", 1)[0] if keep else ""
        out.append({"heading": section["heading"], "text": clipped + _ELLIPSIS if clipped else ""})
    return out, True


def select_sections(full_text: FullText, keywords=None) -> list:
    """The sections most likely to carry method and limitation content.

    Falls back to everything when no heading matches: a paper with unhelpful
    headings ("3.2", "Our system") should still be readable rather than empty.
    """
    terms = tuple(keywords) if keywords else _SECTION_KEYWORDS
    hits = [s for s in full_text.sections if any(t in s["heading"].lower() for t in terms)]
    return hits or list(full_text.sections)


def _try_markup(url: str, tier: str, *, jats: bool, use_cache: bool, max_chars: int, notes: list):
    """Fetch one tier and return a FullText, or None so the cascade continues."""
    try:
        response = http.get(
            url,
            accept="application/xml" if jats else "text/html",
            cache_ttl=cache.TTL_FULLTEXT,
            use_cache=use_cache,
        )
    except http.HTTPError as exc:
        notes.append(f"{tier} has no full text for this document ({exc}).")
        return None

    sections = extract_sections(response.body, jats=jats)
    if sum(len(s["text"]) for s in sections) < MIN_USEFUL_CHARS:
        notes.append(f"{tier} answered but carried no readable body text; trying the next tier.")
        return None

    if response.stale:
        notes.append(f"Served a cached (stale) {tier} response — network unavailable.")

    sections, truncated = apply_budget(sections, max_chars)
    if truncated:
        notes.append(
            f"Full text exceeded the {max_chars}-character budget; every section was "
            "cut proportionally rather than dropping the end of the paper."
        )
    return FullText(
        source_url=url, tier=tier, sections=sections, truncated=truncated, notes=notes
    )


def _epmc_pmcid(doi: str, *, use_cache: bool, notes: list):
    """Resolve a DOI to an open-access PMCID, or None with a note saying why."""
    url = http.build_url(
        f"{EPMC_REST}/search",
        {"query": f'DOI:"{doi}"', "format": "json", "pageSize": 1, "resultType": "core"},
    )
    try:
        response = http.get(url, accept="application/json", cache_ttl=cache.TTL_FULLTEXT,
                            use_cache=use_cache)
        results = response.json().get("resultList", {}).get("result", [])
    except (http.HTTPError, json.JSONDecodeError, AttributeError) as exc:
        notes.append(f"Europe PMC lookup failed for DOI {doi} ({exc}).")
        return None

    if not results:
        notes.append(f"Europe PMC has no record for DOI {doi}.")
        return None
    record = results[0]
    pmcid = record.get("pmcid")
    if not pmcid or record.get("isOpenAccess") != "Y":
        notes.append(
            f"Europe PMC knows DOI {doi} but it is not in the open-access subset, "
            "so the full text cannot be fetched."
        )
        return None
    return pmcid


def fetch(arxiv_id_or_url, *, doi=None, use_cache=True, max_chars: int = MAX_CHARS) -> FullText:
    """Run the cascade and return the first tier that supplies usable text.

    Returning tier="unavailable" is a legitimate outcome, not an error: it means
    this document stays abstract-only, and the notes say which tiers were tried.
    """
    notes: list = []

    arxiv_id = normalize_arxiv_id(arxiv_id_or_url)
    if arxiv_id and _ARXIV_ID_RE.match(arxiv_id):
        for tier, template in ((TIER_ARXIV, ARXIV_HTML), (TIER_AR5IV, AR5IV_HTML)):
            found = _try_markup(
                template.format(id=arxiv_id),
                tier,
                jats=False,
                use_cache=use_cache,
                max_chars=max_chars,
                notes=notes,
            )
            if found is not None:
                return found
    elif arxiv_id:
        notes.append(f"'{arxiv_id}' is not an arXiv id; skipped the two arXiv HTML tiers.")

    doi = normalize_doi(doi)
    if doi:
        pmcid = _epmc_pmcid(doi, use_cache=use_cache, notes=notes)
        if pmcid:
            found = _try_markup(
                f"{EPMC_REST}/{pmcid}/fullTextXML",
                TIER_EPMC,
                jats=True,
                use_cache=use_cache,
                max_chars=max_chars,
                notes=notes,
            )
            if found is not None:
                return found
    else:
        notes.append("No DOI given, so the Europe PMC open-access tier was not tried.")

    notes.append("No tier could supply full text; this document stays abstract-only.")
    return FullText(tier=TIER_UNAVAILABLE, notes=notes)
