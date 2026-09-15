"""Crossref REST API provider, and the retraction check used by the whole run.

Crossref is the registry the publishers themselves deposit into, which makes it
the venue/citation/DOI source here — not an abstract source: `abstract` is
absent from most items and JATS-XML-wrapped when present.

It is also the only source that answers "was this retracted?" for an arbitrary
DOI, so `check_retractions` lives here as a module-level function and is called
on documents from *every* provider, not just this one.

API docs: https://api.crossref.org/swagger-ui/index.html
"""

from __future__ import annotations

import html
import re

from .. import cache, http
from ..document import CLEAR, HAS_CORRECTION, RETRACTED, UNKNOWN, Document, normalize_doi
from .base import Provider, ProviderResult, Query

API = "https://api.crossref.org/works"

# `update-to[].type` vocabularies. Anything that removes the work outranks
# anything that patches it, and the caller only ever sees the worst finding.
RETRACTION_TYPES = {"retraction", "withdrawal", "removal"}
CORRECTION_TYPES = {"erratum", "correction", "corrigendum"}

# One request per this many DOIs: repeated `updates:` filters are OR'd by
# Crossref (confirmed live), so a whole page of documents costs a couple of
# calls instead of one per DOI.
RETRACTION_BATCH_SIZE = 20
# Notices per batch. A batch retraction notice can name ~70 DOIs in one item,
# but items-per-batch stays far under this; see the truncation guard below.
RETRACTION_ROWS = 200

_TAG = re.compile(r"<[^>]+>")


def strip_jats(text: str | None) -> str:
    """Flatten Crossref's JATS-XML abstract into plain text.

    Abstracts arrive as `<jats:p>...</jats:p>` when they arrive at all, and the
    reading tier wants prose, not markup.
    """
    if not text:
        return ""
    return " ".join(html.unescape(_TAG.sub(" ", text)).split())


def iso_date(issued: dict | None) -> str | None:
    """Turn Crossref's `issued.date-parts` into a YYYY-MM-DD string.

    Precision varies per record — `[[2020]]`, `[[2020, 3]]` and
    `[[2020, 3, 1]]` are all real, and `[[None]]` is what an undated record
    looks like. Missing month and day are padded to 01 so `Document.date`
    stays sortable; only the year is ever load-bearing downstream.
    """
    parts = (issued or {}).get("date-parts") or []
    first = parts[0] if parts and isinstance(parts[0], list) else []
    values = [p for p in first if isinstance(p, int)]
    if not values:
        return None
    year = values[0]
    month = values[1] if len(values) > 1 else 1
    day = values[2] if len(values) > 2 else 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def status_from_updates(entries: list, doi: str | None = None) -> str | None:
    """Read `update-to` entries into a retraction status, or None if silent.

    None means "this record says nothing about that DOI", which the callers
    resolve differently: a `filter=updates:` lookup that came back silent is a
    CLEAR bill of health, while a work record that simply doesn't carry a
    notice proves nothing and stays UNKNOWN.

    `doi` filters the entries, because one notice item can update dozens of
    unrelated works and only the entry naming our DOI describes our document.
    """
    types = set()
    for entry in entries or []:
        if doi and normalize_doi((entry or {}).get("DOI")) != doi:
            continue
        kind = ((entry or {}).get("type") or "").strip().lower()
        if kind:
            types.add(kind)

    if types & RETRACTION_TYPES:
        return RETRACTED
    if types & CORRECTION_TYPES:
        return HAS_CORRECTION
    return None


def _author_name(author: dict) -> str:
    """Crossref names are split into given/family, except for organisations."""
    parts = [(author.get("given") or "").strip(), (author.get("family") or "").strip()]
    return " ".join(p for p in parts if p) or (author.get("name") or "").strip()


def _first(values, default=None):
    return values[0] if values else default


def parse_item(item: dict) -> Document | None:
    """Map one Crossref work onto the Document contract.

    Returns None for a record with no DOI: the DOI is this provider's only
    stable id, and an id-less document can neither be deduped nor rechecked.
    """
    doi = normalize_doi(item.get("DOI"))
    if not doi:
        return None

    # A work record only carries `update-to` when its publisher deposited the
    # notice against it; its absence is silence, not a clean bill of health.
    status = status_from_updates(item.get("update-to"), doi) or UNKNOWN

    return Document(
        id=f"crossref:{doi}",
        title=_first(item.get("title") or [], "") or "",
        abstract=strip_jats(item.get("abstract")),
        venue=_first(item.get("container-title") or []),
        date=iso_date(item.get("issued")),
        citations=item.get("is-referenced-by-count"),
        urls={"landing": item["URL"]} if item.get("URL") else {},
        source="crossref",
        retraction_status=status,
        authors=[n for n in (_author_name(a) for a in item.get("author") or []) if n],
        doi=doi,
        extra={
            "publisher": item.get("publisher"),
            "type": item.get("type"),
            "reference-count": item.get("reference-count"),
        },
    )


def parse_search(payload: dict):
    """Parse a /works response into (documents, total_results).

    `total-results` is what separates "the query matched nothing" from "the
    query was malformed", so it is read even when items are present.
    """
    message = (payload or {}).get("message") or {}
    total = message.get("total-results")
    documents = [d for d in (parse_item(i) for i in message.get("items") or []) if d]
    return documents, total if isinstance(total, int) else None


def batch_statuses(message: dict, batch: list) -> dict:
    """Read one `filter=updates:` page into statuses for the DOIs it answers for.

    A DOI is only reported CLEAR when this page proves it: the same DOI can
    appear in several notices (a retraction and a later erratum, say) and the
    worst finding wins. DOIs left out of the returned dict stay UNKNOWN for
    the caller.
    """
    items = message.get("items") or []
    found = {}
    for item in items:
        entries = item.get("update-to") or []
        for doi in batch:
            status = status_from_updates(entries, doi)
            if status and found.get(doi) != RETRACTED:
                found[doi] = status

    # If Crossref held more notices than it returned, a DOI we saw nothing for
    # may still be flagged on a page we never read — that is not a clean bill.
    if (message.get("total-results") or 0) > len(items):
        return found
    return {doi: found.get(doi, CLEAR) for doi in batch}


def check_retractions(dois: list) -> dict:
    """Map each DOI to a retraction status, using Crossref's update notices.

    Deliberately independent of the provider class: the search pipeline calls
    this on documents from arXiv, OpenAlex and Europe PMC too. Cached with
    TTL_DOCUMENT because a retraction notice never un-publishes.

    A DOI whose lookup failed stays UNKNOWN. Returning CLEAR there would turn
    a network error into a clean bill of health, which is the exact failure
    this project exists to prevent.
    """
    wanted = sorted({d for d in (normalize_doi(x) for x in dois) if d})
    statuses = {doi: UNKNOWN for doi in wanted}

    for start in range(0, len(wanted), RETRACTION_BATCH_SIZE):
        batch = wanted[start : start + RETRACTION_BATCH_SIZE]
        url = http.build_url(
            API,
            {
                # Repeated filters of the same name are OR'd, so this asks for
                # every notice updating any DOI in the batch.
                "filter": ",".join(f"updates:{doi}" for doi in batch),
                "rows": RETRACTION_ROWS,
                "mailto": http.contact(),
            },
        )
        try:
            payload = http.get(url, accept="application/json", cache_ttl=cache.TTL_DOCUMENT).json()
        except (http.HTTPError, ValueError):
            continue
        statuses.update(batch_statuses((payload or {}).get("message") or {}, batch))

    return statuses


class CrossrefProvider(Provider):
    name = "crossref"

    def search(self, query: Query) -> ProviderResult:
        result = ProviderResult(provider=self.name)

        phrase = query.phrase()
        url = http.build_url(
            API,
            {
                "query": phrase,
                "rows": query.limit,
                "mailto": http.contact(),  # the polite pool: 3 requests/second
            },
        )
        result.queries.append(phrase)

        try:
            response = http.get(
                url,
                accept="application/json",
                cache_ttl=cache.TTL_SEARCH,
                use_cache=query.use_cache,
            )
        except http.HTTPError as exc:
            result.notes.append(f"Crossref request failed for '{phrase}': {exc}")
            result.failed = True
            return result

        if response.stale:
            result.notes.append(
                f"Served a cached (stale) Crossref response for '{phrase}' — network unavailable."
            )

        try:
            documents, total = parse_search(response.json())
        except ValueError as exc:
            result.notes.append(f"Crossref returned unparseable JSON for '{phrase}': {exc}")
            result.failed = True
            return result

        result.total_available = total
        if total == 0:
            result.notes.append(
                f"Crossref reported total-results=0 for '{phrase}'. The query is valid "
                "but matched nothing — either the terms are too specific or this really "
                "is unexplored ground. Not padded."
            )

        result.documents = documents
        self.apply_recency_filter(result, query.since_years)
        return result
